"""
Production Service & Business Operations
Provides database persistence and operations for Production Orders, Workers, Machines, and Summary Metrics.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.design import Design
from app.models.production import Machine, ProductionOrder, Worker
from app.schemas.production import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
    OrderPriority,
    OrderStatus,
    ProductionOrderCreate,
    ProductionOrderResponse,
    ProductionOrderUpdate,
    ProductionSummaryResponse,
    WorkerCreate,
    WorkerResponse,
    WorkerUpdate,
)


class ProductionService:
    # -----------------------------------------------------------------------
    # Production Orders Operations
    # -----------------------------------------------------------------------

    @staticmethod
    def _to_order_response(order: ProductionOrder) -> ProductionOrderResponse:
        now_utc = datetime.now(timezone.utc)
        deadline_tz = order.deadline if order.deadline.tzinfo else order.deadline.replace(tzinfo=timezone.utc)
        is_overdue = deadline_tz < now_utc and order.status not in (OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value)

        return ProductionOrderResponse(
            id=order.id,
            user_id=order.user_id,
            design_id=order.design_id,
            quantity=order.quantity,
            priority=OrderPriority(order.priority),
            status=OrderStatus(order.status),
            deadline=order.deadline,
            notes=order.notes,
            is_overdue=is_overdue,
            design_name=order.design.name if order.design else None,
            design_category=order.design.category if order.design else None,
            design_thumbnail_url=order.design.sketch_image_url or order.design.rendered_image_url if order.design else None,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    @staticmethod
    def get_user_orders(
        db: Session,
        user_id: Union[str, uuid.UUID],
        status: Optional[Union[str, OrderStatus]] = None,
        priority: Optional[Union[str, OrderPriority]] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ProductionOrderResponse], int, int]:
        """
        Retrieves paginated production orders belonging strictly to the authenticated user.
        Supports status, priority, and design name search filters.
        Returns: (items, total_count, total_pages)
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return ([], 0, 0)

        stmt = select(ProductionOrder).options(joinedload(ProductionOrder.design)).where(ProductionOrder.user_id == user_id)
        count_stmt = select(func.count(ProductionOrder.id)).where(ProductionOrder.user_id == user_id)

        if status:
            stat_val = status.value if isinstance(status, OrderStatus) else str(status).lower()
            stmt = stmt.where(ProductionOrder.status == stat_val)
            count_stmt = count_stmt.where(ProductionOrder.status == stat_val)

        if priority:
            prio_val = priority.value if isinstance(priority, OrderPriority) else str(priority).lower()
            stmt = stmt.where(ProductionOrder.priority == prio_val)
            count_stmt = count_stmt.where(ProductionOrder.priority == prio_val)

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            # Join design to allow searching by design name or notes
            stmt = stmt.join(ProductionOrder.design).where(
                or_(
                    Design.name.ilike(pattern),
                    ProductionOrder.notes.ilike(pattern),
                )
            )
            count_stmt = count_stmt.join(ProductionOrder.design).where(
                or_(
                    Design.name.ilike(pattern),
                    ProductionOrder.notes.ilike(pattern),
                )
            )

        total_count = db.scalar(count_stmt) or 0
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        skip = (page - 1) * page_size
        stmt = stmt.order_by(ProductionOrder.deadline.asc(), ProductionOrder.created_at.desc()).offset(skip).limit(page_size)
        db_orders = db.scalars(stmt).unique().all()

        items = [ProductionService._to_order_response(o) for o in db_orders]
        return items, total_count, total_pages

    @staticmethod
    def get_order_by_id(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> ProductionOrderResponse:
        """
        Retrieves a single production order by ID with ownership verification.
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        if isinstance(order_id, str):
            try:
                order_id = uuid.UUID(order_id)
            except ValueError:
                raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        stmt = (
            select(ProductionOrder)
            .options(joinedload(ProductionOrder.design))
            .where(ProductionOrder.id == order_id, ProductionOrder.user_id == user_id)
        )
        order = db.scalar(stmt)
        if not order:
            raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        return ProductionService._to_order_response(order)

    @staticmethod
    def create_order(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_in: ProductionOrderCreate,
    ) -> ProductionOrderResponse:
        """
        Creates a new production order linked to an existing, user-owned Design.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Validate design existence and ownership
        design_stmt = select(Design).where(Design.id == order_in.design_id, Design.user_id == user_id)
        design = db.scalar(design_stmt)
        if not design:
            raise AppException(
                "Associated jewellery design not found or not owned by user.",
                code="DESIGN_NOT_FOUND",
                status_code=404,
            )

        if order_in.quantity <= 0:
            raise AppException(
                "Order quantity must be greater than zero.",
                code="INVALID_QUANTITY",
                status_code=422,
            )

        order = ProductionOrder(
            user_id=user_id,
            design_id=order_in.design_id,
            quantity=order_in.quantity,
            priority=order_in.priority.value if isinstance(order_in.priority, OrderPriority) else str(order_in.priority),
            status=order_in.status.value if isinstance(order_in.status, OrderStatus) else str(order_in.status),
            deadline=order_in.deadline,
            notes=order_in.notes,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        # Load design relationship
        order.design = design
        return ProductionService._to_order_response(order)

    @staticmethod
    def update_order(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
        order_in: ProductionOrderUpdate,
    ) -> ProductionOrderResponse:
        """
        Updates an existing production order.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        stmt = (
            select(ProductionOrder)
            .options(joinedload(ProductionOrder.design))
            .where(ProductionOrder.id == order_id, ProductionOrder.user_id == user_id)
        )
        order = db.scalar(stmt)
        if not order:
            raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        if order_in.quantity is not None:
            if order_in.quantity <= 0:
                raise AppException("Quantity must be greater than zero.", code="INVALID_QUANTITY", status_code=422)
            order.quantity = order_in.quantity

        if order_in.priority is not None:
            order.priority = order_in.priority.value if isinstance(order_in.priority, OrderPriority) else str(order_in.priority)

        if order_in.status is not None:
            order.status = order_in.status.value if isinstance(order_in.status, OrderStatus) else str(order_in.status)

        if order_in.deadline is not None:
            order.deadline = order_in.deadline

        if order_in.notes is not None:
            order.notes = order_in.notes

        db.commit()
        db.refresh(order)
        return ProductionService._to_order_response(order)

    @staticmethod
    def delete_order(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> None:
        """
        Deletes a production order ensuring user ownership.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        stmt = select(ProductionOrder).where(ProductionOrder.id == order_id, ProductionOrder.user_id == user_id)
        order = db.scalar(stmt)
        if not order:
            raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        db.delete(order)
        db.commit()

    # -----------------------------------------------------------------------
    # Workers Operations
    # -----------------------------------------------------------------------

    @staticmethod
    def get_user_workers(
        db: Session,
        user_id: Union[str, uuid.UUID],
    ) -> List[WorkerResponse]:
        """
        Retrieves all workshop workers belonging to the user.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        stmt = select(Worker).where(Worker.user_id == user_id).order_by(Worker.name.asc())
        workers = db.scalars(stmt).all()
        return [WorkerResponse.model_validate(w) for w in workers]

    @staticmethod
    def get_worker_by_id(
        db: Session,
        user_id: Union[str, uuid.UUID],
        worker_id: Union[str, uuid.UUID],
    ) -> WorkerResponse:
        """
        Retrieves a single worker by ID with ownership verification.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(worker_id, str):
            worker_id = uuid.UUID(worker_id)

        stmt = select(Worker).where(Worker.id == worker_id, Worker.user_id == user_id)
        worker = db.scalar(stmt)
        if not worker:
            raise AppException("Worker not found.", code="WORKER_NOT_FOUND", status_code=404)

        return WorkerResponse.model_validate(worker)

    @staticmethod
    def create_worker(
        db: Session,
        user_id: Union[str, uuid.UUID],
        worker_in: WorkerCreate,
    ) -> WorkerResponse:
        """
        Creates a new workshop worker entity with skill and capacity.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        worker = Worker(
            user_id=user_id,
            name=worker_in.name,
            skill=worker_in.skill,
            capacity_hours_per_day=worker_in.capacity_hours_per_day,
            is_available=worker_in.is_available,
        )

        db.add(worker)
        db.commit()
        db.refresh(worker)
        return WorkerResponse.model_validate(worker)

    @staticmethod
    def update_worker(
        db: Session,
        user_id: Union[str, uuid.UUID],
        worker_id: Union[str, uuid.UUID],
        worker_in: WorkerUpdate,
    ) -> WorkerResponse:
        """
        Updates worker skill, availability, or capacity.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(worker_id, str):
            worker_id = uuid.UUID(worker_id)

        stmt = select(Worker).where(Worker.id == worker_id, Worker.user_id == user_id)
        worker = db.scalar(stmt)
        if not worker:
            raise AppException("Worker not found.", code="WORKER_NOT_FOUND", status_code=404)

        if worker_in.name is not None:
            worker.name = worker_in.name
        if worker_in.skill is not None:
            worker.skill = worker_in.skill
        if worker_in.capacity_hours_per_day is not None:
            worker.capacity_hours_per_day = worker_in.capacity_hours_per_day
        if worker_in.is_available is not None:
            worker.is_available = worker_in.is_available

        db.commit()
        db.refresh(worker)
        return WorkerResponse.model_validate(worker)

    @staticmethod
    def delete_worker(
        db: Session,
        user_id: Union[str, uuid.UUID],
        worker_id: Union[str, uuid.UUID],
    ) -> None:
        """
        Deletes a worker record.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(worker_id, str):
            worker_id = uuid.UUID(worker_id)

        stmt = select(Worker).where(Worker.id == worker_id, Worker.user_id == user_id)
        worker = db.scalar(stmt)
        if not worker:
            raise AppException("Worker not found.", code="WORKER_NOT_FOUND", status_code=404)

        db.delete(worker)
        db.commit()

    # -----------------------------------------------------------------------
    # Machines Operations
    # -----------------------------------------------------------------------

    @staticmethod
    def get_user_machines(
        db: Session,
        user_id: Union[str, uuid.UUID],
    ) -> List[MachineResponse]:
        """
        Retrieves all workshop equipment belonging to the user.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        stmt = select(Machine).where(Machine.user_id == user_id).order_by(Machine.name.asc())
        machines = db.scalars(stmt).all()
        return [MachineResponse.model_validate(m) for m in machines]

    @staticmethod
    def get_machine_by_id(
        db: Session,
        user_id: Union[str, uuid.UUID],
        machine_id: Union[str, uuid.UUID],
    ) -> MachineResponse:
        """
        Retrieves a single machine by ID with ownership verification.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(machine_id, str):
            machine_id = uuid.UUID(machine_id)

        stmt = select(Machine).where(Machine.id == machine_id, Machine.user_id == user_id)
        machine = db.scalar(stmt)
        if not machine:
            raise AppException("Machine not found.", code="MACHINE_NOT_FOUND", status_code=404)

        return MachineResponse.model_validate(machine)

    @staticmethod
    def create_machine(
        db: Session,
        user_id: Union[str, uuid.UUID],
        machine_in: MachineCreate,
    ) -> MachineResponse:
        """
        Registers a new workshop machine entity.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        machine = Machine(
            user_id=user_id,
            name=machine_in.name,
            machine_type=machine_in.machine_type,
            capacity_hours_per_day=machine_in.capacity_hours_per_day,
            is_available=machine_in.is_available,
        )

        db.add(machine)
        db.commit()
        db.refresh(machine)
        return MachineResponse.model_validate(machine)

    @staticmethod
    def update_machine(
        db: Session,
        user_id: Union[str, uuid.UUID],
        machine_id: Union[str, uuid.UUID],
        machine_in: MachineUpdate,
    ) -> MachineResponse:
        """
        Updates machine type, capacity, or operational status.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(machine_id, str):
            machine_id = uuid.UUID(machine_id)

        stmt = select(Machine).where(Machine.id == machine_id, Machine.user_id == user_id)
        machine = db.scalar(stmt)
        if not machine:
            raise AppException("Machine not found.", code="MACHINE_NOT_FOUND", status_code=404)

        if machine_in.name is not None:
            machine.name = machine_in.name
        if machine_in.machine_type is not None:
            machine.machine_type = machine_in.machine_type
        if machine_in.capacity_hours_per_day is not None:
            machine.capacity_hours_per_day = machine_in.capacity_hours_per_day
        if machine_in.is_available is not None:
            machine.is_available = machine_in.is_available

        db.commit()
        db.refresh(machine)
        return MachineResponse.model_validate(machine)

    @staticmethod
    def delete_machine(
        db: Session,
        user_id: Union[str, uuid.UUID],
        machine_id: Union[str, uuid.UUID],
    ) -> None:
        """
        Deletes a machine record.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(machine_id, str):
            machine_id = uuid.UUID(machine_id)

        stmt = select(Machine).where(Machine.id == machine_id, Machine.user_id == user_id)
        machine = db.scalar(stmt)
        if not machine:
            raise AppException("Machine not found.", code="MACHINE_NOT_FOUND", status_code=404)

        db.delete(machine)
        db.commit()

    # -----------------------------------------------------------------------
    # Production Summary KPI Metrics
    # -----------------------------------------------------------------------

    @staticmethod
    def get_production_summary(
        db: Session,
        user_id: Union[str, uuid.UUID],
    ) -> ProductionSummaryResponse:
        """
        Computes deterministic, aggregated production metrics for the user dashboard.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Orders metrics
        orders_stmt = select(ProductionOrder).where(ProductionOrder.user_id == user_id)
        all_orders = db.scalars(orders_stmt).all()

        total_orders = len(all_orders)
        pending = sum(1 for o in all_orders if o.status == OrderStatus.PENDING.value)
        in_progress = sum(1 for o in all_orders if o.status == OrderStatus.IN_PROGRESS.value)
        completed = sum(1 for o in all_orders if o.status == OrderStatus.COMPLETED.value)
        cancelled = sum(1 for o in all_orders if o.status == OrderStatus.CANCELLED.value)

        now_utc = datetime.now(timezone.utc)
        overdue = sum(
            1
            for o in all_orders
            if (o.deadline if o.deadline.tzinfo else o.deadline.replace(tzinfo=timezone.utc)) < now_utc
            and o.status not in (OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value)
        )

        # Worker metrics
        workers_stmt = select(Worker).where(Worker.user_id == user_id)
        all_workers = db.scalars(workers_stmt).all()
        total_workers = len(all_workers)
        available_workers = sum(1 for w in all_workers if w.is_available)
        total_worker_capacity = sum(w.capacity_hours_per_day for w in all_workers if w.is_available)

        # Machine metrics
        machines_stmt = select(Machine).where(Machine.user_id == user_id)
        all_machines = db.scalars(machines_stmt).all()
        total_machines = len(all_machines)
        available_machines = sum(1 for m in all_machines if m.is_available)
        total_machine_capacity = sum(m.capacity_hours_per_day for m in all_machines if m.is_available)

        return ProductionSummaryResponse(
            total_orders=total_orders,
            pending_orders=pending,
            in_progress_orders=in_progress,
            completed_orders=completed,
            cancelled_orders=cancelled,
            overdue_orders=overdue,
            total_workers=total_workers,
            available_workers=available_workers,
            total_worker_capacity_hours=round(total_worker_capacity, 2),
            total_machines=total_machines,
            available_machines=available_machines,
            total_machine_capacity_hours=round(total_machine_capacity, 2),
        )


production_service = ProductionService()
