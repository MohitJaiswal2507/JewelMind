"""
Production Specification Service
Handles business logic, render ownership validation, versioning,
transactional persistence, and retrieval of Production Specifications.
"""

import base64
import logging
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.design import Design, DesignRender
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.schemas.production_intelligence import ProductionIntelligenceInput
from app.schemas.production_specification import ProductionSpecificationGenerateRequest
from app.services.gemini_production_service import (
    get_gemini_production_service,
    map_ai_response_to_production_specification,
)

logger = logging.getLogger("jewelmind.production_specification_service")


class ProductionSpecificationService:
    """
    Service coordinating generation, database transactions, versioning,
    and multi-tenant access control for Production Specifications.
    """

    async def generate_specification(
        self,
        db: Session,
        user_id: uuid.UUID,
        req: ProductionSpecificationGenerateRequest,
    ) -> ProductionSpecification:
        """
        Generates and atomically persists a new ProductionSpecification version from an approved render.
        Strictly enforces multi-tenant ownership, render integrity, and rollback on failure.
        """
        # 1. Load and verify DesignRender ownership (IDOR-safe: return 404)
        render = (
            db.query(DesignRender)
            .filter(DesignRender.id == req.render_id)
            .first()
        )
        if not render or render.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render version not found or access denied.",
            )

        # 2. Load and verify parent Design ownership
        design = (
            db.query(Design)
            .filter(Design.id == render.design_id)
            .first()
        )
        if not design or design.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated jewellery design not found or access denied.",
            )

        # 3. Verify render/design relational integrity
        if render.design_id != design.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inconsistent render and design association detected.",
            )

        # 4. Ensure render has a valid visual asset
        if not render.image_url or not render.image_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The specified render does not have an accessible image URL.",
            )

        # 5. Extract visual payload (base64 or remote URL)
        image_bytes: Optional[bytes] = None
        image_base64: Optional[str] = None
        image_mime_type = "image/png"

        if render.image_url.startswith("data:"):
            try:
                header, b64_part = render.image_url.split(",", 1)
                image_base64 = b64_part
                image_bytes = base64.b64decode(b64_part)
                if "jpeg" in header or "jpg" in header:
                    image_mime_type = "image/jpeg"
                elif "webp" in header:
                    image_mime_type = "image/webp"
            except Exception as exc:
                logger.warning("Failed to decode data URI image: %s", exc)

        # 6. Build ProductionIntelligenceInput for Phase I.2 AI Service
        user_prompt_effective = req.user_prompt or render.prompt or design.ai_prompt
        intelligence_input = ProductionIntelligenceInput(
            design_id=design.id,
            render_id=render.id,
            category=design.category,
            image_url=render.image_url,
            image_bytes=image_bytes,
            image_base64=image_base64,
            image_mime_type=image_mime_type,
            structured_state=render.structured_state,
            user_prompt=user_prompt_effective,
            enhanced_prompt=render.enhanced_prompt,
            material_hint=req.material_hint,
            gemstone_hint=req.gemstone_hint,
        )

        # 7. Execute AI Manufacturing Intelligence Analysis
        ai_service = get_gemini_production_service()
        try:
            ai_response = await ai_service.analyze_production(intelligence_input)
        except Exception as ai_err:
            logger.error("Production intelligence reasoning failed: %s", ai_err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to formulate manufacturing specification from render.",
            ) from ai_err

        # 8. Compute monotonic version_number safely within transaction
        try:
            current_max_v = (
                db.query(func.coalesce(func.max(ProductionSpecification.version_number), 0))
                .filter(
                    ProductionSpecification.user_id == user_id,
                    ProductionSpecification.design_id == design.id,
                )
                .scalar()
            )
            next_version = int(current_max_v) + 1

            # 9. Map AI response to Phase I.1 ORM models (status='draft')
            spec = map_ai_response_to_production_specification(
                ai_response=ai_response,
                user_id=user_id,
                design_id=design.id,
                render_id=render.id,
                version_number=next_version,
                status="draft",
            )

            # 10. Persist parent specification and all children in a single transaction
            db.add(spec)
            db.commit()
            db.refresh(spec)

        except IntegrityError as ie:
            db.rollback()
            logger.error("Database integrity error during specification persistence: %s", ie)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Specification version conflict. Please retry generation.",
            ) from ie
        except Exception as db_err:
            db.rollback()
            logger.error("Database transaction error during specification persistence: %s", db_err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while persisting production specification.",
            ) from db_err

        # 11. Return eagerly loaded specification
        return await self.get_specification_by_id(db, user_id, spec.id)

    async def get_specification_by_id(
        self,
        db: Session,
        user_id: uuid.UUID,
        specification_id: uuid.UUID,
    ) -> ProductionSpecification:
        """
        Retrieves a single ProductionSpecification by ID.
        Enforces user ownership and eagerly loads all child BOM and routing items.
        """
        spec = (
            db.query(ProductionSpecification)
            .options(
                selectinload(ProductionSpecification.materials),
                selectinload(ProductionSpecification.gemstones),
                selectinload(ProductionSpecification.steps),
            )
            .filter(
                ProductionSpecification.id == specification_id,
                ProductionSpecification.user_id == user_id,
            )
            .first()
        )
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Production specification not found or access denied.",
            )
        return spec

    async def get_specifications_by_render(
        self,
        db: Session,
        user_id: uuid.UUID,
        render_id: uuid.UUID,
    ) -> List[ProductionSpecification]:
        """
        Retrieves the specification history associated with a specific render version.
        Enforces render ownership and returns specifications ordered by version_number desc.
        """
        # Verify render ownership first (IDOR-safe: return 404)
        render = (
            db.query(DesignRender)
            .filter(DesignRender.id == render_id)
            .first()
        )
        if not render or render.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render version not found or access denied.",
            )

        specs = (
            db.query(ProductionSpecification)
            .options(
                selectinload(ProductionSpecification.materials),
                selectinload(ProductionSpecification.gemstones),
                selectinload(ProductionSpecification.steps),
            )
            .filter(
                ProductionSpecification.render_id == render_id,
                ProductionSpecification.user_id == user_id,
            )
            .order_by(ProductionSpecification.version_number.desc())
            .all()
        )
        return specs


production_specification_service = ProductionSpecificationService()
