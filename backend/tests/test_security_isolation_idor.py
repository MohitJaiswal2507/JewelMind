"""
Security Regression Tests: Multi-Tenant Isolation & IDOR Protection
Ensures strict object-level authorization across User A and User B:
- Designs, sketches, and AI renders
- Production orders, artisan workers, workshop machines
- CP-SAT optimization and generated schedules
- Dashboard aggregated analytics
"""

import io
from fastapi.testclient import TestClient
from PIL import Image


def _get_auth_tokens(client: TestClient):
    """Helper creating two isolated test users and returning their auth headers."""
    res_a = client.post("/api/v1/auth/register", json={
        "email": "user_a@tenant.com",
        "full_name": "Tenant User A",
        "password": "PasswordUserA123!",
    })
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res_b = client.post("/api/v1/auth/register", json={
        "email": "user_b@tenant.com",
        "full_name": "Tenant User B",
        "password": "PasswordUserB123!",
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    return headers_a, headers_b


def test_cross_tenant_design_idor_isolation(client: TestClient):
    """User B cannot read, update, or delete User A's design."""
    headers_a, headers_b = _get_auth_tokens(client)

    # 1. User A creates a design
    create_res = client.post(
        "/api/v1/designs",
        json={"name": "User A Solitaire Ring", "category": "Ring", "description": "Private Design"},
        headers=headers_a,
    )
    assert create_res.status_code == 201
    design_id = create_res.json()["id"]

    # 2. User B attempts to read User A's design (GET)
    get_res = client.get(f"/api/v1/designs/{design_id}", headers=headers_b)
    assert get_res.status_code == 404
    assert get_res.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # 3. User B attempts to modify User A's design (PATCH)
    patch_res = client.patch(
        f"/api/v1/designs/{design_id}",
        json={"name": "Hacked Name"},
        headers=headers_b,
    )
    assert patch_res.status_code == 404
    assert patch_res.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # 4. User B attempts to delete User A's design (DELETE)
    del_res = client.delete(f"/api/v1/designs/{design_id}", headers=headers_b)
    assert del_res.status_code == 404
    assert del_res.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # 5. Verify User A's design is untouched
    verify_res = client.get(f"/api/v1/designs/{design_id}", headers=headers_a)
    assert verify_res.status_code == 200
    assert verify_res.json()["name"] == "User A Solitaire Ring"


def test_cross_tenant_sketch_and_render_isolation(client: TestClient):
    """User B cannot upload sketch, delete sketch, or render for User A's design."""
    headers_a, headers_b = _get_auth_tokens(client)

    # User A creates a design
    des = client.post(
        "/api/v1/designs",
        json={"name": "User A Diamond Pendant", "category": "Pendant"},
        headers=headers_a,
    ).json()
    design_id = des["id"]

    # Generate a small valid PNG in-memory
    img_buf = io.BytesIO()
    Image.new("RGB", (256, 256), color="white").save(img_buf, format="PNG")
    png_bytes = img_buf.getvalue()

    # User B attempts to upload a sketch to User A's design
    upload_res = client.post(
        f"/api/v1/designs/{design_id}/sketch",
        files={"file": ("malicious_sketch.png", png_bytes, "image/png")},
        headers=headers_b,
    )
    assert upload_res.status_code == 404
    assert upload_res.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # User B attempts to delete sketch from User A's design
    del_sketch_res = client.delete(
        f"/api/v1/designs/{design_id}/sketch",
        headers=headers_b,
    )
    assert del_sketch_res.status_code == 404
    assert del_sketch_res.json()["error"]["code"] == "DESIGN_NOT_FOUND"

    # User B attempts to trigger AI render attaching to User A's design
    ai_render_res = client.post(
        "/api/v1/ai/render",
        files={"file": ("sketch.png", png_bytes, "image/png")},
        data={"category": "pendant", "design_id": design_id},
        headers=headers_b,
    )
    assert ai_render_res.status_code == 404


def test_cross_tenant_production_order_isolation(client: TestClient):
    """User B cannot access or manipulate User A's production orders or link orders to User A's designs."""
    headers_a, headers_b = _get_auth_tokens(client)

    # User A creates a design & order
    des_a = client.post("/api/v1/designs", json={"name": "Design A", "category": "Ring"}, headers=headers_a).json()
    order_a = client.post(
        "/api/v1/production/orders",
        json={"design_id": des_a["id"], "quantity": 10, "priority": "high", "deadline": "2026-10-01T00:00:00Z"},
        headers=headers_a,
    ).json()
    order_id = order_a["id"]

    # User B attempts to create an order referencing User A's design
    spoofed_order = client.post(
        "/api/v1/production/orders",
        json={"design_id": des_a["id"], "quantity": 5, "priority": "medium", "deadline": "2026-10-01T00:00:00Z"},
        headers=headers_b,
    )
    assert spoofed_order.status_code == 404

    # User B attempts to GET User A's order
    assert client.get(f"/api/v1/production/orders/{order_id}", headers=headers_b).status_code == 404

    # User B attempts to PUT/PATCH User A's order
    assert client.patch(f"/api/v1/production/orders/{order_id}", json={"quantity": 99}, headers=headers_b).status_code == 404

    # User B attempts to DELETE User A's order
    assert client.delete(f"/api/v1/production/orders/{order_id}", headers=headers_b).status_code == 404

    # User B's order list does not contain User A's order
    list_b = client.get("/api/v1/production/orders", headers=headers_b).json()
    assert list_b["total"] == 0
    assert len(list_b["items"]) == 0


def test_cross_tenant_worker_and_machine_isolation(client: TestClient):
    """User B cannot view or modify User A's artisan workers or machinery."""
    headers_a, headers_b = _get_auth_tokens(client)

    # User A creates a worker and a machine
    w_a = client.post(
        "/api/v1/production/workers",
        json={"name": "Master Goldsmith A", "skill": "casting", "capacity_hours_per_day": 8.0},
        headers=headers_a,
    ).json()
    m_a = client.post(
        "/api/v1/production/machines",
        json={"name": "Furnace A", "machine_type": "casting_furnace", "capacity_hours_per_day": 8.0},
        headers=headers_a,
    ).json()

    # User B attempts to access worker A
    assert client.get(f"/api/v1/production/workers/{w_a['id']}", headers=headers_b).status_code == 404
    assert client.patch(f"/api/v1/production/workers/{w_a['id']}", json={"name": "Hacked"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/production/workers/{w_a['id']}", headers=headers_b).status_code == 404

    # User B attempts to access machine A
    assert client.get(f"/api/v1/production/machines/{m_a['id']}", headers=headers_b).status_code == 404
    assert client.patch(f"/api/v1/production/machines/{m_a['id']}", json={"name": "Hacked"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/production/machines/{m_a['id']}", headers=headers_b).status_code == 404

    # User B lists workers and machines
    assert len(client.get("/api/v1/production/workers", headers=headers_b).json()["items"]) == 0
    assert len(client.get("/api/v1/production/machines", headers=headers_b).json()["items"]) == 0


def test_cross_tenant_schedule_and_optimization_isolation(client: TestClient):
    """User B cannot access User A's saved optimization schedules, and solver isolates tenants."""
    headers_a, headers_b = _get_auth_tokens(client)

    # 1. Setup User A full production environment
    des_a = client.post("/api/v1/designs", json={"name": "Ring A", "category": "Ring"}, headers=headers_a).json()
    client.post(
        "/api/v1/production/orders",
        json={"design_id": des_a["id"], "quantity": 2, "priority": "high", "deadline": "2026-10-01T00:00:00Z"},
        headers=headers_a,
    )
    client.post(
        "/api/v1/production/workers",
        json={"name": "Artisan A", "skill": "casting", "capacity_hours_per_day": 8.0},
        headers=headers_a,
    )
    client.post(
        "/api/v1/production/machines",
        json={"name": "Furnace A", "machine_type": "casting_furnace", "capacity_hours_per_day": 8.0},
        headers=headers_a,
    )

    # User A runs CP-SAT optimization
    opt_res = client.post(
        "/api/v1/production/optimize",
        json={"horizon_days": 14},
        headers=headers_a,
    )
    assert opt_res.status_code == 200

    # User A lists saved schedules
    schedules_a = client.get("/api/v1/production/schedules", headers=headers_a).json()
    if schedules_a["total"] > 0:
        schedule_id = schedules_a["items"][0]["id"]

        # User B attempts to retrieve User A's schedule
        get_b = client.get(f"/api/v1/production/schedules/{schedule_id}", headers=headers_b)
        assert get_b.status_code == 404
        assert get_b.json()["error"]["code"] == "SCHEDULE_NOT_FOUND"

        # User B attempts to delete User A's schedule
        del_b = client.delete(f"/api/v1/production/schedules/{schedule_id}", headers=headers_b)
        assert del_b.status_code == 404
        assert del_b.json()["error"]["code"] == "SCHEDULE_NOT_FOUND"

    # User B lists schedules
    schedules_b = client.get("/api/v1/production/schedules", headers=headers_b).json()
    assert schedules_b["total"] == 0


def test_cross_tenant_dashboard_isolation(client: TestClient):
    """Dashboard aggregate metrics and analytics remain strictly partitioned per tenant."""
    headers_a, headers_b = _get_auth_tokens(client)

    # User A creates 3 designs and 1 order
    for i in range(3):
        d = client.post("/api/v1/designs", json={"name": f"Ring {i}", "category": "Ring"}, headers=headers_a).json()
        if i == 0:
            client.post(
                "/api/v1/production/orders",
                json={"design_id": d["id"], "quantity": 5, "priority": "high", "deadline": "2026-10-01T00:00:00Z"},
                headers=headers_a,
            )

    # User A dashboard
    dash_a = client.get("/api/v1/dashboard/overview", headers=headers_a).json()
    assert dash_a["kpis"]["total_designs"] == 3
    assert dash_a["kpis"]["total_orders"] == 1

    # User B dashboard
    dash_b = client.get("/api/v1/dashboard/overview", headers=headers_b).json()
    assert dash_b["kpis"]["total_designs"] == 0
    assert dash_b["kpis"]["total_orders"] == 0
    assert len(dash_b["recent_designs"]) == 0
    assert len(dash_b["upcoming_deadlines"]) == 0
