"""Translate Platform mission state without confusing execution and product QA."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


_PLATFORM_TO_WORK_ORDER = {
    "queued": WorkOrderStatus.DISPATCHED,
    "claimed": WorkOrderStatus.RUNNING,
    "running": WorkOrderStatus.RUNNING,
    "awaiting_acceptance": WorkOrderStatus.SUBMITTED,
    "completed": WorkOrderStatus.SUBMITTED,
    "accepted": WorkOrderStatus.SUBMITTED,
    "rejected": WorkOrderStatus.REJECTED,
    "failed": WorkOrderStatus.REJECTED,
    "stopped": WorkOrderStatus.CANCELLED,
    "cancelled": WorkOrderStatus.CANCELLED,
}


def sync_work_order(work_order: WorkOrder, mission: dict[str, Any]) -> WorkOrder:
    """Return an updated task snapshot; never infer ProductFactory acceptance.

    Platform's own mission approval is an execution-governance signal. Product
    acceptance remains a separate QAReport decision in TensorProductFactory.
    """
    mission_id = mission.get("id")
    if mission_id is None:
        raise ValueError("mission response is missing id")
    if work_order.platform_mission_id and str(work_order.platform_mission_id) != str(mission_id):
        raise ValueError("mission id does not match the linked WorkOrder")
    platform_status = str(mission.get("status", "")).strip().lower()
    if platform_status not in _PLATFORM_TO_WORK_ORDER:
        raise ValueError(f"unsupported TensorPlatform mission status: {platform_status!r}")

    result = mission.get("result") or {}
    refs = result.get("output_refs", []) if isinstance(result, dict) else []
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        refs = []
    return replace(
        work_order,
        platform_mission_id=str(mission_id),
        status=_PLATFORM_TO_WORK_ORDER[platform_status],
        output_refs=tuple(dict.fromkeys((*work_order.output_refs, *refs))),
    )
