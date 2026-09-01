"""
Tests for structured exception handlers
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.exceptions import AppException, ResourceNotFoundException, ValidationException
from app.main import app_exception_handler
from app.core.middleware import RequestContextMiddleware

test_app = FastAPI()
test_app.add_middleware(RequestContextMiddleware)
test_app.add_exception_handler(AppException, app_exception_handler)


@test_app.get("/test-not-found")
def trigger_not_found():
    raise ResourceNotFoundException("Design", "12345")


@test_app.get("/test-validation")
def trigger_validation():
    raise ValidationException("Invalid metal carat", details={"field": "carat", "value": "99k"})


client = TestClient(test_app)


def test_resource_not_found_handling():
    response = client.get("/test-not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "Design with identifier '12345' was not found" in data["error"]["message"]
    assert "request_id" in data
    assert "X-Request-ID" in response.headers


def test_validation_error_handling():
    response = client.get("/test-validation")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["details"]["field"] == "carat"
