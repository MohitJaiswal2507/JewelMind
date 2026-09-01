# Database Architecture & Entity Design

> **Document Version:** 1.0.0 (Phase 1 Foundation)  
> **Status:** Architectural Specification & Conceptual Data Model  

---

## 1. Overview
JewelMind utilizes a relational database architecture managed via **SQLAlchemy ORM** and **Alembic migrations**, targeting PostgreSQL (hosted on the Supabase free tier in production and compatible with standard local PostgreSQL instances).

---

## 2. Core Architectural Conventions

1. **Primary Keys:** Standard UUID v4 (`UUID(as_uuid=True)`) across all business entities.
2. **Timestamps:** Automatic `created_at` and `updated_at` UTC timestamps (`TimestampMixin`).
3. **Table Naming:** Lowercase plural with snake_case (`users`, `designs`, `sketches`, `ai_jobs`, `ai_results`, `jewellery_components`, `predictions`, `production_orders`, `production_schedules`).
4. **Foreign Keys:** Explicit relational constraints with cascading delete rules where parent entities dictate lifecycle (e.g. deleting a Design cascades to Sketches and Components).
5. **Enums & State Machines:** Strict enum values for status columns to ensure deterministic state transitions.

---

## 3. Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    USERS ||--o{ DESIGNS : owns
    DESIGNS ||--o{ SKETCHES : contains
    DESIGNS ||--o{ AI_JOBS : triggers
    AI_JOBS ||--o| AI_RESULTS : produces
    DESIGNS ||--o{ JEWELLERY_COMPONENTS : composed_of
    DESIGNS ||--o{ PREDICTIONS : has
    DESIGNS ||--o{ PRODUCTION_ORDERS : scheduled_as
    PRODUCTION_ORDERS ||--o| PRODUCTION_SCHEDULES : allocated_in

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string role
        datetime created_at
        datetime updated_at
    }

    DESIGNS {
        uuid id PK
        uuid user_id FK
        string title
        string category
        string description
        string status
        datetime created_at
        datetime updated_at
    }

    SKETCHES {
        uuid id PK
        uuid design_id FK
        string original_image_url
        string preprocessed_image_url
        int width_px
        int height_px
        datetime created_at
    }

    AI_JOBS {
        uuid id PK
        uuid design_id FK
        uuid user_id FK
        string job_type
        string status
        string worker_id
        datetime started_at
        datetime completed_at
        string error_message
        datetime created_at
    }

    AI_RESULTS {
        uuid id PK
        uuid job_id FK
        string rendered_image_url
        jsonb metadata_payload
        float inference_time_sec
        datetime created_at
    }

    JEWELLERY_COMPONENTS {
        uuid id PK
        uuid design_id FK
        string component_type
        float confidence
        jsonb bounding_box
        int count
        datetime created_at
    }

    PREDICTIONS {
        uuid id PK
        uuid design_id FK
        string metal_type
        float estimated_metal_weight_g
        float estimated_stone_weight_cts
        float estimated_cost_inr
        float estimated_labor_hours
        float estimated_wastage_percentage
        float manufacturability_score
        jsonb warning_flags
        datetime created_at
    }

    PRODUCTION_ORDERS {
        uuid id PK
        uuid design_id FK
        int quantity
        string priority
        datetime target_deadline
        string status
        datetime created_at
    }

    PRODUCTION_SCHEDULES {
        uuid id PK
        uuid order_id FK
        string assigned_worker
        string assigned_machine
        datetime scheduled_start
        datetime scheduled_end
        string solver_status
        datetime created_at
    }
```

---

## 4. Entity Lifecycle & State Machines

### 4.1 AI Job State Machine
```text
[QUEUED] ───► [PROCESSING] ───► [COMPLETED]
                   │
                   └───► [FAILED] (with error_message)
```

- **`QUEUED`:** Job created by FastAPI backend, awaiting worker pickup.
- **`PROCESSING`:** Worker leased the job, executing model inference (YOLO, Diffusion, XGBoost, OR-Tools).
- **`COMPLETED`:** Output artifact saved to Supabase Storage, result payload persisted in `ai_results`.
- **`FAILED`:** Inference failure or timeout; sanitized error logged.

---

## 5. Storage Tier Alignment
- **PostgreSQL:** Relational entities, bounding boxes, numeric predictions, schedules.
- **Object Storage (Supabase Storage):**
  - `sketches/original/`
  - `sketches/preprocessed/`
  - `renderings/photorealistic/`
  - `masks/detection/`
