# JewelMind Development Guidelines

These guidelines define standard code style, architecture boundaries, Git conventions, and security rules for the JewelMind codebase.

---

## 1. Code Style & Naming Conventions

### Python (Backend & AI Modules)
- **Formatting:** PEP 8 compliance.
- **Variables & Functions:** `snake_case` (e.g. `generate_schedule`, `job_status`, `metal_weight_grams`).
- **Classes & Types:** `PascalCase` (e.g. `JewelleryDesign`, `AIJobWorker`, `CostEstimator`).
- **Constants:** `UPPER_SNAKE_CASE` (e.g. `DEFAULT_PRECISION_DECIMALS`, `MAX_IMAGE_UPLOAD_BYTES`).
- **Type Annotations:** Strictly use type hints (`from typing import Optional, List, Dict` or native Python 3.12+ types).

### TypeScript & React (Frontend)
- **Files & Components:** `PascalCase.tsx` for components (e.g. `DesignCard.tsx`, `JobStatusBadge.tsx`).
- **Functions & Variables:** `camelCase` (e.g. `fetchJobDetails`, `activeDesignId`).
- **Interfaces & Types:** `PascalCase` prefixed with descriptive domain nouns (e.g. `JewelleryItem`, `PredictionResult`).
- **Hooks:** Prefixed with `use` (e.g. `useAIJobStatus.ts`).

---

## 2. Architecture & Modularity Boundaries

1. **Decoupled Heavy Compute:** Never execute long-running AI inference or optimization inside synchronous HTTP request handlers. Always enqueue jobs.
2. **Deterministic Fallbacks:** Implement rule-based fallback estimates alongside ML prediction models to ensure operational resilience.
3. **No Hardcoded Secrets:** Pass all keys, tokens, and database connection strings via environment variables.
4. **Single Source of Truth for Schemas:** Align Pydantic schemas in the backend with TypeScript types in the frontend.

---

## 3. Git Workflow & Commit Conventions

Follow the **Conventional Commits** specification:

| Prefix | Usage | Example |
| :--- | :--- | :--- |
| `feat:` | New feature | `feat: add jewellery sketch upload endpoint` |
| `fix:` | Bug fix | `fix: resolve bounding box coordinate scaling` |
| `refactor:` | Code change that neither fixes a bug nor adds a feature | `refactor: extract feature calculation pipeline` |
| `docs:` | Documentation changes only | `docs: add phase 0 completion report` |
| `test:` | Adding or modifying tests | `test: add unit tests for /health endpoint` |
| `chore:` | Build process, auxiliary tools, or dependency updates | `chore: update tailwind config and dependencies` |

---

## 4. Security & Sensitive Data Policy

- Never commit `.env` files or hardcoded secrets (API keys, Supabase credentials, JWT secrets).
- Never commit large raw datasets ($>10$ MB) or binary model weights (`.pt`, `.pth`, `.safetensors`, `.onnx`, `.ckpt`).
- Always validate and sanitize user uploads (enforce file size limits and MIME type checking for image formats: JPEG, PNG, WEBP).
