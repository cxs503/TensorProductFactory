import pytest

from product_factory.adapters.platform_sync import sync_work_order
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


def _work_order():
    return WorkOrder(
        work_order_id="wo-001",
        production_order_id="po-001",
        objective="Produce one validated asset",
        worker_role="implementer",
        acceptance_criteria=("A testable output exists",),
    )


@pytest.mark.parametrize(
    ("platform_status", "expected"),
    [
        ("queued", WorkOrderStatus.DISPATCHED),
        ("running", WorkOrderStatus.RUNNING),
        ("awaiting_acceptance", WorkOrderStatus.SUBMITTED),
        ("succeeded", WorkOrderStatus.SUBMITTED),
        ("awaiting_pr_merge", WorkOrderStatus.BLOCKED),
        ("suspended", WorkOrderStatus.BLOCKED),
        ("reopened", WorkOrderStatus.RUNNING),
        ("orphan", WorkOrderStatus.REJECTED),
        ("failed", WorkOrderStatus.REJECTED),
    ],
)
def test_platform_status_mapping_never_auto_accepts(platform_status, expected):
    updated = sync_work_order(_work_order(), {"id": 21, "status": platform_status})
    assert updated.status is expected
    assert updated.status is not WorkOrderStatus.ACCEPTED


def test_sync_rejects_wrong_mission_id():
    work = _work_order()
    linked = sync_work_order(work, {"id": 21, "status": "running"})
    with pytest.raises(ValueError, match="does not match"):
        sync_work_order(linked, {"id": 22, "status": "completed"})


def test_sync_collects_output_refs():
    updated = sync_work_order(
        _work_order(),
        {"id": 21, "status": "succeeded", "result": {"output_refs": ["data://a", "data://a"]}},
    )
    assert updated.output_refs == ("data://a",)
