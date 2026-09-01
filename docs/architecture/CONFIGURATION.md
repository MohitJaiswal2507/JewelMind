# Environment Configuration & Variables Specification

> **Document Version:** 1.0.0 (Phase 1 Foundation)  

---

## 1. Configuration Principles
- **Strict 12-Factor App Compliance:** All configuration is strictly driven by environment variables.
- **No Committed Secrets:** `.env` is ignored by Git; developers copy from `.env.example`.
- **Validation on Boot:** Settings are validated via `pydantic-settings` on startup.

---

## 2. Environment Variables Reference Matrix

| Variable | Type | Default | Required For | Description |
| :--- | :--- | :--- | :--- | :--- |
| `APP_ENV` | `str` | `development` | Core | Environment name (`development`, `testing`, `production`) |
| `DEBUG` | `bool` | `true` | Core | Enables debug logs and detailed error diagnostics |
| `LOG_LEVEL` | `str` | `INFO` | Logging | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `API_V1_STR` | `str` | `/api/v1` | Routing | Master version prefix for API routes |
| `CORS_ORIGINS` | `list[str]` | `http://localhost:5173` | Security | Allowed origins for browser CORS requests |
| `DATABASE_URL` | `str` | `postgresql://...` | Database | Connection string for PostgreSQL database |
| `DB_ECHO_LOG` | `bool` | `false` | Database | Prints raw SQL queries to stdout when enabled |
| `SUPABASE_URL` | `str` | `""` | Storage | Supabase project URL (Phases 3+) |
| `SUPABASE_ANON_KEY` | `str` | `""` | Storage | Supabase client public anon key (Phases 3+) |
| `SUPABASE_SERVICE_ROLE_KEY` | `str` | `""` | Storage | Supabase server-side admin key (Backend only) |
| `AI_WORKER_URL` | `str` | `http://localhost:8001` | AI Queue | Host address of local RTX 4060 GPU worker |
| `AI_WORKER_TOKEN` | `str` | `local-worker-token` | AI Queue | Auth token for worker job leasing |
| `VITE_API_URL` | `str` | `http://localhost:8000` | Frontend | Frontend environment base URL for API requests |

---

## 3. Frontend Variable Rules
- Only variables prefixed with `VITE_` are exposed in browser bundles.
- Never place database connection strings, JWT private keys, or service role keys in Vite environment variables.
