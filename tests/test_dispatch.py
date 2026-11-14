import pytest

from product_factory.adapters.sqlite_store import SQLiteWorkOrderStore
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.dispatch import dispatch_work_order


class FakeMissionClient:
    def __init__(self):
        self.calls = []

    def create_mission(self, payload):
        self.calls.append(payload)
        return {"id": 73, "status": "queued"}


def _ready_order():
    return WorkOrder(
        work_order_id="wo-child",
        production_order_id="po-1",
        objective="Produce the validated child asset",
        worker_role="implementer",
        acceptance_criteria=("A verifiable asset is produced",),
        dependencies=("wo-parent",),
        status=WorkOrderStatus.READY,
    )


def test_dispatch_checks_dependencies_and_persists_mission(tmp_path):
    store = SQLiteWorkOrderStore(tmp_path / "factory.sqlite3")
    order = _ready_order()
    store.create(order)
    client = FakeMissionClient()

    with pytest.raises(ValueError, match="not independently accepted"):
        dispatch_work_order(
            order.work_order_id,
            store=store,
            client=client,
            accepted_work_order_ids=set(),
            platform_project_id="factory-project",
            platform_worker_role="applications",
        )
    assert client.calls == []

    linked = dispatch_work_order(
        order.work_order_id,
        store=store,
        client=client,
        accepted_work_order_ids={"wo-parent"},
        platform_project_id="factory-project",
        platform_worker_role="applications",
    )
    assert linked.platform_mission_id == "73"
    assert linked.status is WorkOrderStatus.DISPATCHED
    assert client.calls[0]["task_key"] == "wo-child"
    saved, revision = store.get("wo-child")
    assert revision == 2
    assert saved == linked


def test_dispatch_requires_ready_work_order(tmp_path):
    store = SQLiteWorkOrderStore(tmp_path / "factory.sqlite3")
    order = WorkOrder(
        work_order_id="wo-draft",
        production_order_id="po-1",
        objective="Draft task",
        worker_role="implementer",
        acceptance_criteria=("Output exists",),
    )
    store.create(order)
    with pytest.raises(ValueError, match="READY"):
        dispatch_work_order(
            "wo-draft",
            store=store,
            client=FakeMissionClient(),
            accepted_work_order_ids=set(),
            platform_project_id="factory-project",
            platform_worker_role="applications",
        )
