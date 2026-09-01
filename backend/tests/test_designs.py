"""
Jewellery Design Management API & Service Tests
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.design import Design
from app.services.user_service import user_service
from app.schemas.auth import UserCreate


def create_test_user(db: Session, email: str = "designer@jewelmind.com") -> User:
    """Helper to create a user for tests."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Artisan Tester",
        ),
    )


def get_auth_headers(user: User) -> dict:
    """Helper to generate JWT Bearer headers for a user."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_design_authenticated(client: TestClient, db_session: Session):
    """Authenticated user can successfully create a new design."""
    user = create_test_user(db_session, "creator@jewelmind.com")
    headers = get_auth_headers(user)

    payload = {
        "name": "Solitaire Diamond Ring",
        "description": "18k White Gold 6-prong solitaire setting",
        "category": "Ring",
        "status": "draft",
        "ai_prompt": "Photorealistic 18k white gold ring with 2 carat round brilliant diamond",
    }

    response = client.post("/api/v1/designs", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Solitaire Diamond Ring"
    assert data["category"] == "Ring"
    assert data["status"] == "draft"
    assert data["user_id"] == str(user.id)
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_design_unauthenticated(client: TestClient):
    """Unauthenticated request to create a design returns 401."""
    payload = {
        "name": "Royal Emerald Necklace",
        "category": "Necklace",
    }
    response = client.post("/api/v1/designs", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_create_design_validation_empty_name(client: TestClient, db_session: Session):
    """Design with blank name is rejected with 422."""
    user = create_test_user(db_session, "val_name@jewelmind.com")
    headers = get_auth_headers(user)

    payload = {
        "name": "   ",
        "category": "Ring",
    }
    response = client.post("/api/v1/designs", json=payload, headers=headers)
    assert response.status_code == 422


def test_create_design_validation_invalid_category(client: TestClient, db_session: Session):
    """Design with invalid category is rejected with 422."""
    user = create_test_user(db_session, "val_cat@jewelmind.com")
    headers = get_auth_headers(user)

    payload = {
        "name": "Fancy Tiara",
        "category": "InvalidCategoryName",
    }
    response = client.post("/api/v1/designs", json=payload, headers=headers)
    assert response.status_code == 422


def test_list_designs_and_pagination(client: TestClient, db_session: Session):
    """User can list their designs with pagination."""
    user = create_test_user(db_session, "lister@jewelmind.com")
    headers = get_auth_headers(user)

    # Create 3 designs
    for i in range(3):
        client.post(
            "/api/v1/designs",
            json={"name": f"Design {i+1}", "category": "Pendant"},
            headers=headers,
        )

    response = client.get("/api/v1/designs?page=1&page_size=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["pages"] == 2
    assert data["page"] == 1


def test_filter_designs_by_category_and_status(client: TestClient, db_session: Session):
    """Filtering by category and status returns matching subsets."""
    user = create_test_user(db_session, "filterer@jewelmind.com")
    headers = get_auth_headers(user)

    client.post("/api/v1/designs", json={"name": "Gold Ring", "category": "Ring", "status": "draft"}, headers=headers)
    client.post("/api/v1/designs", json={"name": "Silver Ring", "category": "Ring", "status": "ready"}, headers=headers)
    client.post("/api/v1/designs", json={"name": "Ruby Necklace", "category": "Necklace", "status": "draft"}, headers=headers)

    # Filter by category = Ring
    res_cat = client.get("/api/v1/designs?category=Ring", headers=headers)
    assert res_cat.status_code == 200
    data_cat = res_cat.json()
    assert data_cat["total"] == 2
    assert all(d["category"] == "Ring" for d in data_cat["items"])

    # Filter by category = Ring and status = ready
    res_both = client.get("/api/v1/designs?category=Ring&status=ready", headers=headers)
    assert res_both.status_code == 200
    data_both = res_both.json()
    assert data_both["total"] == 1
    assert data_both["items"][0]["name"] == "Silver Ring"


def test_search_designs_keyword(client: TestClient, db_session: Session):
    """Search queries match substrings in name or description."""
    user = create_test_user(db_session, "searcher@jewelmind.com")
    headers = get_auth_headers(user)

    client.post(
        "/api/v1/designs",
        json={"name": "Art Deco Platinum Band", "description": "Vintage filigree", "category": "Ring"},
        headers=headers,
    )
    client.post(
        "/api/v1/designs",
        json={"name": "Minimalist Hoop", "description": "14k yellow gold", "category": "Earrings"},
        headers=headers,
    )

    # Search for "Vintage"
    res = client.get("/api/v1/designs?search=Vintage", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Art Deco Platinum Band"


def test_get_single_design(client: TestClient, db_session: Session):
    """User can retrieve a single design by ID."""
    user = create_test_user(db_session, "singler@jewelmind.com")
    headers = get_auth_headers(user)

    create_res = client.post(
        "/api/v1/designs",
        json={"name": "Charm Bracelet", "category": "Bracelet"},
        headers=headers,
    )
    design_id = create_res.json()["id"]

    res = client.get(f"/api/v1/designs/{design_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == design_id
    assert res.json()["name"] == "Charm Bracelet"


def test_get_nonexistent_design(client: TestClient, db_session: Session):
    """Requesting non-existent design returns 404."""
    user = create_test_user(db_session, "nonexistent@jewelmind.com")
    headers = get_auth_headers(user)

    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/designs/{fake_id}", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "DESIGN_NOT_FOUND"


def test_update_design(client: TestClient, db_session: Session):
    """User can update mutable properties of their design."""
    user = create_test_user(db_session, "updater@jewelmind.com")
    headers = get_auth_headers(user)

    create_res = client.post(
        "/api/v1/designs",
        json={"name": "Initial Name", "category": "Ring", "status": "draft"},
        headers=headers,
    )
    design_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/designs/{design_id}",
        json={
            "name": "Updated Luxury Name",
            "status": "ready",
            "description": "Added detailed specification",
        },
        headers=headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "Updated Luxury Name"
    assert data["status"] == "ready"
    assert data["description"] == "Added detailed specification"
    assert data["category"] == "Ring"


def test_delete_design(client: TestClient, db_session: Session):
    """User can delete their design, removing it permanently."""
    user = create_test_user(db_session, "deleter@jewelmind.com")
    headers = get_auth_headers(user)

    create_res = client.post(
        "/api/v1/designs",
        json={"name": "To Be Deleted", "category": "Bangle"},
        headers=headers,
    )
    design_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/designs/{design_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/designs/{design_id}", headers=headers)
    assert get_res.status_code == 404


def test_multi_user_isolation_security(client: TestClient, db_session: Session):
    """
    CRITICAL SECURITY TEST:
    User A's designs cannot be read, listed, modified, or deleted by User B.
    All unauthorized access attempts must return 404 DESIGN_NOT_FOUND (zero leakage).
    """
    user_a = create_test_user(db_session, "user_a@jewelmind.com")
    user_b = create_test_user(db_session, "user_b@jewelmind.com")

    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    # User A creates a secret design
    create_res = client.post(
        "/api/v1/designs",
        json={
            "name": "User A Proprietary Ring",
            "description": "Secret bridal design",
            "category": "Ring",
        },
        headers=headers_a,
    )
    design_a_id = create_res.json()["id"]

    # 1. User B lists designs -> User A's design MUST NOT appear
    list_b = client.get("/api/v1/designs", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0
    assert len(list_b.json()["items"]) == 0

    # 2. User B tries to read User A's design -> 404
    get_b = client.get(f"/api/v1/designs/{design_a_id}", headers=headers_b)
    assert get_b.status_code == 404
    assert get_b.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # 3. User B tries to update User A's design -> 404
    patch_b = client.patch(
        f"/api/v1/designs/{design_a_id}",
        json={"name": "Hijacked Name"},
        headers=headers_b,
    )
    assert patch_b.status_code == 404
    assert patch_b.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # 4. User B tries to delete User A's design -> 404
    del_b = client.delete(f"/api/v1/designs/{design_a_id}", headers=headers_b)
    assert del_b.status_code == 404
    assert del_b.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # 5. Verify User A's design is completely intact
    get_a = client.get(f"/api/v1/designs/{design_a_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["name"] == "User A Proprietary Ring"
