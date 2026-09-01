# API Conventions & Architecture Standards

> **Document Version:** 1.0.0 (Phase 1 Foundation)  
> **API Base URL:** `/api/v1`  

---

## 1. API Versioning
All domain feature endpoints are hosted under the versioned prefix `/api/v1/`.  
Root `/` and `/health` endpoints are maintained for general orchestration checks and backwards compatibility.

---

## 2. Standard Response Wrapper
Endpoints returning application data utilize the standardized JSON response structure:

```json
{
  "success": true,
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Diamond Solitaire Ring"
  },
  "message": "Design created successfully",
  "request_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

---

## 3. Standard Error Response Wrapper
All handled and unhandled errors return a consistent, machine-parseable schema without exposing internal system details or stack traces:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Design with identifier '12345' was not found.",
    "details": {
      "resource": "Design",
      "identifier": "12345"
    }
  },
  "request_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

---

## 4. HTTP Status Code Guidelines

| Status Code | Usage | Meaning |
| :--- | :--- | :--- |
| `200 OK` | Successful read or sync update | Request succeeded |
| `201 Created` | Successful entity creation | Resource created |
| `202 Accepted` | Async task enqueued | AI job placed in queue |
| `204 No Content` | Successful deletion | Entity deleted |
| `400 Bad Request` | Malformed request body/syntax | Client error |
| `401 Unauthorized` | Missing/invalid authentication token | Authentication required |
| `403 Forbidden` | Authenticated user lacks permission | Access denied |
| `404 Not Found` | Entity not found in database | Resource does not exist |
| `422 Unprocessable Entity` | Pydantic validation failure | Invalid input fields |
| `429 Too Many Requests` | Rate limit exceeded | Back off and retry |
| `500 Internal Server Error` | Unexpected backend error | Server error (sanitized) |
| `503 Service Unavailable` | Downstream worker offline | External service unavailable |

---

## 5. Tracing & Correlation Headers
Every request passing through FastAPI receives:
- `X-Request-ID`: Unique correlation UUID injected via `RequestContextMiddleware`.
- `X-Process-Time-Ms`: Execution latency in milliseconds.
