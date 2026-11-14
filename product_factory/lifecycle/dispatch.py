"""Dependency-safe, idempotent dispatch orchestration for one WorkOrder."""
from __future__ import annotations

from typing import Any, Protocol

from product_factory.adapters.platform import mission_payload
from product_factory.adapters.platform_sync import sync_work_order
from product_factory.domain.work_order import WorkOrderStatus


class WorkOrderStore(Protocol):
    def get(self, work_order_id: str): ...
    def update(self, order, *, expected_revision: int) -> int: ...


class MissionClient(Protocol):
    def create_mission(self, payload: dict[str, Any]) -> dict[str, Any]: ...


def dispatch_work_order(
    work_order_id: str,
    *,
    store: WorkOrderStore,
    client: MissionClient,
    accepted_work_order_ids: set[str] | frozenset[str],
    platform_project_id: str,
    platform_worker_role: str,
    **platform_options: Any,
):
    """Create/retrieve the Platform mission and durably link it to its WorkOrder.

    The WorkOrder ID is the Platform task_key. If the network response is lost
    after Platform creates the mission, retrying this function reuses that key
    and obtains the same mission rather than creating a duplicate.
    """
    stored = store.get(work_order_id)
    if stored is None:
        raise KeyError(work_order_id)
    order, revision = stored
    if order.status is not WorkOrderStatus.READY:
        raise ValueError(f"work order must be READY, got {order.status.value}")
    if order.platform_mission_id:
        raise ValueError("work order is already linked to a Platform mission")
    missing = sorted(set(order.dependencies) - set(accepted_work_order_ids))
    if missing:
        raise ValueError(f"work order dependencies are not independently accepted: {missing}")

    payload = mission_payload(
        order,
        platform_project_id=platform_project_id,
        platform_worker_role=platform_worker_role,
        **platform_options,
    )
    response = client.create_mission(payload)
    linked = sync_work_order(order, response)
    # If this compare-and-swap fails, do not hide it. A retry can safely recover
    # the same remote mission via task_key and reconcile against the new revision.
    store.update(linked, expected_revision=revision)
    return linked
