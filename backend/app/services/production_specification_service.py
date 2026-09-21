"""
Production Specification Service
Handles business logic, render ownership validation, versioning,
transactional persistence, artisan updates/overrides, approval, and retrieval of Production Specifications.
"""

import base64
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set, Tuple
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
from app.schemas.production_specification import (
    ProductionSpecificationGenerateRequest,
    ProductionSpecificationResponse,
    ProductionSpecificationUpdateRequest,
    ProductionMaterialResponse,
    ProductionGemstoneResponse,
    ProductionStepResponse,
)
from app.services.gemini_production_service import (
    get_gemini_production_service,
    map_ai_response_to_production_specification,
)

logger = logging.getLogger("jewelmind.production_specification_service")

PROVENANCE_MARKER = "\n\n<!-- PROVENANCE_METADATA:"


def extract_provenance_meta(notes: Optional[str]) -> Tuple[Optional[str], Set[str]]:
    """Extracts human readable notes and set of artisan-overridden item IDs."""
    if not notes or PROVENANCE_MARKER not in notes:
        return notes, set()
    clean_notes, meta_part = notes.split(PROVENANCE_MARKER, 1)
    try:
        raw_json = meta_part.split("-->", 1)[0].strip()
        data = json.loads(raw_json)
        return clean_notes.strip(), set(data.get("overridden_ids", []))
    except Exception:
        return clean_notes.strip(), set()


def inject_provenance_meta(clean_notes: Optional[str], overridden_ids: Set[str]) -> Optional[str]:
    """Injects structured override provenance into notes storage."""
    text = (clean_notes or "").strip()
    if not overridden_ids:
        return text if text else None
    meta_json = json.dumps({"overridden_ids": sorted(list(overridden_ids))})
    return f"{text}{PROVENANCE_MARKER} {meta_json} -->"


class ProductionSpecificationService:
    """
    Service coordinating generation, database transactions, versioning,
    artisan reviews, approval, and multi-tenant access control for Production Specifications.
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

    async def update_specification(
        self,
        db: Session,
        user_id: uuid.UUID,
        specification_id: uuid.UUID,
        req: ProductionSpecificationUpdateRequest,
    ) -> ProductionSpecification:
        """
        Applies artisan review edits and manual overrides to a DRAFT specification.
        Strictly enforces multi-tenant ownership, immutability of APPROVED specifications,
        provenance tracking, and child record reconciliation within an atomic transaction.
        """
        # 1. Load specification and verify ownership
        spec = await self.get_specification_by_id(db, user_id, specification_id)

        # 2. Immutability check: approved specifications cannot be modified via PATCH
        if spec.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Approved production specifications are immutable and cannot be modified.",
            )

        # 3. Extract existing provenance overrides
        clean_notes, overridden_ids = extract_provenance_meta(spec.fabrication_notes)

        # 4. Update parent scalar fields
        if req.category is not None:
            spec.category = req.category
        if req.estimated_rough_metal_weight_grams is not None:
            spec.estimated_rough_metal_weight_grams = req.estimated_rough_metal_weight_grams
            overridden_ids.add("estimated_rough_metal_weight_grams")
        if req.estimated_finished_metal_weight_grams is not None:
            spec.estimated_finished_metal_weight_grams = req.estimated_finished_metal_weight_grams
            overridden_ids.add("estimated_finished_metal_weight_grams")
        if req.total_gemstone_count is not None:
            spec.total_gemstone_count = req.total_gemstone_count
            overridden_ids.add("total_gemstone_count")
        if req.estimated_total_bench_hours is not None:
            spec.estimated_total_bench_hours = req.estimated_total_bench_hours
            overridden_ids.add("estimated_total_bench_hours")
        if req.complexity_rating is not None:
            clean_comp = req.complexity_rating.strip().lower()
            if clean_comp not in ("simple", "moderate", "intricate", "masterpiece"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid complexity rating '{req.complexity_rating}'. Allowed: simple, moderate, intricate, masterpiece.",
                )
            spec.complexity_rating = clean_comp
            overridden_ids.add("complexity_rating")
        if req.fabrication_notes is not None:
            clean_notes = req.fabrication_notes.strip()
            overridden_ids.add("fabrication_notes")

        # 5. Reconcile Materials Collection
        if req.materials is not None:
            existing_mats = {m.id: m for m in spec.materials}
            retained_mat_ids = {m_in.id for m_in in req.materials if m_in.id and m_in.id in existing_mats}

            # Remove omitted materials first
            for mid, m in list(existing_mats.items()):
                if mid not in retained_mat_ids:
                    spec.materials.remove(m)
                    db.delete(m)
            db.flush()

            for mat_in in req.materials:
                if mat_in.id and mat_in.id in existing_mats:
                    # Update existing material
                    m = existing_mats[mat_in.id]
                    m.metal_type = mat_in.metal_type
                    m.metal_purity = mat_in.metal_purity
                    m.metal_color = mat_in.metal_color
                    m.metal_finish = mat_in.metal_finish
                    m.plating = mat_in.plating
                    m.estimated_weight_grams = mat_in.estimated_weight_grams
                    m.casting_loss_percentage = mat_in.casting_loss_percentage
                    overridden_ids.add(str(m.id))
                else:
                    # New material added by artisan
                    new_mat = ProductionMaterial(
                        id=uuid.uuid4(),
                        specification_id=spec.id,
                        metal_type=mat_in.metal_type,
                        metal_purity=mat_in.metal_purity,
                        metal_color=mat_in.metal_color,
                        metal_finish=mat_in.metal_finish,
                        plating=mat_in.plating,
                        estimated_weight_grams=mat_in.estimated_weight_grams,
                        casting_loss_percentage=mat_in.casting_loss_percentage,
                    )
                    spec.materials.append(new_mat)
                    overridden_ids.add(str(new_mat.id))
            db.flush()

        # 6. Reconcile Gemstones Collection
        if req.gemstones is not None:
            existing_gems = {g.id: g for g in spec.gemstones}
            retained_gem_ids = {g_in.id for g_in in req.gemstones if g_in.id and g_in.id in existing_gems}

            # Remove omitted gemstones first
            for gid, g in list(existing_gems.items()):
                if gid not in retained_gem_ids:
                    spec.gemstones.remove(g)
                    db.delete(g)
            db.flush()

            for gem_in in req.gemstones:
                if gem_in.id and gem_in.id in existing_gems:
                    # Update existing gemstone
                    g = existing_gems[gem_in.id]
                    g.gemstone_type = gem_in.gemstone_type
                    g.cut_shape = gem_in.cut_shape
                    g.stone_count = gem_in.stone_count
                    g.estimated_carat_weight = gem_in.estimated_carat_weight
                    g.approximate_dimensions_mm = gem_in.approximate_dimensions_mm
                    g.setting_type = gem_in.setting_type
                    g.is_center_stone = gem_in.is_center_stone
                    overridden_ids.add(str(g.id))
                else:
                    # New gemstone added by artisan
                    new_gem = ProductionGemstone(
                        id=uuid.uuid4(),
                        specification_id=spec.id,
                        gemstone_type=gem_in.gemstone_type,
                        cut_shape=gem_in.cut_shape,
                        stone_count=gem_in.stone_count,
                        estimated_carat_weight=gem_in.estimated_carat_weight,
                        approximate_dimensions_mm=gem_in.approximate_dimensions_mm,
                        setting_type=gem_in.setting_type,
                        is_center_stone=gem_in.is_center_stone,
                    )
                    spec.gemstones.append(new_gem)
                    overridden_ids.add(str(new_gem.id))
            db.flush()

            # Auto-update total gem count if not explicitly supplied
            if req.total_gemstone_count is None:
                spec.total_gemstone_count = sum(g.stone_count for g in spec.gemstones)

        # 7. Reconcile Production Steps Collection
        if req.steps is not None:
            existing_steps = {s.id: s for s in spec.steps}
            retained_step_ids = {s_in.id for s_in in req.steps if s_in.id and s_in.id in existing_steps}

            # First: remove omitted steps and flush to free up their step numbers
            for sid, s in list(existing_steps.items()):
                if sid not in retained_step_ids:
                    spec.steps.remove(s)
                    db.delete(s)
            db.flush()

            # Second: temporarily offset remaining existing steps to avoid unique constraint collision
            for idx, s in enumerate(spec.steps):
                s.step_number = 10000 + idx
            db.flush()

            # Third: apply updates and insert new steps
            for step_in in req.steps:
                if step_in.id and step_in.id in existing_steps:
                    s = existing_steps[step_in.id]
                    s.step_number = step_in.step_number
                    s.stage_name = step_in.stage_name
                    s.required_skill = step_in.required_skill
                    s.required_machine_type = step_in.required_machine_type
                    s.base_hours = step_in.base_hours
                    s.per_unit_hours = step_in.per_unit_hours
                    s.description = step_in.description
                    s.quality_checkpoint = step_in.quality_checkpoint
                    overridden_ids.add(str(s.id))
                else:
                    new_step = ProductionStep(
                        id=uuid.uuid4(),
                        specification_id=spec.id,
                        step_number=step_in.step_number,
                        stage_name=step_in.stage_name,
                        required_skill=step_in.required_skill,
                        required_machine_type=step_in.required_machine_type,
                        base_hours=step_in.base_hours,
                        per_unit_hours=step_in.per_unit_hours,
                        description=step_in.description,
                        quality_checkpoint=step_in.quality_checkpoint,
                    )
                    spec.steps.append(new_step)
                    overridden_ids.add(str(new_step.id))
            db.flush()

            # Auto-update total bench hours if not explicitly supplied
            if req.estimated_total_bench_hours is None:
                spec.estimated_total_bench_hours = round(
                    sum(s.base_hours + s.per_unit_hours for s in spec.steps), 2
                )

        # 8. Save updated provenance metadata into fabrication notes
        spec.fabrication_notes = inject_provenance_meta(clean_notes, overridden_ids)

        # 9. Atomic Transaction Commit
        try:
            db.commit()
            db.refresh(spec)
        except Exception as err:
            db.rollback()
            logger.error("Failed to persist specification update: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while saving specification changes.",
            ) from err

        return await self.get_specification_by_id(db, user_id, spec.id)

    async def approve_specification(
        self,
        db: Session,
        user_id: uuid.UUID,
        specification_id: uuid.UUID,
    ) -> ProductionSpecification:
        """
        Validates and approves a DRAFT specification, transitioning it to immutable APPROVED status.
        Performs thorough manufacturing readiness validation.
        """
        # 1. Load specification and enforce ownership
        spec = await self.get_specification_by_id(db, user_id, specification_id)

        # 2. Check current status eligibility
        if spec.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Specification is already approved.",
            )
        if spec.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve specification with status '{spec.status}'.",
            )

        # 3. Manufacturing Completeness Validation
        # Category validation
        if not spec.category or not spec.category.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval failed: Specification must have a valid jewellery category.",
            )

        # Material BOM validation
        if not spec.materials or len(spec.materials) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval failed: At least one material BOM item is required before approval.",
            )
        for m in spec.materials:
            if not m.metal_type or not m.metal_purity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Approval failed: Material must specify metal type and purity grade.",
                )
            if m.estimated_weight_grams is not None and m.estimated_weight_grams < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Approval failed: Material weight cannot be negative.",
                )

        # Gemstone BOM validation (optional if design has no gems, but must be valid if present)
        for g in spec.gemstones:
            if g.stone_count < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Approval failed: Gemstone stone count cannot be negative.",
                )
            if g.estimated_carat_weight is not None and g.estimated_carat_weight < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Approval failed: Gemstone carat weight cannot be negative.",
                )

        # Routing Steps validation
        if not spec.steps or len(spec.steps) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval failed: At least one manufacturing routing stage is required before approval.",
            )

        step_nums = [s.step_number for s in spec.steps]
        # Verify positive and non-duplicate
        if any(n <= 0 for n in step_nums) or len(step_nums) != len(set(step_nums)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval failed: Production step numbers must be positive and unique.",
            )
        # Verify sequential 1..N
        if sorted(step_nums) != list(range(1, len(step_nums) + 1)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval failed: Production steps must have sequential step numbers without gaps.",
            )

        for s in spec.steps:
            if not s.stage_name or not s.required_skill:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Approval failed: Step #{s.step_number} must specify a stage name and required skill.",
                )
            if s.base_hours < 0 or s.per_unit_hours < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Approval failed: Step #{s.step_number} duration hours cannot be negative.",
                )

        # Complexity validation
        if spec.complexity_rating and spec.complexity_rating not in ("simple", "moderate", "intricate", "masterpiece"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval failed: Invalid complexity rating '{spec.complexity_rating}'.",
            )

        # 4. Apply Approval State Transition
        spec.status = "approved"
        spec.approved_at = datetime.now(timezone.utc)

        # 5. Atomic Transaction Commit
        try:
            db.commit()
            db.refresh(spec)
        except Exception as err:
            db.rollback()
            logger.error("Failed to commit specification approval: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while approving specification.",
            ) from err

        return await self.get_specification_by_id(db, user_id, spec.id)


production_specification_service = ProductionSpecificationService()


def serialize_specification_response(spec: ProductionSpecification) -> ProductionSpecificationResponse:
    """
    Serializes a ProductionSpecification ORM model into a strongly typed response,
    resolving artisan override provenance for materials, gemstones, and routing steps.
    """
    clean_notes, overridden_ids = extract_provenance_meta(spec.fabrication_notes)

    materials_res = []
    for m in spec.materials:
        origin = "ARTISAN_OVERRIDE" if str(m.id) in overridden_ids else "AI_ESTIMATE"
        materials_res.append(
            ProductionMaterialResponse(
                id=m.id,
                specification_id=m.specification_id,
                metal_type=m.metal_type,
                metal_purity=m.metal_purity,
                metal_color=m.metal_color,
                metal_finish=m.metal_finish,
                plating=m.plating,
                estimated_weight_grams=m.estimated_weight_grams,
                casting_loss_percentage=m.casting_loss_percentage,
                origin=origin,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
        )

    gemstones_res = []
    for g in spec.gemstones:
        origin = "ARTISAN_OVERRIDE" if str(g.id) in overridden_ids else "AI_ESTIMATE"
        gemstones_res.append(
            ProductionGemstoneResponse(
                id=g.id,
                specification_id=g.specification_id,
                gemstone_type=g.gemstone_type,
                cut_shape=g.cut_shape,
                stone_count=g.stone_count,
                estimated_carat_weight=g.estimated_carat_weight,
                approximate_dimensions_mm=g.approximate_dimensions_mm,
                setting_type=g.setting_type,
                is_center_stone=g.is_center_stone,
                origin=origin,
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
        )

    steps_res = []
    for s in spec.steps:
        origin = "ARTISAN_OVERRIDE" if str(s.id) in overridden_ids else "AI_ESTIMATE"
        steps_res.append(
            ProductionStepResponse(
                id=s.id,
                specification_id=s.specification_id,
                step_number=s.step_number,
                stage_name=s.stage_name,
                required_skill=s.required_skill,
                required_machine_type=s.required_machine_type,
                base_hours=s.base_hours,
                per_unit_hours=s.per_unit_hours,
                description=s.description,
                quality_checkpoint=s.quality_checkpoint,
                origin=origin,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )

    return ProductionSpecificationResponse(
        id=spec.id,
        user_id=spec.user_id,
        design_id=spec.design_id,
        render_id=spec.render_id,
        version_number=spec.version_number,
        status=spec.status,
        category=spec.category,
        estimated_rough_metal_weight_grams=spec.estimated_rough_metal_weight_grams,
        estimated_finished_metal_weight_grams=spec.estimated_finished_metal_weight_grams,
        total_gemstone_count=spec.total_gemstone_count,
        estimated_total_bench_hours=spec.estimated_total_bench_hours,
        complexity_rating=spec.complexity_rating,
        fabrication_notes=clean_notes,
        ai_confidence_score=spec.ai_confidence_score,
        approved_at=spec.approved_at,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
        materials=materials_res,
        gemstones=gemstones_res,
        steps=steps_res,
    )
