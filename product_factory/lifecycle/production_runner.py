"""One-tick production-order orchestrator over the WorkOrder DAG."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Protocol

from product_factory.adapters.platform_sync import sync_work_order
from product_factory.domain.production_order import ProductionOrder, ProductionOrderStatus
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.dispatch import dispatch_work_order
from product_factory.lifecycle.work_graph import dispatchable_work_orders, topological_order


class ProductionStore(Protocol):
    def get_product_spec(self, product_id: str, version: str): ...
    def get_production_order(self, production_order_id: str): ...
    def update_production_order(self, order: ProductionOrder, *, expected_revision: int) -> int: ...


class WorkOrderStore(Protocol):
    def get(self, work_order_id: str): ...
    def update(self, order: WorkOrder, *, expected_revision: int) -> int: ...
    def list_for_production_order(self, production_order_id: str) -> tuple[WorkOrder, ...]: ...


class MissionClient(Protocol):
    def create_mission(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def get_mission(self, mission_id: int | str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ProductionOrderTick:
    production_order: ProductionOrder
    synced_work_order_ids: tuple[str, ...]
    dispatched_work_order_ids: tuple[str, ...]
    accepted_work_order_ids: tuple[str, ...]
    waiting_work_order_ids: tuple[str, ...]


_POLLABLE = {
    WorkOrderStatus.DISPATCHED,
    WorkOrderStatus.RUNNING,
    WorkOrderStatus.BLOCKED,
    WorkOrderStatus.SUBMITTED,
}
_ACTIVE = {
    WorkOrderStatus.DISPATCHED,
    WorkOrderStatus.RUNNING,
    WorkOrderStatus.BLOCKED,
    WorkOrderStatus.SUBMITTED,
}


def advance_production_order(
    production_order_id: str,
    *,
    production_store: ProductionStore,
    work_order_store: WorkOrderStore,
    mission_client: MissionClient,
    platform_project_id: str,
    platform_worker_role: str,
    platform_options: dict[str, Any] | None = None,
) -> ProductionOrderTick:
    """Poll existing missions, dispatch newly unblocked tasks, and update order state.

    A Platform mission reaching succeeded/awaiting_acceptance only moves its
    WorkOrder to SUBMITTED. Independent ProductFactory QA must explicitly move
    it to ACCEPTED before dependent tasks can be dispatched.
    """
    stored_order = production_store.get_production_order(production_order_id)
    if stored_order is None:
        raise KeyError(production_order_id)
    order, order_revision = stored_order
    product = production_store.get_product_spec(order.product_id, order.product_version)
    if product is None:
        raise ValueError(
            f"production order references missing ProductSpec {order.product_id}@{order.product_version}"
        )
    if order.status in {
        ProductionOrderStatus.RELEASED,
        ProductionOrderStatus.FAILED,
        ProductionOrderStatus.CANCELLED,
        ProductionOrderStatus.QA,
    }:
        return ProductionOrderTick(order, (), (), (), ())

    work_orders = list(work_order_store.list_for_production_order(production_order_id))
    if not work_orders:
        raise ValueError("production order has no work orders")
    if any(item.production_order_id != production_order_id for item in work_orders):
        raise ValueError("work-order store returned a task from another production order")
    topological_order(work_orders)

    synced: list[str] = []
    by_id = {item.work_order_id: item for item in work_orders}
    for item in tuple(work_orders):
        if item.platform_mission_id and item.status in _POLLABLE:
            mission = mission_client.get_mission(item.platform_mission_id)
            updated = sync_work_order(item, mission)
            if updated != item:
                stored_task = work_order_store.get(item.work_order_id)
                if stored_task is None:
                    raise KeyError(item.work_order_id)
                _, revision = stored_task
                work_order_store.update(updated, expected_revision=revision)
                by_id[item.work_order_id] = updated
                synced.append(item.work_order_id)

    work_orders = [by_id[item.work_order_id] for item in work_orders]
    accepted = {item.work_order_id for item in work_orders if item.status is WorkOrderStatus.ACCEPTED}
    dispatched: list[str] = []
    options = dict(platform_options or {})
    for item in dispatchable_work_orders(work_orders, accepted):
        dispatch_work_order(
            item.work_order_id,
            store=work_order_store,
            client=mission_client,
            accepted_work_order_ids=accepted,
            platform_project_id=platform_project_id,
            platform_worker_role=platform_worker_role,
            **options,
        )
        dispatched.append(item.work_order_id)

    work_orders = list(work_order_store.list_for_production_order(production_order_id))
    accepted = {item.work_order_id for item in work_orders if item.status is WorkOrderStatus.ACCEPTED}
    failed = any(item.status is WorkOrderStatus.REJECTED for item in work_orders)
    all_accepted = bool(work_orders) and len(accepted) == len(work_orders)
    has_activity = any(item.status in _ACTIVE | {WorkOrderStatus.ACCEPTED} for item in work_orders)

    next_status = order.status
    if failed:
        next_status = ProductionOrderStatus.FAILED
    elif all_accepted:
        next_status = ProductionOrderStatus.QA
    elif has_activity and order.status is ProductionOrderStatus.PLANNED:
        next_status = ProductionOrderStatus.PRODUCING

    if next_status is not order.status:
        updated_order = replace(order, status=next_status)
        production_store.update_production_order(updated_order, expected_revision=order_revision)
        order = updated_order

    waiting = tuple(
        item.work_order_id for item in work_orders
        if item.status not in {WorkOrderStatus.ACCEPTED, WorkOrderStatus.REJECTED, WorkOrderStatus.CANCELLED}
    )
    return ProductionOrderTick(
        production_order=order,
        synced_work_order_ids=tuple(synced),
        dispatched_work_order_ids=tuple(dispatched),
        accepted_work_order_ids=tuple(sorted(accepted)),
        waiting_work_order_ids=waiting,
    )
