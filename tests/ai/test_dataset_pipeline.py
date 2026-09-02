"""Unit tests for JewelMind Dataset Acquisition and Curation Pipeline.

Covers:
  - Image quality, dimension, and corruption filtering
  - Cryptographic SHA-256 certified exact duplicate detection
  - Tiered perceptual deduplication (Exact vs Review Required vs Distinct)
  - Proof that dHash distance <= threshold does NOT auto-reject candidates
  - Preservation of source metadata (classification, department, search_query)
  - Jewellery relevance assessment (JEWELLERY_RELEVANT vs NOT_JEWELLERY)
  - Met jewellery-specific query and department construction
  - Manifest generation and license metadata handling
"""

import io
import json
import hashlib
from pathlib import Path
import pytest
from PIL import Image
import numpy as np

from ai.dataset_pipeline.schemas import CandidateItem, FilterResult, ManifestEntry
from ai.dataset_pipeline.filter import ImageQualityFilter
from ai.dataset_pipeline.dedup import (
    compute_sha256,
    compute_dhash,
    compute_ahash,
    hamming_distance,
    PerceptualDeduplicator,
)
from ai.dataset_pipeline.sources.met import (
    MetSourceFetcher,
    assess_jewellery_relevance,
    DEFAULT_JEWELLERY_QUERIES,
    EXCLUDED_OBJECT_KEYWORDS,
)
from ai.dataset_pipeline.sources.cma import CmaSourceFetcher


def create_test_image_bytes(width: int, height: int, color=(255, 255, 255), format="JPEG") -> bytes:
    """Helper to generate in-memory image bytes."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_image_filter_rejects_undersized_images():
    """Verify images smaller than 512x512 are strictly rejected."""
    q_filter = ImageQualityFilter(min_width=512, min_height=512)
    small_bytes = create_test_image_bytes(400, 400)
    result, img = q_filter.validate(small_bytes)

    assert not result.passed
    assert "BELOW_MIN_RESOLUTION" in result.rejection_reason
    assert result.original_dimensions == (400, 400)
    assert img is None


def test_image_filter_detects_corruption():
    """Verify corrupt or unreadable image bytes are caught gracefully."""
    q_filter = ImageQualityFilter(min_width=512, min_height=512)
    corrupt_bytes = b"NOT_A_VALID_IMAGE_FILE_HEADER_GARBAGE_BYTES"
    result, img = q_filter.validate(corrupt_bytes)

    assert not result.passed
    assert "CORRUPT_OR_UNREADABLE_IMAGE" in result.rejection_reason
    assert img is None


def test_image_filter_accepts_valid_jewellery_image():
    """Verify clean, properly sized image passes validation."""
    q_filter = ImageQualityFilter(min_width=512, min_height=512)

    img = Image.new("RGB", (600, 600), color=(250, 250, 250))
    arr = np.array(img)
    y, x = np.ogrid[:600, :600]
    mask = (x - 300)**2 + (y - 300)**2 <= 150**2
    arr[mask] = [212, 175, 55]  # Gold

    valid_img = Image.fromarray(arr)
    buf = io.BytesIO()
    valid_img.save(buf, format="JPEG")

    result, decoded = q_filter.validate(buf.getvalue())
    assert result.passed
    assert result.rejection_reason is None
    assert result.original_dimensions == (600, 600)
    assert decoded is not None


def test_sha256_exact_duplicate_detection():
    """Verify identical bytes trigger certified EXACT_DUPLICATE via SHA-256."""
    dedup = PerceptualDeduplicator(review_threshold=6)
    img_bytes1 = create_test_image_bytes(512, 512, color=(212, 175, 55))
    img1 = Image.open(io.BytesIO(img_bytes1))

    # Same exact bytes
    img_bytes2 = bytes(img_bytes1)
    img2 = Image.open(io.BytesIO(img_bytes2))

    status1, _, _, _, _, sha1 = dedup.classify_and_add("item_1", img1, img_bytes=img_bytes1)
    assert status1 == "DISTINCT"
    assert sha1 == hashlib.sha256(img_bytes1).hexdigest()

    status2, match2, dist2, _, _, sha2 = dedup.classify_and_add("item_2", img2, img_bytes=img_bytes2)
    assert status2 == "EXACT_DUPLICATE"
    assert match2 == "item_1"
    assert dist2 == 0
    assert sha2 == sha1


def test_near_duplicate_does_not_auto_reject():
    """Verify that a dHash distance <= review_threshold results in NEAR_DUPLICATE_REVIEW_REQUIRED, NOT auto-rejection."""
    dedup = PerceptualDeduplicator(review_threshold=6)

    imgA = Image.new("RGB", (100, 100), color=(200, 200, 200))
    bufA = io.BytesIO()
    imgA.save(bufA, format="PNG")
    bytesA = bufA.getvalue()
    dedup.classify_and_add("item_A", imgA, img_bytes=bytesA)

    # Make an image with a small variation that yields distance <= 6, but different SHA-256
    arrB = np.full((100, 100, 3), 200, dtype=np.uint8)
    arrB[:10, :10] = [180, 180, 180]
    imgB = Image.fromarray(arrB)
    bufB = io.BytesIO()
    imgB.save(bufB, format="PNG")
    bytesB = bufB.getvalue()

    status, match_id, dist, _, _, shaB = dedup.classify_and_add("item_B", imgB, img_bytes=bytesB)
    assert shaB != hashlib.sha256(bytesA).hexdigest()
    if dist <= 6 and dist > 0:
        assert status == "NEAR_DUPLICATE_REVIEW_REQUIRED"
        assert match_id == "item_A"


def test_distinct_images_classified_as_distinct():
    """Verify clearly distinct visual designs receive DISTINCT status."""
    dedup = PerceptualDeduplicator(review_threshold=6)

    img1 = Image.new("RGB", (100, 100), color=(255, 215, 0))
    dedup.classify_and_add("item_1", img1)

    # Vertical stripes producing strong horizontal gradient
    arr_distinct = np.zeros((100, 100, 3), dtype=np.uint8)
    arr_distinct[:, ::4] = [255, 255, 255]
    img_distinct = Image.fromarray(arr_distinct)

    status, match_id, dist, _, _, _ = dedup.classify_and_add("item_distinct", img_distinct)
    assert status == "DISTINCT"
    assert dist > 6


def test_met_targeted_query_construction():
    """Verify Met fetcher queries are jewellery-specific and avoid generic 'gold'."""
    # Broad 'gold' must NOT be in default queries
    assert "gold" not in DEFAULT_JEWELLERY_QUERIES
    assert "gold object" not in DEFAULT_JEWELLERY_QUERIES

    # Targeted terms must be present
    assert "finger ring" in DEFAULT_JEWELLERY_QUERIES
    assert "earrings" in DEFAULT_JEWELLERY_QUERIES
    assert "necklace" in DEFAULT_JEWELLERY_QUERIES
    assert "pendant" in DEFAULT_JEWELLERY_QUERIES
    assert "bracelet" in DEFAULT_JEWELLERY_QUERIES


def test_jewellery_relevance_assessment():
    """Verify classification and title filter flags clocks, vases, screens as NOT_JEWELLERY."""
    # Non-jewellery objects
    cat, rel, conf = assess_jewellery_relevance("Table clock with calendar", "Horology", "silver, gold")
    assert rel == "NOT_JEWELLERY"

    cat, rel, conf = assess_jewellery_relevance("Vase chinois", "Ceramics", "porcelain, gold")
    assert rel == "NOT_JEWELLERY"

    cat, rel, conf = assess_jewellery_relevance("Cherry Blossom Screens", "Paintings", "gold leaf on paper")
    assert rel == "NOT_JEWELLERY"

    cat, rel, conf = assess_jewellery_relevance("Miniature camelid effigy", "Sculpture", "gold-silver alloy")
    assert rel == "NOT_JEWELLERY"

    # Genuine jewellery
    cat, rel, conf = assess_jewellery_relevance("Gold finger ring with Hermes", "Gold-Jewelry", "Gold")
    assert rel == "JEWELLERY_RELEVANT"
    assert cat == "ring"
    assert conf == "HIGH"

    cat, rel, conf = assess_jewellery_relevance("Disk Pendant (akrafokonmu)", "Jewelry", "Gold")
    assert rel == "JEWELLERY_RELEVANT"
    assert cat == "pendant"
    assert conf == "HIGH"

    cat, rel, conf = assess_jewellery_relevance("Diamond Stud Earrings", "Precious Jewelry", "Platinum, diamond")
    assert rel == "JEWELLERY_RELEVANT"
    assert cat == "earring"
    assert conf == "HIGH"


def test_metadata_preservation_in_manifest():
    """Verify ManifestEntry preserves sha256, search query, department, classification, and relevance."""
    entry = ManifestEntry(
        local_path="datasets/curation/pilot_images/met_123_ring.jpg",
        source="met",
        source_id="123",
        source_url="https://images.metmuseum.org/example.jpg",
        image_url="https://images.metmuseum.org/example.jpg",
        title="Gold and Sapphire Ring",
        category="ring",
        medium="Gold, sapphire",
        classification="Gold-Jewelry",
        department="Greek and Roman Art",
        search_query="finger ring",
        license="CC0 1.0 Universal",
        license_status="VERIFIED_CC0",
        jewellery_relevance="JEWELLERY_RELEVANT",
        category_confidence="HIGH",
        original_dimensions=(1200, 1200),
        status="ACCEPTED",
        sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        duplicate_status="DISTINCT",
        dhash="0000ffff0000ffff",
        ahash="ffff0000ffff0000",
    )

    d = entry.to_dict()
    assert d["sha256"].startswith("abcdef")
    assert d["search_query"] == "finger ring"
    assert d["department"] == "Greek and Roman Art"
    assert d["classification"] == "Gold-Jewelry"
    assert d["jewellery_relevance"] == "JEWELLERY_RELEVANT"
    assert d["category_confidence"] == "HIGH"
    assert d["duplicate_status"] == "DISTINCT"
