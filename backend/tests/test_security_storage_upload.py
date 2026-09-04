"""
Security Regression Tests: Storage & File Upload Security
Validates MIME whitelisting, file extension checks, magic bytes verification,
oversized upload rejection, malicious filename path traversal protection, and safe key generation.
"""

import io
from fastapi.testclient import TestClient
from PIL import Image

from app.services.storage_service import storage_service


def _get_auth_headers_and_design(client: TestClient):
    res = client.post("/api/v1/auth/register", json={
        "email": "upload_tester@jewelmind.com",
        "full_name": "Upload Tester",
        "password": "UploadPassword2026!",
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    des = client.post(
        "/api/v1/designs",
        json={"name": "Upload Target Design", "category": "Ring"},
        headers=headers,
    ).json()
    return headers, des["id"]


def test_upload_empty_file_rejected(client: TestClient):
    """Empty files must be rejected with 400."""
    headers, design_id = _get_auth_headers_and_design(client)

    response = client.post(
        f"/api/v1/designs/{design_id}/sketch",
        files={"file": ("empty.png", b"", "image/png")},
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_FILE"


def test_upload_disallowed_mime_types(client: TestClient):
    """Executable, script, or document MIME types must be rejected."""
    headers, design_id = _get_auth_headers_and_design(client)

    disallowed = [
        ("malicious.exe", b"MZ\x90\x00\x03\x00", "application/x-msdownload"),
        ("script.php", b"<?php phpinfo(); ?>", "application/x-php"),
        ("document.pdf", b"%PDF-1.4...", "application/pdf"),
        ("vector.svg", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "image/svg+xml"),
        ("hack.html", b"<html><body><script>alert(1)</script></body></html>", "text/html"),
    ]

    for filename, content, mime in disallowed:
        res = client.post(
            f"/api/v1/designs/{design_id}/sketch",
            files={"file": (filename, content, mime)},
            headers=headers,
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_upload_magic_bytes_corruption_check(client: TestClient):
    """Files with image extensions but non-matching magic bytes are rejected."""
    headers, design_id = _get_auth_headers_and_design(client)

    # Fake PNG containing plain ASCII text
    fake_png = b"This is not a real PNG image header."
    res = client.post(
        f"/api/v1/designs/{design_id}/sketch",
        files={"file": ("fake.png", fake_png, "image/png")},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "CORRUPT_FILE_CONTENT"


def test_upload_oversized_file_rejected(client: TestClient):
    """Files exceeding MAX_UPLOAD_SIZE_BYTES (10MB) must be rejected with 413."""
    headers, design_id = _get_auth_headers_and_design(client)

    # Create 11MB pseudo payload with PNG header
    oversized_bytes = b"\x89PNG\r\n\x1a\n" + (b"0" * (11 * 1024 * 1024))
    res = client.post(
        f"/api/v1/designs/{design_id}/sketch",
        files={"file": ("huge.png", oversized_bytes, "image/png")},
        headers=headers,
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_storage_path_sanitization_and_random_keys():
    """Verify storage key generator eliminates directory traversal sequences."""
    malicious_filenames = [
        "../../etc/passwd.png",
        "..\\..\\windows\\system32\\calc.png",
        "../../../sketch.png",
        "../../../../../../root/.ssh/id_rsa.png",
    ]

    for malicious_name in malicious_filenames:
        path, unique_name = storage_service.generate_storage_path(
            user_id="11111111-1111-1111-1111-111111111111",
            design_id="22222222-2222-2222-2222-222222222222",
            original_filename=malicious_name,
            content_type="image/png",
        )
        assert ".." not in path
        assert "\\" not in path
        assert unique_name.startswith("sketch_")
        assert unique_name.endswith(".png")
        assert path.startswith("11111111-1111-1111-1111-111111111111/22222222-2222-2222-2222-222222222222/")


def test_ai_render_output_path_traversal_rejection(client: TestClient):
    """Verify /outputs/{filename} blocks path traversal attempts."""
    traversal_paths = [
        "../../app/core/config.py",
        "..%2F..%2F.env",
        "....//....//etc/passwd",
    ]
    for bad_path in traversal_paths:
        res = client.get(f"/api/v1/ai/render/outputs/{bad_path}")
        assert res.status_code in (404, 422)
