"""The Metropolitan Museum of Art Open Access API fetcher with jewellery-specific targeting."""

import json
import logging
import urllib.request
import urllib.parse
from typing import List, Optional, Iterator, Set
import time

from ai.dataset_pipeline.schemas import CandidateItem

logger = logging.getLogger("jewelmind.dataset.met")

# Targeted jewellery search terms (replaces overly broad "gold" query)
DEFAULT_JEWELLERY_QUERIES = [
    "finger ring",
    "ring",
    "earrings",
    "gemstone pendant",
    "pendant",
    "necklace",
    "brooch",
    "bracelet",
    "bangle",
    "jewelry",
]

# Relevant museum departments known to house jewellery collections
# 1: American Decorative Arts, 12: European Sculpture & Decorative Arts,
# 13: Greek and Roman Art, 10: Egyptian Art, 14: Islamic Art, 5: Arts of Africa, Oceania, Americas
DEFAULT_TARGET_DEPARTMENTS = [12, 1, 13, 10, 14, 5]

# Keywords that explicitly disqualify an object from being wearable jewellery
EXCLUDED_OBJECT_KEYWORDS = {
    "clock", "horology", "watch", "vase", "vessel", "porcelain", "ceramics",
    "painting", "screen", "sculpture", "statue", "effigy", "figurine",
    "textile", "costume", "print", "drawing", "arms", "armor", "sword", "dagger",
    "musical", "furniture", "reliquary", "altar", "chalice", "cup", "bowl", "plate",
    "snuffbox", "box", "carpet", "tapestry", "manuscript",
}

# Positive jewellery indicator keywords
POSITIVE_JEWELLERY_KEYWORDS = {
    "ring", "finger ring", "earring", "earrings", "pendant", "necklace",
    "brooch", "bracelet", "bangle", "locket", "tiara", "diadem", "cufflink",
    "jewelry", "jewellery", "bezel", "collar", "choker", "armlet", "torc",
}


def assess_jewellery_relevance(title: str, classification: str, medium: str) -> tuple[str, str, str]:
    """Assess whether an object is genuine jewellery, uncertain, or definitely not jewellery.
    
    Returns:
        (category, jewellery_relevance, category_confidence)
    """
    combined_text = f"{title} {classification} {medium}".lower()

    # 1. Check for negative exclusion keywords first
    for ex_word in EXCLUDED_OBJECT_KEYWORDS:
        # Require word boundary / distinct match
        if ex_word in classification.lower() or ex_word in title.lower():
            # Special case: "watch" might be a pendant watch, but usually horology
            return "other", "NOT_JEWELLERY", "LOW"

    # 2. Canonical category identification (ring, earring, pendant, necklace, bracelet, bangle, brooch, other)
    title_lower = title.lower()
    class_lower = classification.lower()

    if any(w in title_lower or w in class_lower for w in ("earring", "earrings", "earstud", "ear pendant")):
        return "earring", "JEWELLERY_RELEVANT", "HIGH"
    elif any(w in title_lower or w in class_lower for w in ("necklace", "choker", "collar")):
        return "necklace", "JEWELLERY_RELEVANT", "HIGH"
    elif any(w in title_lower or w in class_lower for w in ("pendant", "locket", "medallion")):
        return "pendant", "JEWELLERY_RELEVANT", "HIGH"
    elif "bangle" in title_lower or "bangle" in class_lower:
        return "bangle", "JEWELLERY_RELEVANT", "HIGH"
    elif any(w in title_lower or w in class_lower for w in ("bracelet", "armlet", "cuff")):
        return "bracelet", "JEWELLERY_RELEVANT", "HIGH"
    elif any(w in title_lower or w in class_lower for w in ("brooch", "fibula", "pin")):
        return "brooch", "JEWELLERY_RELEVANT", "HIGH"
    elif "finger ring" in title_lower or "finger ring" in class_lower or ("ring" in title_lower and "earring" not in title_lower):
        return "ring", "JEWELLERY_RELEVANT", "HIGH"

    # 3. Check for general jewellery classification
    if any(w in combined_text for w in POSITIVE_JEWELLERY_KEYWORDS):
        return "other", "JEWELLERY_RELEVANT", "MEDIUM"

    return "other", "JEWELLERY_UNCERTAIN", "LOW"


class MetSourceFetcher:
    """Queries The Met collection API with targeted jewellery queries and department filtering."""

    BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"

    def __init__(self, user_agent: str = "JewelMind/1.0 (Research Dataset Pilot)"):
        self.headers = {"User-Agent": user_agent}
        self.is_blocked = False

    def _get_json(self, url: str, retry: bool = True) -> Optional[dict]:
        if self.is_blocked:
            return None
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code in (403, 429):
                logger.warning("Met API rate limited (%s) on %s; activating circuit breaker.", err.code, url)
                self.is_blocked = True
                return None
            logger.warning("Met API HTTP error %s for %s", err.code, url)
            return None
        except Exception as err:
            logger.warning("Met API request failed for %s: %s", url, err)
            return None

    def search_object_ids(self, query: str, department_id: Optional[int] = None) -> List[int]:
        """Search for object IDs matching query with images, optionally scoped to department."""
        encoded = urllib.parse.quote(query)
        if department_id is not None:
            url = f"{self.BASE_URL}/search?departmentId={department_id}&q={encoded}&hasImages=true"
        else:
            url = f"{self.BASE_URL}/search?q={encoded}&hasImages=true"

        data = self._get_json(url)
        if data and "objectIDs" in data and data["objectIDs"]:
            return data["objectIDs"]
        return []

    def fetch_object(self, object_id: int, search_query: str = "") -> Optional[CandidateItem]:
        """Fetch detailed metadata for an object and return CandidateItem if valid."""
        url = f"{self.BASE_URL}/objects/{object_id}"
        obj = self._get_json(url)
        if not obj:
            return None

        # Must have a valid primary image URL (prefer primaryImageSmall for fast web download, fallback to primaryImage)
        primary_image = obj.get("primaryImageSmall") or obj.get("primaryImage")
        if not primary_image:
            return None

        title = obj.get("title") or "Untitled Object"
        medium = obj.get("medium") or ""
        classification = obj.get("classification") or ""
        department = obj.get("department") or ""

        # Relevance assessment
        category, relevance, confidence = assess_jewellery_relevance(title, classification, medium)

        # Verify license status
        is_pd = bool(obj.get("isPublicDomain", False))
        license_status = "VERIFIED_CC0" if is_pd else "LICENSE_REVIEW_REQUIRED"
        license_str = "CC0 1.0 Universal (Public Domain)" if is_pd else "Met Open Access (Unverified PD)"

        return CandidateItem(
            source="met",
            source_id=str(object_id),
            title=title,
            category=category,
            image_url=primary_image,
            medium=medium,
            classification=classification,
            department=department,
            search_query=search_query,
            license_str=license_str,
            is_public_domain=is_pd,
            license_status=license_status,
            jewellery_relevance=relevance,
            category_confidence=confidence,
            raw_metadata={
                "culture": obj.get("culture"),
                "period": obj.get("period"),
                "objectDate": obj.get("objectDate"),
            },
        )

    def fetch_candidates(
        self,
        queries: Optional[List[str]] = None,
        departments: Optional[List[int]] = None,
        max_candidates: int = 15,
        filter_non_jewellery: bool = True,
        exclude_ids: Optional[Set[str]] = None,
    ) -> Iterator[CandidateItem]:
        """Yield candidate items up to max_candidates across specific search queries."""
        search_terms = queries or DEFAULT_JEWELLERY_QUERIES
        dept_ids = departments if departments is not None else DEFAULT_TARGET_DEPARTMENTS
        seen_ids: Set[int] = set()
        if exclude_ids:
            seen_ids.update(int(x) for x in exclude_ids if x.isdigit())
        yielded = 0
        inspected = 0
        max_inspections = max_candidates * 4

        for term in search_terms:
            if yielded >= max_candidates or inspected >= max_inspections:
                break
            for dept in dept_ids:
                if yielded >= max_candidates or inspected >= max_inspections:
                    break
                ids = self.search_object_ids(term, department_id=dept)
                for oid in ids:
                    if oid in seen_ids:
                        continue
                    seen_ids.add(oid)
                    inspected += 1
                    candidate = self.fetch_object(oid, search_query=term)
                    if candidate:
                        # Pre-filter non-jewellery objects before yield if requested
                        if filter_non_jewellery and candidate.jewellery_relevance == "NOT_JEWELLERY":
                            continue

                        yield candidate
                        yielded += 1
                        if yielded >= max_candidates:
                            break
                    if inspected >= max_inspections:
                        break
                    time.sleep(0.1)
