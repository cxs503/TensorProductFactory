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
    "succeeded": WorkOrderStatus.SUBMITTED,
    "awaiting_pr_merge": WorkOrderStatus.BLOCKED,
    "failed": WorkOrderStatus.REJECTED,
    "revoked": WorkOrderStatus.CANCELLED,
    "stopped": WorkOrderStatus.CANCELLED,
    "suspended": WorkOrderStatus.BLOCKED,
    "reopened": WorkOrderStatus.RUNNING,
    "orphan": WorkOrderStatus.REJECTED,
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
    if not isinstance(result, dict):
        raise ValueError("mission result must be an object")
    refs = result.get("output_refs", [])
    if not isinstance(refs, list):
        raise ValueError("mission result.output_refs must be a list")
    if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ValueError("mission result.output_refs must contain non-empty strings")
    return replace(
        work_order,
        platform_mission_id=str(mission_id),
        status=_PLATFORM_TO_WORK_ORDER[platform_status],
        output_refs=tuple(dict.fromkeys((*work_order.output_refs, *refs))),
    )
