"""Cleveland Museum of Art (CMA) Open Access API fetcher with jewellery relevance metadata."""

import json
import logging
import urllib.request
import urllib.parse
from typing import List, Optional, Iterator, Set
import time

from ai.dataset_pipeline.schemas import CandidateItem

logger = logging.getLogger("jewelmind.dataset.cma")


class CmaSourceFetcher:
    """Queries Cleveland Museum of Art API for CC0 open-access jewellery records."""

    BASE_URL = "https://openaccess-api.clevelandart.org/api/artworks"

    def __init__(self, user_agent: str = "JewelMind/1.0 (Research Dataset Pilot)"):
        self.headers = {"User-Agent": user_agent}

    def _get_json(self, url: str) -> Optional[dict]:
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as err:
            logger.warning("CMA API request failed for %s: %s", url, err)
            return None

    def fetch_candidates(
        self,
        query: str = "jewelry",
        limit: int = 15,
        exclude_ids: Optional[Set[str]] = None,
    ) -> Iterator[CandidateItem]:
        """Fetch candidate items up to limit from CMA open access."""
        encoded = urllib.parse.quote(query)
        url = f"{self.BASE_URL}/?q={encoded}&has_image=1&limit={limit * 2}"
        payload = self._get_json(url)
        if not payload or "data" not in payload:
            return

        seen_ids = set(exclude_ids or [])
        yielded = 0
        for item in payload["data"]:
            if yielded >= limit:
                break

            cma_id = str(item.get("id"))
            if cma_id in seen_ids:
                continue

            images = item.get("images") or {}
            web_img = images.get("web") or {}
            img_url = web_img.get("url")
            if not img_url:
                continue

            title = item.get("title") or "Untitled Artwork"
            title_lower = title.lower()
            obj_type = (item.get("type") or "").lower()
            technique = item.get("technique") or ""
            department = item.get("department") or ""

            category = "other"
            category_confidence = "LOW"
            jewellery_relevance = "JEWELLERY_UNCERTAIN"

            # Canonical categories: ring, earring, pendant, necklace, bracelet, bangle, brooch, other
            if any(w in title_lower or w in obj_type for w in ("earring", "earrings", "earstud", "ear pendant")):
                category = "earring"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif any(w in title_lower or w in obj_type for w in ("necklace", "choker", "collar")):
                category = "necklace"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif any(w in title_lower or w in obj_type for w in ("pendant", "locket", "medallion")):
                category = "pendant"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif "bangle" in title_lower or "bangle" in obj_type:
                category = "bangle"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif any(w in title_lower or w in obj_type for w in ("bracelet", "armlet", "cuff")):
                category = "bracelet"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif any(w in title_lower or w in obj_type for w in ("brooch", "fibula", "pin")):
                category = "brooch"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif "finger ring" in title_lower or "finger ring" in obj_type or ("ring" in title_lower and "earring" not in title_lower):
                category = "ring"
                category_confidence = "HIGH"
                jewellery_relevance = "JEWELLERY_RELEVANT"
            elif "jewelry" in obj_type or "jewelry" in title_lower:
                category = "other"
                category_confidence = "MEDIUM"
                jewellery_relevance = "JEWELLERY_RELEVANT"

            license_tag = item.get("share_license_status")
            is_cc0 = license_tag == "CC0"
            license_status = "VERIFIED_CC0" if is_cc0 else "LICENSE_REVIEW_REQUIRED"
            license_str = "CC0 1.0 Universal" if is_cc0 else f"CMA License: {license_tag}"

            yield CandidateItem(
                source="cma",
                source_id=str(item.get("id")),
                title=title,
                category=category,
                image_url=img_url,
                medium=technique,
                classification=item.get("type") or "",
                department=department,
                search_query=query,
                license_str=license_str,
                is_public_domain=is_cc0,
                license_status=license_status,
                jewellery_relevance=jewellery_relevance,
                category_confidence=category_confidence,
                raw_metadata={
                    "culture": item.get("culture"),
                    "creation_date": item.get("creation_date"),
                },
            )
            yielded += 1
            time.sleep(0.08)
