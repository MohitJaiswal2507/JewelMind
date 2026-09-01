"""
Design Service & Database Operations
"""

import math
import uuid
from typing import Optional, Tuple, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.core.exceptions import AppException
from app.models.design import Design
from app.schemas.design import DesignCreate, DesignUpdate, DesignCategory, DesignStatus


class DesignService:
    @staticmethod
    def get_user_designs(
        db: Session,
        user_id: Union[str, uuid.UUID],
        category: Optional[Union[str, DesignCategory]] = None,
        status: Optional[Union[str, DesignStatus]] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Design], int, int]:
        """
        Retrieves a paginated list of designs belonging strictly to the authenticated user.
        Supports category, status, and substring search filtering.
        Returns: (items, total_count, total_pages)
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return ([], 0, 0)

        # Base query filtered strictly by user_id
        stmt = select(Design).where(Design.user_id == user_id)
        count_stmt = select(func.count(Design.id)).where(Design.user_id == user_id)

        if category:
            cat_val = category.value if isinstance(category, DesignCategory) else category
            stmt = stmt.where(Design.category == cat_val)
            count_stmt = count_stmt.where(Design.category == cat_val)

        if status:
            stat_val = status.value if isinstance(status, DesignStatus) else status
            stmt = stmt.where(Design.status == stat_val)
            count_stmt = count_stmt.where(Design.status == stat_val)

        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            search_clause = or_(
                Design.name.ilike(search_pattern),
                Design.description.ilike(search_pattern),
            )
            stmt = stmt.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        total_count = db.scalar(count_stmt) or 0
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        # Pagination & ordering (newest first)
        skip = (page - 1) * page_size
        stmt = stmt.order_by(Design.created_at.desc()).offset(skip).limit(page_size)
        items = list(db.scalars(stmt).all())

        return items, total_count, total_pages

    @staticmethod
    def get_user_design_by_id(
        db: Session,
        user_id: Union[str, uuid.UUID],
        design_id: Union[str, uuid.UUID],
    ) -> Design:
        """
        Retrieves a single design by ID ensuring strict user ownership.
        Raises 404 DESIGN_NOT_FOUND if design does not exist or belongs to another user.
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                raise AppException(
                    message="Design not found.",
                    code="DESIGN_NOT_FOUND",
                    status_code=404,
                )

        if isinstance(design_id, str):
            try:
                design_id = uuid.UUID(design_id)
            except ValueError:
                raise AppException(
                    message="Design not found.",
                    code="DESIGN_NOT_FOUND",
                    status_code=404,
                )

        stmt = select(Design).where(Design.id == design_id, Design.user_id == user_id)
        design = db.scalars(stmt).first()

        if not design:
            raise AppException(
                message="Design not found.",
                code="DESIGN_NOT_FOUND",
                status_code=404,
            )

        return design

    @staticmethod
    def create_user_design(
        db: Session,
        user_id: Union[str, uuid.UUID],
        obj_in: DesignCreate,
    ) -> Design:
        """
        Creates a new jewellery design under the authenticated user's workspace.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        db_design = Design(
            user_id=user_id,
            name=obj_in.name,
            description=obj_in.description,
            category=obj_in.category.value if isinstance(obj_in.category, DesignCategory) else obj_in.category,
            status=obj_in.status.value if isinstance(obj_in.status, DesignStatus) else obj_in.status,
            sketch_image_url=obj_in.sketch_image_url,
            rendered_image_url=obj_in.rendered_image_url,
            ai_prompt=obj_in.ai_prompt,
        )
        db.add(db_design)
        db.commit()
        db.refresh(db_design)
        return db_design

    @staticmethod
    def update_user_design(
        db: Session,
        user_id: Union[str, uuid.UUID],
        design_id: Union[str, uuid.UUID],
        obj_in: DesignUpdate,
    ) -> Design:
        """
        Updates an existing design owned by the authenticated user.
        Raises 404 if design does not exist or user is unauthorized.
        """
        design = DesignService.get_user_design_by_id(db, user_id=user_id, design_id=design_id)

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if isinstance(value, (DesignCategory, DesignStatus)):
                    setattr(design, field, value.value)
                else:
                    setattr(design, field, value)

        db.add(design)
        db.commit()
        db.refresh(design)
        return design

    @staticmethod
    def delete_user_design(
        db: Session,
        user_id: Union[str, uuid.UUID],
        design_id: Union[str, uuid.UUID],
    ) -> None:
        """
        Deletes a design owned by the authenticated user.
        Raises 404 if design does not exist or user is unauthorized.
        """
        design = DesignService.get_user_design_by_id(db, user_id=user_id, design_id=design_id)
        db.delete(design)
        db.commit()


design_service = DesignService()
