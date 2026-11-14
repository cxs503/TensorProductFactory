from product_factory.domain.work_order import WorkOrder


def mission_payload(work_order: WorkOrder, repo: str | None = None, base_ref: str = "main") -> dict:
    """Map a WorkOrder to TensorPlatform MissionCreate fields.

    This is a pure mapping function. It does not call TensorPlatform and does not
    imply that a repository is allowlisted or that a mission was created.
    """
    selected_repo = repo or work_order.repository
    if not selected_repo:
        raise ValueError("a Platform execution repository is required")
    return {
        "goal": work_order.objective,
        "repo": selected_repo,
        "base_ref": base_ref,
        "budget": work_order.budget,
        "worker_role": work_order.worker_role,
        "task_key": work_order.work_order_id,
        "acceptance_criteria": list(work_order.acceptance_criteria),
        "origin": "tensorproductfactory",
        "task_class": "engineering",
    }


def attach_mission(work_order: WorkOrder, mission_id: str) -> WorkOrder:
    """Return a new WorkOrder linked to an already-created Platform mission."""
    if not mission_id.strip():
        raise ValueError("mission_id must not be empty")
    from dataclasses import replace
    return replace(work_order, platform_mission_id=mission_id)
