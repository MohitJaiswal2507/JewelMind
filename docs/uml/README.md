# UML & Architectural Models Specification

> **Document Version:** 1.3.0 (Phase 3 Design Management)  
> **Status:** Architectural Models & Design Management Specification  

---

## 1. Class Diagram (Phase 3 Core Domain)

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String hashed_password
        +String full_name
        +Boolean is_active
        +String role
        +DateTime created_at
        +DateTime updated_at
        +List~Design~ designs
    }

    class Design {
        +UUID id
        +UUID user_id
        +String name
        +String description
        +String category
        +String status
        +String sketch_image_url
        +String rendered_image_url
        +String ai_prompt
        +DateTime created_at
        +DateTime updated_at
        +User user
    }

    class DesignCategory {
        <<enumeration>>
        RING
        NECKLACE
        EARRINGS
        BRACELET
        BANGLE
        PENDANT
        OTHER
    }

    class DesignStatus {
        <<enumeration>>
        DRAFT
        READY
        RENDERING
        RENDERED
        ARCHIVED
    }

    User "1" --> "0..*" Design : owns (cascade delete)
    Design ..> DesignCategory : categorizes
    Design ..> DesignStatus : tracks lifecycle
```

---

## 2. Use Case Diagram (Jewellery Design Management)

```mermaid
flowchart TD
    subgraph Authenticated User / Artisan
        U((Jewellery Artisan))
    end

    subgraph JewelMind Design Module
        UC1[Create Jewellery Design]
        UC2[View Design Portfolio & Grid]
        UC3[Filter by Category & Status]
        UC4[Search Designs by Keyword]
        UC5[View Detailed Design Blueprint]
        UC6[Update Design Metadata & Prompt]
        UC7[Delete Design with Confirmation]
    end

    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    U --> UC7
```

---

## 3. Sequence Diagram (Design Creation & Ownership Verification)

```mermaid
sequenceDiagram
    autonumber
    actor Artisan as Authenticated User
    participant UI as React Frontend (DesignsPage)
    participant Client as Axios/Fetch Client (designService)
    participant API as FastAPI Router (/api/v1/designs)
    participant Guard as Auth Guard (get_current_active_user)
    participant Service as DesignService
    participant DB as PostgreSQL (designs table)

    Artisan->>UI: Fill design details (Name, Category, Notes) & Submit
    UI->>Client: createDesign(payload)
    Client->>API: POST /api/v1/designs (Bearer Token + JSON Payload)
    API->>Guard: Verify JWT token & extract active user
    Guard-->>API: User (id, email)
    API->>Service: create_user_design(user_id, DesignCreate)
    Service->>DB: INSERT INTO designs (id, user_id, name, category, status, ...)
    DB-->>Service: Committed Design Row
    Service-->>API: Design ORM Instance
    API-->>Client: 201 Created (DesignResponse)
    Client-->>UI: Deserialized Design Object
    UI-->>Artisan: Display new design card in workspace grid
```

---

## 4. Sequence Diagram (Multi-Tenant Unauthorized Access Prevention)

```mermaid
sequenceDiagram
    autonumber
    actor Attacker as User B (Different User)
    participant API as FastAPI Router (/api/v1/designs/{id})
    participant Guard as Auth Guard
    participant Service as DesignService
    participant DB as PostgreSQL (designs table)

    Attacker->>API: GET /api/v1/designs/{Design_A_UUID} (Bearer Token B)
    API->>Guard: Verify JWT token for User B
    Guard-->>API: User B Object
    API->>Service: get_user_design_by_id(user_id=User_B, design_id=Design_A)
    Service->>DB: SELECT * FROM designs WHERE id = Design_A AND user_id = User_B
    DB-->>Service: Empty (No matching row)
    Service-->>API: Raise AppException(404, "DESIGN_NOT_FOUND")
    API-->>Attacker: 404 Not Found (Zero information leaked)
```
