"""
V1 API Master Router
Aggregates all versioned feature subrouters.
"""

from fastapi import APIRouter
from app.api.v1 import (
    ai_components,
    ai_gemini,
    ai_rendering,
    auth,
    dashboard,
    designs,
    health,
    production,
    production_specifications,
)

api_v1_router = APIRouter()

# Register subrouters
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(designs.router)
api_v1_router.include_router(ai_components.router)
api_v1_router.include_router(ai_rendering.router)
api_v1_router.include_router(ai_gemini.router)
api_v1_router.include_router(production.router)
api_v1_router.include_router(production_specifications.router)
api_v1_router.include_router(dashboard.router)


