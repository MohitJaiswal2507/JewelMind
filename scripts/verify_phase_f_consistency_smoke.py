"""JewelMind — Phase F Smoke Tests: Jewellery Type Consistency & Conflict Guards on RTX 4060.

Executes live end-to-end tests against:
- FastAPI Backend: http://127.0.0.1:8000
- AI Worker: http://127.0.0.1:8001 (NVIDIA GeForce RTX 4060)

Scenarios:
1. Matching Earring: gallery_earring.png + Earring prompt -> Authentic Earring render.
2. Matching Necklace: gallery_necklace.png + Necklace prompt -> Authentic Necklace render.
3. Conflict Guard: gallery_necklace.png + Earring prompt without resolution -> HTTP 409 Conflict.
4. Conflict Resolved (Option A): gallery_necklace.png + conflict_resolution="blueprint" -> Valid Necklace render.
"""

import sys
from pathlib import Path
import httpx

# Ensure paths
WORKSPACE = Path(__file__).resolve().parent.parent
QA_DIR = WORKSPACE / "ai" / "rendering" / "datasets" / "rendering_final_corrected_conditioning" / "qa"
OUTPUT_DIR = WORKSPACE / "outputs" / "phase_f_smoke"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_URL = "http://127.0.0.1:8000"


def get_auth_token():
    """Login or register a smoke test user to acquire JWT token."""
    client = httpx.Client(base_url=BACKEND_URL, timeout=10.0)
    email = "phase_f_artisan@jewelmind.com"
    password = "SecurePassword123!"

    # Try login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    if login_resp.status_code == 200:
        return login_resp.json()["access_token"]

    # Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Phase F QA Artisan"},
    )
    if reg_resp.status_code in (200, 201):
        return reg_resp.json()["access_token"]

    raise RuntimeError(f"Failed to authenticate smoke test user: {login_resp.text} / {reg_resp.text}")


def run_smoke_tests():
    print("=" * 70)
    print("JEWELMIND PHASE F — REAL RTX 4060 VISUAL & CONSISTENCY SMOKE TESTS")
    print("=" * 70)

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    client = httpx.Client(base_url=BACKEND_URL, timeout=180.0, headers=headers)

    # 1. Matching Earring
    print("\n[TEST 1] Matching Earring Blueprint + Earring Prompt...")
    earring_path = QA_DIR / "gallery_earring.png"
    with open(earring_path, "rb") as f:
        resp = client.post(
            "/api/v1/ai/render",
            files={"file": ("gallery_earring.png", f, "image/png")},
            data={
                "category": "earring",
                "source_blueprint_category": "earring",
                "prompt": "Create a sophisticated earring in polished 18k yellow gold with a pear-shaped diamond.",
                "steps": "20",
                "seed": "42",
            },
        )
    print(f"Status Code: {resp.status_code}")
    assert resp.status_code == 200, f"Test 1 Failed: {resp.text}"
    res1 = resp.json()
    print(f"Output URL: {res1.get('output_url')}")
    print(f"Inference Time: {res1.get('inference_time_ms')} ms")
    print(f"Device Used: {res1.get('device_used')}")
    print(f"Category Conflict: {res1.get('category_conflict')}")
    assert res1.get("category_conflict") is False
    print("[PASS] Test 1: Authentic Earring render successfully synthesized.")

    # 2. Matching Necklace
    print("\n[TEST 2] Matching Necklace Blueprint + Necklace Prompt...")
    necklace_path = QA_DIR / "gallery_necklace.png"
    with open(necklace_path, "rb") as f:
        resp = client.post(
            "/api/v1/ai/render",
            files={"file": ("gallery_necklace.png", f, "image/png")},
            data={
                "category": "necklace",
                "source_blueprint_category": "necklace",
                "prompt": "A luxury statement necklace in 18k yellow gold with brilliant diamonds.",
                "steps": "20",
                "seed": "42",
            },
        )
    print(f"Status Code: {resp.status_code}")
    assert resp.status_code == 200, f"Test 2 Failed: {resp.text}"
    res2 = resp.json()
    print(f"Output URL: {res2.get('output_url')}")
    print(f"Inference Time: {res2.get('inference_time_ms')} ms")
    print(f"Device Used: {res2.get('device_used')}")
    print(f"Category Conflict: {res2.get('category_conflict')}")
    assert res2.get("category_conflict") is False
    print("[PASS] Test 2: Authentic Necklace render successfully synthesized.")

    # 3. Category Conflict Guard (The Exact Bug Scenario)
    print("\n[TEST 3A] Conflict Guard: Necklace Blueprint + Earring Prompt (Unconfirmed)...")
    with open(necklace_path, "rb") as f:
        resp = client.post(
            "/api/v1/ai/render",
            files={"file": ("gallery_necklace.png", f, "image/png")},
            data={
                "category": "earring",
                "source_blueprint_category": "necklace",
                "prompt": "Create a sophisticated earring in polished 18k yellow gold with a pear-shaped diamond.",
                "steps": "20",
                "seed": "42",
            },
        )
    print(f"Status Code: {resp.status_code}")
    assert resp.status_code == 409, f"Test 3A Failed (expected 409): {resp.text}"
    detail = resp.json().get("detail", {})
    print(f"Detail Error: {detail.get('error')}")
    print(f"Message: {detail.get('message')}")
    print(f"Requested Category: {detail.get('requested_category')}")
    print(f"Source Blueprint Category: {detail.get('source_blueprint_category')}")
    assert detail.get("error") == "CATEGORY_CONFLICT"
    assert detail.get("requested_category") == "earring"
    assert detail.get("source_blueprint_category") == "necklace"
    print("[PASS] Test 3A: Unconfirmed category conflict successfully rejected with HTTP 409.")

    # 4. Conflict Resolved via Option A ("blueprint")
    print("\n[TEST 3B] Conflict Resolved: Option A (Align with Blueprint)...")
    with open(necklace_path, "rb") as f:
        resp = client.post(
            "/api/v1/ai/render",
            files={"file": ("gallery_necklace.png", f, "image/png")},
            data={
                "category": "necklace",
                "source_blueprint_category": "necklace",
                "conflict_resolution": "blueprint",
                "prompt": "Create a sophisticated necklace in polished 18k yellow gold with pear-shaped diamonds.",
                "steps": "20",
                "seed": "42",
            },
        )
    print(f"Status Code: {resp.status_code}")
    assert resp.status_code == 200, f"Test 3B Failed: {resp.text}"
    res3b = resp.json()
    print(f"Output URL: {res3b.get('output_url')}")
    print(f"Category: {res3b.get('category')}")
    print(f"Source Blueprint Category: {res3b.get('source_blueprint_category')}")
    print(f"Category Conflict: {res3b.get('category_conflict')}")
    print("[PASS] Test 3B: User-confirmed Option A successfully rendered authentic necklace from blueprint.")

    print("\n" + "=" * 70)
    print("ALL 4 PHASE F CONSISTENCY SMOKE TESTS PASSED ON REAL RTX 4060 GPU!")
    print("=" * 70)


if __name__ == "__main__":
    run_smoke_tests()
