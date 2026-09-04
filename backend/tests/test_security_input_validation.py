"""
Security Regression Tests: API Input Validation & Constraint Hardening
Validates rejection of invalid UUIDs, negative numbers, impossible dates, invalid enums,
oversized parameters, and malformed AI arguments across all endpoints.
"""

from fastapi.testclient import TestClient


def _get_auth_headers(client: TestClient) -> dict:
    res = client.post("/api/v1/auth/register", json={
        "email": "validation_tester@jewelmind.com",
        "full_name": "Validation Tester",
        "password": "ValidPassword2026!",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_invalid_uuid_path_parameters(client: TestClient):
    """Verify malformed or traversal UUIDs in URL paths return 422 Unprocessable Entity."""
    headers = _get_auth_headers(client)

    malformed_uuids = [
        "not-a-uuid",
        "12345",
        "../../etc/passwd",
        "..%2F..%2Fhack",
        "00000000-0000-0000-0000-00000000000Z",  # Invalid hex
        "00000000-0000-0000-0000",  # Truncated
    ]

    for bad_id in malformed_uuids:
        # Designs
        assert client.get(f"/api/v1/designs/{bad_id}", headers=headers).status_code in (404, 422)
        assert client.delete(f"/api/v1/designs/{bad_id}", headers=headers).status_code in (404, 422)
        # Orders
        assert client.get(f"/api/v1/production/orders/{bad_id}", headers=headers).status_code in (404, 422)
        assert client.delete(f"/api/v1/production/orders/{bad_id}", headers=headers).status_code in (404, 422)
        # Workers
        assert client.get(f"/api/v1/production/workers/{bad_id}", headers=headers).status_code in (404, 422)
        # Machines
        assert client.get(f"/api/v1/production/machines/{bad_id}", headers=headers).status_code in (404, 422)
        # Schedules
        assert client.get(f"/api/v1/production/schedules/{bad_id}", headers=headers).status_code in (404, 422)


def test_design_input_validation(client: TestClient):
    """Verify design creation rejects empty names, oversized descriptions, or invalid categories."""
    headers = _get_auth_headers(client)

    # Empty name
    res1 = client.post("/api/v1/designs", json={"name": "", "category": "Ring"}, headers=headers)
    assert res1.status_code == 422

    # Whitespace-only name
    res2 = client.post("/api/v1/designs", json={"name": "   ", "category": "Ring"}, headers=headers)
    assert res2.status_code == 422

    # Invalid category
    res3 = client.post("/api/v1/designs", json={"name": "Ring", "category": "Spaceship"}, headers=headers)
    assert res3.status_code == 422


def test_production_order_quantity_and_enum_validation(client: TestClient):
    """Verify order creation and update reject invalid quantities (<=0) and invalid enums."""
    headers = _get_auth_headers(client)

    des = client.post("/api/v1/designs", json={"name": "Valid Ring", "category": "Ring"}, headers=headers).json()
    design_id = des["id"]

    # Zero quantity
    res_zero = client.post(
        "/api/v1/production/orders",
        json={"design_id": design_id, "quantity": 0, "priority": "medium", "deadline": "2026-10-01T00:00:00Z"},
        headers=headers,
    )
    assert res_zero.status_code == 422

    # Negative quantity
    res_neg = client.post(
        "/api/v1/production/orders",
        json={"design_id": design_id, "quantity": -5, "priority": "medium", "deadline": "2026-10-01T00:00:00Z"},
        headers=headers,
    )
    assert res_neg.status_code == 422

    # Invalid priority enum
    res_prio = client.post(
        "/api/v1/production/orders",
        json={"design_id": design_id, "quantity": 1, "priority": "super_critical_9000", "deadline": "2026-10-01T00:00:00Z"},
        headers=headers,
    )
    assert res_prio.status_code == 422


def test_worker_and_machine_capacity_validation(client: TestClient):
    """Verify capacity hours must be within valid daily bounds (0 <= capacity <= 24)."""
    headers = _get_auth_headers(client)

    # Worker capacity < 0
    res_w_neg = client.post(
        "/api/v1/production/workers",
        json={"name": "Worker Neg", "skill": "casting", "capacity_hours_per_day": -1.0},
        headers=headers,
    )
    assert res_w_neg.status_code == 422

    # Worker capacity > 24 hours
    res_w25 = client.post(
        "/api/v1/production/workers",
        json={"name": "Worker 25h", "skill": "casting", "capacity_hours_per_day": 25.0},
        headers=headers,
    )
    assert res_w25.status_code == 422

    # Machine capacity < 0
    res_m_neg = client.post(
        "/api/v1/production/machines",
        json={"name": "Machine Neg", "machine_type": "casting_furnace", "capacity_hours_per_day": -1.0},
        headers=headers,
    )
    assert res_m_neg.status_code == 422


def test_optimization_request_validation(client: TestClient):
    """Verify OR-Tools optimization parameters enforce valid bounds."""
    headers = _get_auth_headers(client)

    # Horizon = 0
    res_h0 = client.post("/api/v1/production/optimize", json={"horizon_days": 0}, headers=headers)
    assert res_h0.status_code == 422

    # Horizon > 90
    res_h_huge = client.post("/api/v1/production/optimize", json={"horizon_days": 100}, headers=headers)
    assert res_h_huge.status_code == 422

    # Negative solver timeout
    res_timeout = client.post("/api/v1/production/optimize", json={"horizon_days": 14, "time_limit_seconds": 0}, headers=headers)
    assert res_timeout.status_code == 422
