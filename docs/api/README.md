# API Documentation

This directory documents the RESTful API endpoints for the JewelMind backend service.

---

## Planned API Routing Structure

```text
/api
├── /auth            # User registration, login, token refresh, logout
├── /users           # User profile management and preferences
├── /designs         # Jewellery design CRUD, metadata, and category filters
├── /sketches        # Sketch upload, image preprocessing, and file management
├── /ai              # AI Job dispatch, status polling, and result retrieval
├── /predictions     # Material, cost, time, and wastage estimation endpoints
├── /production      # Production orders, artisan skills, and machine capacity
└── /optimization    # Workshop schedule generation and timeline queries
```

FastAPI automatically serves interactive Swagger UI documentation at `/docs` and ReDoc at `/redoc`.
