"""
Jewellery Sketch Asset Management & Supabase Storage Tests
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.services.user_service import user_service
from app.schemas.auth import UserCreate


# Helper minimal valid image byte fixtures
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
VALID_WEBP_BYTES = b"RIFF\x1a\x00\x00\x00WEBPVP8L\x0e\x00\x00\x00/\x00\x00\x00\x00\x07\x08\x88\x01\x00"


def create_test_user(db: Session, email: str = "sketcher@jewelmind.com") -> User:
    """Helper to create a user for tests."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Sketch Artisan",
        ),
    )


def get_auth_headers(user: User) -> dict:
    """Helper to generate JWT Bearer headers."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def create_user_design(client: TestClient, headers: dict, name: str = "Diamond Solitaire Ring") -> str:
    """Helper to create a design and return its ID."""
    res = client.post(
        "/api/v1/designs",
        json={"name": name, "category": "Ring", "status": "draft"},
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_unauthenticated_upload_rejected(client: TestClient):
    """Unauthenticated upload request returns 401."""
    fake_design_id = str(uuid.uuid4())
    files = {"file": ("sketch.png", VALID_PNG_BYTES, "image/png")}
    res = client.post(f"/api/v1/designs/{fake_design_id}/sketch", files=files)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_unauthenticated_delete_rejected(client: TestClient):
    """Unauthenticated sketch deletion request returns 401."""
    fake_design_id = str(uuid.uuid4())
    res = client.delete(f"/api/v1/designs/{fake_design_id}/sketch")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_upload_sketch_png_success(client: TestClient, db_session: Session):
    """Authenticated user can upload a valid PNG sketch."""
    user = create_test_user(db_session, "png_user@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Emerald Ring")

    files = {"file": ("emerald_sketch.png", VALID_PNG_BYTES, "image/png")}
    res = client.post(f"/api/v1/designs/{design_id}/sketch", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == design_id
    assert data["sketch_image_url"] is not None
    assert str(user.id) in data["sketch_image_url"]
    assert str(design_id) in data["sketch_image_url"]
    assert data["sketch_image_url"].endswith(".png")


def test_upload_sketch_jpeg_success(client: TestClient, db_session: Session):
    """Authenticated user can upload a valid JPEG sketch."""
    user = create_test_user(db_session, "jpg_user@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Gold Necklace")

    files = {"file": ("necklace.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    res = client.post(f"/api/v1/designs/{design_id}/sketch", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["sketch_image_url"] is not None
    assert data["sketch_image_url"].endswith(".jpg")


def test_upload_sketch_webp_success(client: TestClient, db_session: Session):
    """Authenticated user can upload a valid WEBP sketch."""
    user = create_test_user(db_session, "webp_user@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Sapphire Pendant")

    files = {"file": ("pendant.webp", VALID_WEBP_BYTES, "image/webp")}
    res = client.post(f"/api/v1/designs/{design_id}/sketch", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["sketch_image_url"] is not None
    assert data["sketch_image_url"].endswith(".webp")


def test_upload_unsupported_mime_rejected(client: TestClient, db_session: Session):
    """Uploading unsupported MIME types (e.g. PDF, SVG, TXT) is rejected with 400."""
    user = create_test_user(db_session, "invalid_mime@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Ruby Earrings")

    # Attempt PDF
    files_pdf = {"file": ("blueprint.pdf", b"%PDF-1.4 fake pdf data", "application/pdf")}
    res_pdf = client.post(f"/api/v1/designs/{design_id}/sketch", files=files_pdf, headers=headers)
    assert res_pdf.status_code == 400
    assert res_pdf.json()["error"]["code"] == "INVALID_FILE_TYPE"

    # Attempt SVG
    files_svg = {"file": ("vector.svg", b"<svg>fake</svg>", "image/svg+xml")}
    res_svg = client.post(f"/api/v1/designs/{design_id}/sketch", files=files_svg, headers=headers)
    assert res_svg.status_code == 400
    assert res_svg.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_upload_oversized_file_rejected(client: TestClient, db_session: Session):
    """Uploading a file exceeding 10MB is rejected with 413."""
    user = create_test_user(db_session, "large_file@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Platinum Bracelet")

    # 10.5 MB oversized payload
    oversized_bytes = b"\x89PNG\r\n\x1a\n" + b"A" * (11 * 1024 * 1024)
    files = {"file": ("giant_sketch.png", oversized_bytes, "image/png")}
    res = client.post(f"/api/v1/designs/{design_id}/sketch", files=files, headers=headers)
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_empty_file_rejected(client: TestClient, db_session: Session):
    """Uploading an empty 0-byte file is rejected with 400."""
    user = create_test_user(db_session, "empty_file@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Silver Bangle")

    files = {"file": ("empty.png", b"", "image/png")}
    res = client.post(f"/api/v1/designs/{design_id}/sketch", files=files, headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "EMPTY_FILE"


def test_cross_user_upload_forbidden(client: TestClient, db_session: Session):
    """User B cannot upload a sketch to User A's design (returns 404)."""
    user_a = create_test_user(db_session, "owner_a@jewelmind.com")
    user_b = create_test_user(db_session, "intruder_b@jewelmind.com")

    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    design_a_id = create_user_design(client, headers_a, "Proprietary Ring")

    # User B attempts to upload sketch
    files = {"file": ("hacked.png", VALID_PNG_BYTES, "image/png")}
    res = client.post(f"/api/v1/designs/{design_a_id}/sketch", files=files, headers=headers_b)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "DESIGN_NOT_FOUND"


def test_cross_user_delete_forbidden(client: TestClient, db_session: Session):
    """User B cannot delete a sketch from User A's design (returns 404)."""
    user_a = create_test_user(db_session, "owner_del@jewelmind.com")
    user_b = create_test_user(db_session, "intruder_del@jewelmind.com")

    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    design_a_id = create_user_design(client, headers_a, "Secure Pendant")

    # User A uploads sketch
    files = {"file": ("sketch.png", VALID_PNG_BYTES, "image/png")}
    client.post(f"/api/v1/designs/{design_a_id}/sketch", files=files, headers=headers_a)

    # User B attempts deletion
    del_res = client.delete(f"/api/v1/designs/{design_a_id}/sketch", headers=headers_b)
    assert del_res.status_code == 404
    assert del_res.json()["error"]["code"] == "DESIGN_NOT_FOUND"


def test_replace_sketch_flow(client: TestClient, db_session: Session):
    """Replacing an existing sketch updates the URL with the new asset."""
    user = create_test_user(db_session, "replacer@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Bridal Tiara")

    # 1. First upload
    files_1 = {"file": ("initial.png", VALID_PNG_BYTES, "image/png")}
    res_1 = client.post(f"/api/v1/designs/{design_id}/sketch", files=files_1, headers=headers)
    assert res_1.status_code == 200
    initial_url = res_1.json()["sketch_image_url"]

    # 2. Second upload (Replacement)
    files_2 = {"file": ("revised.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    res_2 = client.post(f"/api/v1/designs/{design_id}/sketch", files=files_2, headers=headers)
    assert res_2.status_code == 200
    revised_url = res_2.json()["sketch_image_url"]

    assert revised_url is not None
    assert revised_url != initial_url
    assert revised_url.endswith(".jpg")


def test_delete_sketch_success(client: TestClient, db_session: Session):
    """Deleting a sketch removes the URL and keeps the parent design entity intact."""
    user = create_test_user(db_session, "deleter_sketch@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Diamond Studs")

    # 1. Upload sketch
    files = {"file": ("studs.png", VALID_PNG_BYTES, "image/png")}
    client.post(f"/api/v1/designs/{design_id}/sketch", files=files, headers=headers)

    # 2. Delete sketch
    del_res = client.delete(f"/api/v1/designs/{design_id}/sketch", headers=headers)
    assert del_res.status_code == 200
    data = del_res.json()
    assert data["sketch_image_url"] is None
    assert data["name"] == "Diamond Studs"

    # 3. Verify Design still exists
    get_res = client.get(f"/api/v1/designs/{design_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["sketch_image_url"] is None
    assert get_res.json()["name"] == "Diamond Studs"


def test_delete_sketch_when_none_exists(client: TestClient, db_session: Session):
    """Deleting a sketch when none is attached is a safe 200 operation."""
    user = create_test_user(db_session, "no_sketch_del@jewelmind.com")
    headers = get_auth_headers(user)
    design_id = create_user_design(client, headers, "Gold Choker")

    del_res = client.delete(f"/api/v1/designs/{design_id}/sketch", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["sketch_image_url"] is None
