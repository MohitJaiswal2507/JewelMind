"""
V1 API Master Router
Aggregates all versioned feature subrouters.
"""

from fastapi import APIRouter
from app.api.v1 import health, auth

api_v1_router = APIRouter()

# Register subrouters
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)

# Future phase routers will be registered here:
# api_v1_router.include_router(designs.router)     # Phase 3
# api_v1_router.include_router(sketches.router)    # Phase 4
# api_v1_router.include_router(ai.router)          # Phase 5
# api_v1_router.include_router(predictions.router) # Phase 9
# api_v1_router.include_router(production.router)  # Phase 11
# api_v1_router.include_router(optimization.router)# Phase 12
