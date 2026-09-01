"""
Jewellery Design Management API Router
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.design import (
    DesignCategory,
    DesignCreate,
    DesignListResponse,
    DesignResponse,
    DesignStatus,
    DesignUpdate,
)
from app.services.design_service import design_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/designs", tags=["Designs"])


@router.post(
    "",
    response_model=DesignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new jewellery design",
)
async def create_design(
    design_in: DesignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates a new jewellery design record in the authenticated user's workspace.
    """
    design = design_service.create_user_design(
        db=db,
        user_id=current_user.id,
        obj_in=design_in,
    )
    return DesignResponse.model_validate(design)


@router.get(
    "",
    response_model=DesignListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all designs belonging to the authenticated user",
)
async def list_designs(
    category: Optional[DesignCategory] = Query(None, description="Filter designs by category"),
    status_filter: Optional[DesignStatus] = Query(None, alias="status", description="Filter designs by status"),
    search: Optional[str] = Query(None, description="Search keyword in design name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns a paginated list of designs belonging strictly to the authenticated user.
    Supports filtering by category, status, and text search.
    """
    items, total, pages = design_service.get_user_designs(
        db=db,
        user_id=current_user.id,
        category=category,
        status=status_filter,
        search=search,
        page=page,
        page_size=page_size,
    )
    return DesignListResponse(
        items=[DesignResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{design_id}",
    response_model=DesignResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single design details",
)
async def get_design(
    design_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fetches detailed design information. Fails with 404 if design does not exist
    or belongs to a different user.
    """
    design = design_service.get_user_design_by_id(
        db=db,
        user_id=current_user.id,
        design_id=design_id,
    )
    return DesignResponse.model_validate(design)


@router.patch(
    "/{design_id}",
    response_model=DesignResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a jewellery design",
)
async def update_design(
    design_id: uuid.UUID,
    design_in: DesignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates mutable attributes of a design. Fails with 404 if design is not found
    or owned by another user.
    """
    updated_design = design_service.update_user_design(
        db=db,
        user_id=current_user.id,
        design_id=design_id,
        obj_in=design_in,
    )
    return DesignResponse.model_validate(updated_design)


@router.delete(
    "/{design_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a jewellery design",
)
async def delete_design(
    design_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes a design permanently, including any associated sketch in Supabase Storage.
    Fails with 404 if design is not found or owned by another user.
    """
    design = design_service.get_user_design_by_id(
        db=db,
        user_id=current_user.id,
        design_id=design_id,
    )
    
    # Clean up storage asset if present
    if design.sketch_image_url:
        await storage_service.delete_sketch(design.sketch_image_url)

    design_service.delete_user_design(
        db=db,
        user_id=current_user.id,
        design_id=design_id,
    )
    return {
        "success": True,
        "message": "Jewellery design deleted successfully.",
        "design_id": str(design_id),
    }


# ==========================================
# Phase 4: Sketch Asset Management Endpoints
# ==========================================

@router.post(
    "/{design_id}/sketch",
    response_model=DesignResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload or replace jewellery sketch asset",
)
async def upload_design_sketch(
    design_id: uuid.UUID,
    file: UploadFile = File(..., description="Sketch image file (PNG, JPEG, WEBP <= 10MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Uploads a new sketch image or replaces an existing sketch for the given design.
    Enforces user authentication, ownership check, MIME validation, and size constraints.
    """
    # 1. Ownership & Design Check
    design = design_service.get_user_design_by_id(
        db=db,
        user_id=current_user.id,
        design_id=design_id,
    )

    # 2. Read and validate file content
    file_bytes = await file.read()

    # 3. Upload new sketch to Supabase Storage
    new_sketch_url, _ = await storage_service.upload_sketch(
        file_bytes=file_bytes,
        filename=file.filename or "sketch.png",
        content_type=file.content_type or "image/png",
        user_id=current_user.id,
        design_id=design_id,
    )

    # 4. Atomic Replacement: Update DB reference, then clean old storage asset
    old_sketch_url = design.sketch_image_url
    design.sketch_image_url = new_sketch_url
    db.add(design)
    db.commit()
    db.refresh(design)

    # 5. Clean up previous object if replaced
    if old_sketch_url and old_sketch_url != new_sketch_url:
        await storage_service.delete_sketch(old_sketch_url)

    return DesignResponse.model_validate(design)


@router.delete(
    "/{design_id}/sketch",
    response_model=DesignResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete sketch asset from design",
)
async def delete_design_sketch(
    design_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes the sketch image asset from Supabase Storage and clears the sketch_image_url field.
    Leaves the parent Design entity intact.
    """
    # 1. Ownership & Design Check
    design = design_service.get_user_design_by_id(
        db=db,
        user_id=current_user.id,
        design_id=design_id,
    )

    # 2. Delete from Supabase Storage
    if design.sketch_image_url:
        await storage_service.delete_sketch(design.sketch_image_url)
        design.sketch_image_url = None
        db.add(design)
        db.commit()
        db.refresh(design)

    return DesignResponse.model_validate(design)
