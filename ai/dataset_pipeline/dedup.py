"""Perceptual and cryptographic deduplication utilities with SHA-256 exact matching.

Provides:
  - SHA-256 cryptographic byte-level hashing for certified exact duplicate detection.
  - 64-bit difference hash (dHash) and average hash (aHash) for perceptual similarity.
  - Three-tier classification:
      * EXACT_DUPLICATE: Confirmed identical SHA-256 byte digest (safe for automated rejection).
      * NEAR_DUPLICATE_REVIEW_REQUIRED: dHash/aHash distance <= review_threshold (preserved on disk, NEVER auto-rejected).
      * DISTINCT: Clean separation above review threshold.
"""

import hashlib
from typing import List, Tuple, Dict, Optional
import numpy as np
from PIL import Image


def compute_sha256(img_bytes: bytes) -> str:
    """Compute SHA-256 cryptographic digest of raw image bytes."""
    return hashlib.sha256(img_bytes).hexdigest()


def compute_dhash(img: Image.Image, hash_size: int = 8) -> str:
    """Compute difference hash (dHash) capturing relative horizontal gradients."""
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(resized, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    bit_str = "".join("1" if b else "0" for b in diff.flatten())
    hex_len = hash_size * hash_size // 4
    return format(int(bit_str, 2), f"0{hex_len}x")


def compute_ahash(img: Image.Image, hash_size: int = 8) -> str:
    """Compute average hash (aHash) capturing overall low-frequency intensity layout."""
    resized = img.convert("L").resize((hash_size, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(resized, dtype=np.float32)
    avg = float(pixels.mean())
    diff = pixels > avg
    bit_str = "".join("1" if b else "0" for b in diff.flatten())
    hex_len = hash_size * hash_size // 4
    return format(int(bit_str, 2), f"0{hex_len}x")


def hamming_distance(h1: str, h2: str) -> int:
    """Compute bitwise Hamming distance between two hex-encoded hashes."""
    if not h1 or not h2:
        return 999
    try:
        val1 = int(h1, 16)
        val2 = int(h2, 16)
        return bin(val1 ^ val2).count("1")
    except ValueError:
        return 999


class PerceptualDeduplicator:
    """Catalog of cryptographic and perceptual hashes with certified duplicate classification."""

    def __init__(self, review_threshold: int = 6):
        """
        Args:
            review_threshold: Distance <= this threshold indicates visual similarity requiring human review.
                              Near-duplicates are ALWAYS preserved on disk for manual operator inspection.
        """
        self.review_threshold = review_threshold

        # Maps sha256 -> item_id
        self.sha256_catalog: Dict[str, str] = {}

        # Maps item_id -> (dhash, ahash, sha256, metadata)
        self.catalog: Dict[str, Tuple[str, str, str, Dict]] = {}

        # Log of duplicate comparisons
        self.duplicate_log: List[Dict] = []

    def classify_and_add(
        self,
        item_id: str,
        img: Image.Image,
        img_bytes: Optional[bytes] = None,
        metadata: Optional[Dict] = None,
    ) -> Tuple[str, Optional[str], int, str, str, str]:
        """Classify candidate image against existing catalog and register it.
        
        Returns:
            (duplicate_status, matched_id, min_distance, dhash, ahash, sha256)
            where duplicate_status is one of:
              - 'EXACT_DUPLICATE' (certified via identical SHA-256)
              - 'NEAR_DUPLICATE_REVIEW_REQUIRED' (dHash/aHash distance <= review_threshold; NOT auto-rejected)
              - 'DISTINCT' (distance > review_threshold)
        """
        metadata = metadata or {}
        dhash = compute_dhash(img)
        ahash = compute_ahash(img)

        # Compute SHA-256 from raw bytes if provided, else from converted PNG bytes
        if img_bytes is not None:
            sha256 = compute_sha256(img_bytes)
        else:
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            sha256 = compute_sha256(buf.getvalue())

        # 1. Check for certified EXACT_DUPLICATE via cryptographic SHA-256
        if sha256 in self.sha256_catalog:
            matched_id = self.sha256_catalog[sha256]
            self.duplicate_log.append({
                "candidate_id": item_id,
                "matched_id": matched_id,
                "hamming_distance": 0,
                "status": "EXACT_DUPLICATE",
                "sha256": sha256,
            })
            return "EXACT_DUPLICATE", matched_id, 0, dhash, ahash, sha256

        # 2. Check for perceptual similarity (dHash / aHash)
        closest_id = None
        min_dist = 999

        for existing_id, (ex_dhash, ex_ahash, _, _) in self.catalog.items():
            dist_d = hamming_distance(dhash, ex_dhash)
            dist_a = hamming_distance(ahash, ex_ahash)
            effective_dist = min(dist_d, dist_a)

            if effective_dist < min_dist:
                min_dist = effective_dist
                closest_id = existing_id

        # Near-duplicate review threshold check: NEVER auto-rejected
        if min_dist <= self.review_threshold:
            duplicate_status = "NEAR_DUPLICATE_REVIEW_REQUIRED"
        else:
            duplicate_status = "DISTINCT"

        if duplicate_status == "NEAR_DUPLICATE_REVIEW_REQUIRED" and closest_id:
            self.duplicate_log.append({
                "candidate_id": item_id,
                "matched_id": closest_id,
                "hamming_distance": min_dist,
                "status": duplicate_status,
                "review_threshold": self.review_threshold,
                "sha256": sha256,
            })

        # Register in catalogs
        self.sha256_catalog[sha256] = item_id
        self.catalog[item_id] = (dhash, ahash, sha256, metadata)

        return duplicate_status, closest_id, min_dist, dhash, ahash, sha256
