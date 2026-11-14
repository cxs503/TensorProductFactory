from dataclasses import replace
from typing import Any

from product_factory.domain.work_order import WorkOrder


_PLATFORM_ROLES = {
    "platform", "data", "models", "applications", "infrastructure", "verifier", "strategy"
}
_RUNNERS = {"openhands", "native"}
_ORIGINS = {"owner", "agent"}
_TASK_CLASSES = {"research", "engineering"}


def mission_payload(
    work_order: WorkOrder,
    *,
    platform_project_id: str,
    platform_worker_role: str,
    base_ref: str = "main",
    platform_budget: dict[str, Any] | None = None,
    runner: str = "native",
    origin: str = "owner",
    co_project_ids: tuple[str, ...] = (),
    parent_mission_id: int | None = None,
    difficulty: int | None = None,
    task_class: str | None = None,
    problem_tree: tuple[str, ...] = (),
    baseline_summary: str | None = None,
    baseline_gap: str | None = None,
    exemption_declared: bool = False,
) -> dict[str, Any]:
    """Build a TensorPlatform MissionCreate payload without making a network call.

    platform_project_id is the key configured in FACTORY_PROFILE.projects,
    not a GitHub owner/repository slug. Domain budget units are deliberately not
    coerced into Platform's structured budget object; callers pass that mapping
    explicitly after choosing a budget policy.
    """
    if not platform_project_id.strip():
        raise ValueError("platform_project_id is required")
    if platform_worker_role not in _PLATFORM_ROLES:
        raise ValueError(f"unsupported TensorPlatform worker_role: {platform_worker_role}")
    if runner not in _RUNNERS:
        raise ValueError(f"unsupported TensorPlatform runner: {runner}")
    if origin not in _ORIGINS:
        raise ValueError(f"unsupported TensorPlatform origin: {origin}")
    if task_class is not None and task_class not in _TASK_CLASSES:
        raise ValueError(f"unsupported TensorPlatform task_class: {task_class}")
    if parent_mission_id is not None and parent_mission_id < 1:
        raise ValueError("parent_mission_id must be positive")
    if len(set(co_project_ids)) != len(co_project_ids):
        raise ValueError("co_project_ids must be unique")
    if platform_project_id in co_project_ids:
        raise ValueError("primary and co-project ids must be distinct")

    return {
        "goal": work_order.objective,
        "repo": platform_project_id,
        "base_ref": base_ref,
        "co_repos": list(co_project_ids) or None,
        "parent_mission_id": parent_mission_id,
        "budget": platform_budget or {},
        "runner": runner,
        "origin": origin,
        "worker_role": platform_worker_role,
        "task_key": work_order.work_order_id,
        "acceptance_criteria": list(work_order.acceptance_criteria),
        "difficulty": difficulty,
        "task_class": task_class,
        "problem_tree": list(problem_tree) or None,
        "baseline_summary": baseline_summary,
        "baseline_gap": baseline_gap,
        "exemption_declared": exemption_declared,
    }


def attach_mission(work_order: WorkOrder, mission_id: str) -> WorkOrder:
    """Return a new WorkOrder linked to an already-created Platform mission."""
    if not mission_id.strip():
        raise ValueError("mission_id must not be empty")
    return replace(work_order, platform_mission_id=mission_id)
