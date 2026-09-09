"""JewelMind Other Jewellery (Class 7) CC0 / Public Domain Harvester.

Strict Annotation Policy for other_jewellery (Class 7):
INCLUDED:
- Tiaras, diadems, crowns, aigrettes (jewellery headpieces)
- Hairpins, ornamental hair combs, topknot pins
- Cameos, intaglios (precious engraved gems)
- Precious cufflinks
- Anklets

EXCLUDED:
- Watches and clocks (strictly prohibited)
- Vessels, chalices, bowls, tableware, dishes, snuff boxes, spoons
- Armor, swords, shields, helmets
- Sculptures, large statues, figurines
- Coins, medals, currency (tetradrachms, denarii, sovereigns)
- Clothing, textiles, shoes, paintings, drawings, prints, masks, wigs
- Birds, animals (e.g. egrets / aigrette birds), portraits of persons
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import requests

from scripts.prepare_met_dataset import (
    segment_museum_object,
    mask_to_yolo_polygons,
    get_deterministic_split,
)

OUTPUT_DATASET_DIR = Path("ai/vision/datasets/jewellery_v2")
RAW_SAVE_DIR = Path("ai/vision/datasets/raw/met_jewellery/other_jewellery")
PREVIEWS_DIR = Path("ai/vision/datasets/previews/new_categories")

HEADERS = {
    "User-Agent": "JewelMind-Research-Dataset-Builder/2.0 (https://jewelmind.org; contact@jewelmind.org)"
}

EXCLUDED_WORDS = [
    "watch", "clock", "painting", "drawing", "print", "textile", "furniture",
    "vessel", "pottery", "vase", "bottle", "cup", "chalice", "bowl", "statue",
    "sculpture", "armor", "sword", "dagger", "shield", "helmet", "coin", "medal",
    "church", "building", "monument", "landscape", "portrait", "illustration",
    "engraving", "woodcut", "lithograph", "etched", "etching", "manuscript", "page",
    "carpet", "tapestry", "chair", "table", "altarpiece", "deva", "buddha", "cross",
    "tetradrachm", "didrachm", "denarius", "sovereign", "mask", "wig", "dish", "plate",
    "box", "snuff", "spoon", "ceremonial beadwork", "casket", "tray", "basket",
    "bird", "egret", "garzetta", "fauna", "animal", "actress", "actor", "dress",
    "outfit", "photoplay", "model", "celebrity", "dancer"
]

CMA_ALLOWED_TYPES = [
    "Jewelry", "Glyptic", "Metalwork", "Ivory", "Lapidary Work-Gems", "Enamel", "Glass"
]


def clean_str(s: str) -> str:
    return str(s).encode("ascii", "replace").decode("ascii")


def is_valid_title(title: str) -> bool:
    t = title.lower()
    for w in EXCLUDED_WORDS:
        if w in t:
            return False
    return True


def harvest_other_jewellery(target_count: int = 180):
    RAW_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check already present in dataset
    existing_images = list((OUTPUT_DATASET_DIR / "train" / "images").glob("other_*.jpg")) + \
                      list((OUTPUT_DATASET_DIR / "val" / "images").glob("other_*.jpg")) + \
                      list((OUTPUT_DATASET_DIR / "test" / "images").glob("other_*.jpg")) + \
                      list((OUTPUT_DATASET_DIR / "train" / "images").glob("met_other_*.jpg")) + \
                      list((OUTPUT_DATASET_DIR / "val" / "images").glob("met_other_*.jpg")) + \
                      list((OUTPUT_DATASET_DIR / "test" / "images").glob("met_other_*.jpg"))
                      
    print(f"[*] Starting other_jewellery harvest. Already have {len(existing_images)} images in dataset.")
    
    seen_hashes = set()
    for split in ["train", "val", "test"]:
        for p in (OUTPUT_DATASET_DIR / split / "images").glob("*.*"):
            with open(p, "rb") as f:
                seen_hashes.add(hashlib.sha256(f.read()).hexdigest())
                
    collected = len(existing_images)
    contact_samples = []
    
    # 1. Cleveland Museum of Art (CC0)
    cleveland_terms = ["cameo", "tiara", "hairpin", "diadem", "cufflink", "anklet", "aigrette"]
    for term in cleveland_terms:
        if collected >= target_count:
            break
        print(f"\n[*] Querying Cleveland Museum of Art for '{term}'...")
        try:
            url = f"https://openaccess-api.clevelandart.org/api/artworks/?q={term}&has_image=1&cc0=1&limit=50"
            r = requests.get(url, headers=HEADERS, timeout=10).json()
            data = r.get("data", [])
            print(f"    - Found {len(data)} items")
            for item in data:
                if collected >= target_count:
                    break
                item_type = item.get("type") or ""
                if item_type not in CMA_ALLOWED_TYPES:
                    continue
                title = item.get("title") or ""
                if not is_valid_title(title):
                    continue
                img_url = item.get("images", {}).get("web", {}).get("url")
                if not img_url:
                    continue
                    
                cid = item.get("id") or item.get("accession_number", "item")
                stem = f"other_cma_{cid}"
                
                try:
                    img_res = requests.get(img_url, headers=HEADERS, timeout=12)
                    if img_res.status_code != 200 or len(img_res.content) < 3000:
                        continue
                except Exception:
                    continue
                    
                sha = hashlib.sha256(img_res.content).hexdigest()
                if sha in seen_hashes:
                    continue
                    
                img_bgr = cv2.imdecode(np.frombuffer(img_res.content, np.uint8), cv2.IMREAD_COLOR)
                if img_bgr is None:
                    continue
                    
                h, w = img_bgr.shape[:2]
                if h < 100 or w < 100:
                    continue
                    
                mask = segment_museum_object(img_bgr)
                mask_px = np.count_nonzero(mask)
                if mask_px / (h * w) < 0.005 or mask_px / (h * w) > 0.90:
                    continue
                    
                polys = mask_to_yolo_polygons(mask, class_id=7)
                if not polys:
                    continue
                    
                seen_hashes.add(sha)
                split = get_deterministic_split(stem)
                
                # Save raw & dataset
                cv2.imwrite(str(RAW_SAVE_DIR / f"{stem}.jpg"), img_bgr)
                cv2.imwrite(str(RAW_SAVE_DIR / f"{stem}_mask.png"), mask)
                
                dest_img = OUTPUT_DATASET_DIR / split / "images" / f"{stem}.jpg"
                dest_lbl = OUTPUT_DATASET_DIR / split / "labels" / f"{stem}.txt"
                dest_img.parent.mkdir(parents=True, exist_ok=True)
                dest_lbl.parent.mkdir(parents=True, exist_ok=True)
                
                cv2.imwrite(str(dest_img), img_bgr)
                with open(dest_lbl, "w", encoding="utf-8") as f:
                    f.write("\n".join(polys) + "\n")
                    
                collected += 1
                print(f"      [+] ({collected}/{target_count}) Added CMA [{item_type}]: {clean_str(title)[:35]} ({len(polys)} polys)")
                
                if len(contact_samples) < 16:
                    overlay = img_bgr.copy()
                    overlay[mask > 0] = cv2.addWeighted(img_bgr[mask > 0], 0.5, np.full_like(img_bgr[mask > 0], (0, 220, 255)), 0.5, 0)
                    thumb = cv2.resize(overlay, (200, 200))
                    cv2.putText(thumb, f"other #{cid}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)
                    contact_samples.append(thumb)
        except Exception as e:
            print(f"    [WARN] Cleveland search failed for '{term}': {e}")
            
    # 2. Wikimedia Commons (Curated CC0 / Public Domain Categories)
    wiki_cats = [
        ("Category:Cameos", 50),
        ("Category:Tiaras", 50),
        ("Category:Diadems", 50),
        ("Category:Cufflinks", 50),
        ("Category:Ancient Greek jewellery in the British Museum", 50),
        ("Category:Ancient Roman jewellery in the British Museum", 50),
        ("Category:Etruscan jewellery in the British Museum", 50),
        ("Category:Byzantine jewellery in the British Museum", 50),
    ]
    
    for cat, limit in wiki_cats:
        if collected >= target_count:
            break
        print(f"\n[*] Querying Wikimedia Commons for '{cat}'...")
        try:
            url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=categorymembers&gcmtitle={cat}&gcmtype=file&gcmlimit={limit}&prop=imageinfo&iiprop=url|mime|size&format=json"
            r = requests.get(url, headers=HEADERS, timeout=12).json()
            pages = r.get("query", {}).get("pages", {})
            print(f"    - Found {len(pages)} files")
            for pid, pdata in pages.items():
                if collected >= target_count:
                    break
                title = pdata.get("title", "")
                if not is_valid_title(title):
                    continue
                ii = pdata.get("imageinfo", [{}])[0]
                img_url = ii.get("url")
                mime = ii.get("mime", "")
                if not img_url or not mime.startswith("image/"):
                    continue
                    
                clean_pid = "".join([c if c.isalnum() else "_" for c in str(pid)])
                stem = f"other_wiki_{clean_pid}"
                
                try:
                    img_res = requests.get(img_url, headers=HEADERS, timeout=15)
                    if img_res.status_code != 200 or len(img_res.content) < 3000:
                        continue
                except Exception:
                    continue
                    
                sha = hashlib.sha256(img_res.content).hexdigest()
                if sha in seen_hashes:
                    continue
                    
                img_bgr = cv2.imdecode(np.frombuffer(img_res.content, np.uint8), cv2.IMREAD_COLOR)
                if img_bgr is None:
                    continue
                    
                h, w = img_bgr.shape[:2]
                if h < 100 or w < 100:
                    continue
                    
                if max(h, w) > 1600:
                    scale = 1600 / max(h, w)
                    img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))
                    h, w = img_bgr.shape[:2]
                    
                mask = segment_museum_object(img_bgr)
                mask_px = np.count_nonzero(mask)
                if mask_px / (h * w) < 0.005 or mask_px / (h * w) > 0.90:
                    continue
                    
                polys = mask_to_yolo_polygons(mask, class_id=7)
                if not polys:
                    continue
                    
                seen_hashes.add(sha)
                split = get_deterministic_split(stem)
                
                cv2.imwrite(str(RAW_SAVE_DIR / f"{stem}.jpg"), img_bgr)
                cv2.imwrite(str(RAW_SAVE_DIR / f"{stem}_mask.png"), mask)
                
                dest_img = OUTPUT_DATASET_DIR / split / "images" / f"{stem}.jpg"
                dest_lbl = OUTPUT_DATASET_DIR / split / "labels" / f"{stem}.txt"
                dest_img.parent.mkdir(parents=True, exist_ok=True)
                dest_lbl.parent.mkdir(parents=True, exist_ok=True)
                
                cv2.imwrite(str(dest_img), img_bgr)
                with open(dest_lbl, "w", encoding="utf-8") as f:
                    f.write("\n".join(polys) + "\n")
                    
                collected += 1
                print(f"      [+] ({collected}/{target_count}) Added Wiki: {clean_str(title)[:35]} ({len(polys)} polys)")
                
                if len(contact_samples) < 16:
                    overlay = img_bgr.copy()
                    overlay[mask > 0] = cv2.addWeighted(img_bgr[mask > 0], 0.5, np.full_like(img_bgr[mask > 0], (0, 220, 255)), 0.5, 0)
                    thumb = cv2.resize(overlay, (200, 200))
                    cv2.putText(thumb, f"other #{clean_pid}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)
                    contact_samples.append(thumb)
        except Exception as e:
            print(f"    [WARN] Wikimedia search failed for '{cat}': {e}")
            
    # 3. Openverse (CC0 / Public Domain Mark)
    openverse_terms = ["cameo jewellery", "tiara jewellery", "diadem jewellery", "hairpin jewellery", "cufflinks jewellery", "cameo gem", "anklet jewellery"]
    for term in openverse_terms:
        if collected >= target_count:
            break
        print(f"\n[*] Querying Openverse CC0 for '{term}'...")
        try:
            url = f"https://api.openverse.org/v1/images/?q={term}&license=cc0,pdm&page_size=50"
            r = requests.get(url, headers=HEADERS, timeout=12).json()
            results = r.get("results", [])
            print(f"    - Found {len(results)} items")
            for item in results:
                if collected >= target_count:
                    break
                title = item.get("title") or ""
                if not is_valid_title(title):
                    continue
                img_url = item.get("url")
                if not img_url:
                    continue
                oid = item.get("id", "ov")[:8]
                stem = f"other_ov_{oid}"
                
                try:
                    img_res = requests.get(img_url, headers=HEADERS, timeout=12)
                    if img_res.status_code != 200 or len(img_res.content) < 3000:
                        continue
                except Exception:
                    continue
                    
                sha = hashlib.sha256(img_res.content).hexdigest()
                if sha in seen_hashes:
                    continue
                    
                img_bgr = cv2.imdecode(np.frombuffer(img_res.content, np.uint8), cv2.IMREAD_COLOR)
                if img_bgr is None:
                    continue
                    
                h, w = img_bgr.shape[:2]
                if h < 100 or w < 100:
                    continue
                if max(h, w) > 1600:
                    scale = 1600 / max(h, w)
                    img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))
                    h, w = img_bgr.shape[:2]
                    
                mask = segment_museum_object(img_bgr)
                mask_px = np.count_nonzero(mask)
                if mask_px / (h * w) < 0.005 or mask_px / (h * w) > 0.90:
                    continue
                    
                polys = mask_to_yolo_polygons(mask, class_id=7)
                if not polys:
                    continue
                    
                seen_hashes.add(sha)
                split = get_deterministic_split(stem)
                
                cv2.imwrite(str(RAW_SAVE_DIR / f"{stem}.jpg"), img_bgr)
                cv2.imwrite(str(RAW_SAVE_DIR / f"{stem}_mask.png"), mask)
                
                dest_img = OUTPUT_DATASET_DIR / split / "images" / f"{stem}.jpg"
                dest_lbl = OUTPUT_DATASET_DIR / split / "labels" / f"{stem}.txt"
                dest_img.parent.mkdir(parents=True, exist_ok=True)
                dest_lbl.parent.mkdir(parents=True, exist_ok=True)
                
                cv2.imwrite(str(dest_img), img_bgr)
                with open(dest_lbl, "w", encoding="utf-8") as f:
                    f.write("\n".join(polys) + "\n")
                    
                collected += 1
                print(f"      [+] ({collected}/{target_count}) Added Openverse: {clean_str(title)[:35]} ({len(polys)} polys)")
                
                if len(contact_samples) < 16:
                    overlay = img_bgr.copy()
                    overlay[mask > 0] = cv2.addWeighted(img_bgr[mask > 0], 0.5, np.full_like(img_bgr[mask > 0], (0, 220, 255)), 0.5, 0)
                    thumb = cv2.resize(overlay, (200, 200))
                    cv2.putText(thumb, f"other #{oid}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)
                    contact_samples.append(thumb)
        except Exception as e:
            print(f"    [WARN] Openverse search failed for '{term}': {e}")
            
    print(f"\n[OK] other_jewellery harvest complete: {collected} images collected.")
    
    # Save contact sheet
    if contact_samples:
        n = len(contact_samples)
        cols = 4
        rows = (n + cols - 1) // cols
        grid_img = np.full((rows * 200, cols * 200, 3), 30, dtype=np.uint8)
        for i, thumb in enumerate(contact_samples):
            r = i // cols
            c = i % cols
            grid_img[r*200:(r+1)*200, c*200:(c+1)*200] = thumb
        sheet_path = PREVIEWS_DIR / "contact_sheet_other_jewellery.jpg"
        cv2.imwrite(str(sheet_path), grid_img)
        print(f"[*] Saved updated contact sheet: {sheet_path}")


if __name__ == "__main__":
    harvest_other_jewellery(target_count=180)
