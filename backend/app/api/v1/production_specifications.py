"""
Production Specification Management API Router
Provides authenticated endpoints for generating, inspecting, and tracking
versioned manufacturing blueprints (Production Specifications).
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.production_specification import (
    ProductionSpecificationGenerateRequest,
    ProductionSpecificationResponse,
    ProductionSpecificationUpdateRequest,
)
from app.services.production_specification_service import (
    production_specification_service,
    serialize_specification_response,
)

router = APIRouter(prefix="/production-specifications", tags=["Production Specifications"])


@router.post(
    "/generate",
    response_model=ProductionSpecificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a production specification from an approved render",
    description=(
        "Analyzes an approved jewellery render and its associated structured design parameters "
        "using AI manufacturing intelligence, formats the Bill of Materials (BOM) and workshop routing, "
        "and atomically persists a new immutable version of the Production Specification."
    ),
)
async def generate_production_specification(
    request_in: ProductionSpecificationGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates and persists a new Production Specification.
    Strictly verifies render and design ownership before invoking manufacturing intelligence.
    """
    spec = await production_specification_service.generate_specification(
        db=db,
        user_id=current_user.id,
        req=request_in,
    )
    return serialize_specification_response(spec)


@router.get(
    "/{specification_id}",
    response_model=ProductionSpecificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single production specification details",
    description="Retrieves a full production specification including materials BOM, gemstones, and sequential routing.",
)
async def get_production_specification(
    specification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves specification by ID. Enforces strict multi-tenant ownership.
    """
    spec = await production_specification_service.get_specification_by_id(
        db=db,
        user_id=current_user.id,
        specification_id=specification_id,
    )
    return serialize_specification_response(spec)


@router.patch(
    "/{specification_id}",
    response_model=ProductionSpecificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Artisan edit/override a draft production specification",
    description=(
        "Allows an authenticated artisan to modify BOM line items, gemstone quantities, "
        "routing stages, and specification metadata. Overridden items are marked with provenance. "
        "Approved specifications are immutable and will be rejected with 409 Conflict."
    ),
)
async def update_production_specification(
    specification_id: uuid.UUID,
    request_in: ProductionSpecificationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates a draft production specification with artisan review overrides.
    """
    spec = await production_specification_service.update_specification(
        db=db,
        user_id=current_user.id,
        specification_id=specification_id,
        req=request_in,
    )
    return serialize_specification_response(spec)


@router.post(
    "/{specification_id}/approve",
    response_model=ProductionSpecificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a production specification for manufacturing",
    description=(
        "Transitions a draft production specification to APPROVED status after validating "
        "manufacturing readiness. Once approved, the specification is immutable."
    ),
)
async def approve_production_specification(
    specification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Validates and locks the production specification as APPROVED.
    """
    spec = await production_specification_service.approve_specification(
        db=db,
        user_id=current_user.id,
        specification_id=specification_id,
    )
    return serialize_specification_response(spec)


@router.get(
    "/by-render/{render_id}",
    response_model=List[ProductionSpecificationResponse],
    status_code=status.HTTP_200_OK,
    summary="List specifications associated with a specific render version",
    description="Returns the specification history generated from this render, ordered newest version first.",
)
async def get_specifications_by_render(
    render_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves all specification versions bound to a given render.
    Enforces render ownership before returning records.
    """
    specs = await production_specification_service.get_specifications_by_render(
        db=db,
        user_id=current_user.id,
        render_id=render_id,
    )
    return [serialize_specification_response(s) for s in specs]

