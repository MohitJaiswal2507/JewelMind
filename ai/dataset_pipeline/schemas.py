"""Data models and schemas for the JewelMind dataset acquisition pipeline."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Tuple, Dict, Any


@dataclass
class CandidateItem:
    """Represents a discovered candidate from an open-access source."""
    source: str                          # "met", "cma", "smithsonian"
    source_id: str                       # Native ID in source database
    title: str                           # Artwork/object title
    category: str                        # "ring", "pendant", "earring", "bracelet", "other"
    image_url: str                       # Direct image URL
    medium: Optional[str] = None         # Materials / techniques string
    classification: str = ""             # Source classification (e.g., "Gold-Jewelry", "Horology")
    department: str = ""                 # Museum department (e.g., "European Sculpture and Decorative Arts")
    search_query: str = ""               # Search keyword used to discover item
    license_str: str = "Unknown"         # e.g. "CC0 1.0 Universal", "Public Domain"
    is_public_domain: bool = False       # Explicit public domain flag from source
    license_status: str = "LICENSE_REVIEW_REQUIRED" # "VERIFIED_CC0" or "LICENSE_REVIEW_REQUIRED"
    jewellery_relevance: str = "JEWELLERY_RELEVANT" # "JEWELLERY_RELEVANT", "JEWELLERY_UNCERTAIN", "NOT_JEWELLERY"
    category_confidence: str = "HIGH"    # "HIGH", "MEDIUM", "LOW"
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilterResult:
    """Result of quality and integrity validation."""
    passed: bool
    rejection_reason: Optional[str] = None
    original_dimensions: Optional[Tuple[int, int]] = None
    foreground_ratio: Optional[float] = None
    background_brightness: Optional[float] = None
    jewellery_relevance: str = "JEWELLERY_RELEVANT"


@dataclass
class ManifestEntry:
    """Entry in the machine-readable dataset manifest."""
    local_path: str
    source: str
    source_id: str
    source_url: str
    image_url: str
    title: str
    category: str
    medium: Optional[str]
    classification: str
    department: str
    search_query: str
    license: str
    license_status: str
    jewellery_relevance: str             # "JEWELLERY_RELEVANT", "JEWELLERY_UNCERTAIN", "NOT_JEWELLERY"
    category_confidence: str             # "HIGH", "MEDIUM", "LOW"
    original_dimensions: Tuple[int, int]
    status: str                          # "ACCEPTED", "REJECTED", "REVIEW_REQUIRED"
    rejection_reason: Optional[str] = None
    sha256: Optional[str] = None
    dhash: Optional[str] = None
    ahash: Optional[str] = None
    duplicate_status: str = "DISTINCT"   # "DISTINCT", "EXACT_DUPLICATE", "NEAR_DUPLICATE_REVIEW_REQUIRED"
    duplicate_distance: Optional[int] = None
    duplicate_of: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
