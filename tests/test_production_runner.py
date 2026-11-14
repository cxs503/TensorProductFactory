from datetime import datetime, timezone
from decimal import Decimal

from product_factory.adapters.sqlite_production_store import SQLiteProductionStore
from product_factory.adapters.sqlite_store import SQLiteWorkOrderStore
from product_factory.domain.product import ProductMode, ProductSpec
from product_factory.domain.production_order import ProductionOrder, ProductionOrderStatus
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.production_runner import advance_production_order


class FakeMissionClient:
    def __init__(self):
        self.next_id = 100
        self.created = []
        self.missions = {}

    def create_mission(self, payload):
        self.next_id += 1
        mission = {"id": self.next_id, "status": "queued"}
        self.created.append(payload)
        self.missions[str(self.next_id)] = mission
        return mission

    def get_mission(self, mission_id):
        return self.missions[str(mission_id)]


def _spec():
    return ProductSpec(
        product_id="ocean-lab", version="0.1.0", name="Ocean Lab",
        audience="children 8-12", mode=ProductMode.STANDARD,
        delivery_format="interactive-web", currency="USD",
        list_price=Decimal("19.00"), acceptance_profile="standard-digital-product",
    )


def _order():
    return ProductionOrder(
        production_order_id="po-001", product_id="ocean-lab",
        product_version="0.1.0", quantity=1, budget=100,
        created_at=datetime(2026, 11, 14, tzinfo=timezone.utc),
    )


def _tasks():
    return (
        WorkOrder(
            work_order_id="wo-root", production_order_id="po-001",
            objective="Create the core content", worker_role="implementer",
            acceptance_criteria=("Content artifact exists",),
            status=WorkOrderStatus.READY,
        ),
        WorkOrder(
            work_order_id="wo-child", production_order_id="po-001",
            objective="Build the interactive experience", worker_role="implementer",
            acceptance_criteria=("Working interaction exists",),
            dependencies=("wo-root",), status=WorkOrderStatus.READY,
        ),
    )


def _stores(tmp_path):
    production = SQLiteProductionStore(tmp_path / "production.sqlite")
    production.create_product_spec(_spec())
    production.create_production_order(_order())
    tasks = SQLiteWorkOrderStore(tmp_path / "work.sqlite")
    for task in _tasks():
        tasks.create(task)
    return production, tasks


def test_runner_dispatches_roots_then_waits_for_independent_acceptance(tmp_path):
    production, tasks = _stores(tmp_path)
    client = FakeMissionClient()

    first = advance_production_order(
        "po-001", production_store=production, work_order_store=tasks,
        mission_client=client, platform_project_id="factory-project",
        platform_worker_role="applications",
    )
    assert first.production_order.status is ProductionOrderStatus.PRODUCING
    assert first.dispatched_work_order_ids == ("wo-root",)
    assert len(client.created) == 1

    root, revision = tasks.get("wo-root")
    client.missions[root.platform_mission_id] = {
        "id": int(root.platform_mission_id), "status": "succeeded",
        "result": {"output_refs": ["tensor-data://ocean-lab/content-v1"]},
    }
    second = advance_production_order(
        "po-001", production_store=production, work_order_store=tasks,
        mission_client=client, platform_project_id="factory-project",
        platform_worker_role="applications",
    )
    submitted, _ = tasks.get("wo-root")
    assert submitted.status is WorkOrderStatus.SUBMITTED
    assert submitted.output_refs == ("tensor-data://ocean-lab/content-v1",)
    assert second.dispatched_work_order_ids == ()
    assert len(client.created) == 1  # SUBMITTED is not independently ACCEPTED.

    tasks.update(
        WorkOrder(**{**submitted.__dict__, "status": WorkOrderStatus.ACCEPTED}),
        expected_revision=tasks.get("wo-root")[1],
    )
    third = advance_production_order(
        "po-001", production_store=production, work_order_store=tasks,
        mission_client=client, platform_project_id="factory-project",
        platform_worker_role="applications",
    )
    assert third.dispatched_work_order_ids == ("wo-child",)
    assert len(client.created) == 2


def test_runner_moves_order_to_qa_only_after_every_task_is_accepted(tmp_path):
    production, tasks = _stores(tmp_path)
    for task in _tasks():
        tasks.update(
            WorkOrder(**{**task.__dict__, "status": WorkOrderStatus.ACCEPTED}),
            expected_revision=tasks.get(task.work_order_id)[1],
        )
    result = advance_production_order(
        "po-001", production_store=production, work_order_store=tasks,
        mission_client=FakeMissionClient(), platform_project_id="factory-project",
        platform_worker_role="applications",
    )
    assert result.production_order.status is ProductionOrderStatus.QA
    saved, revision = production.get_production_order("po-001")
    assert saved.status is ProductionOrderStatus.QA
    assert revision == 2


def test_runner_rejects_missing_product_spec(tmp_path):
    production = SQLiteProductionStore(tmp_path / "production.sqlite")
    order = _order()
    # Bypass the store's FK only to model legacy/imported inconsistent data.
    with production._connection() as db:
        db.execute(
            """INSERT INTO product_factory_production_orders
               (production_order_id, product_id, product_version, payload_json, revision)
               VALUES (?, ?, ?, ?, 1)""",
            (order.production_order_id, order.product_id, order.product_version,
             production._encode_order(order)),
        )
    tasks = SQLiteWorkOrderStore(tmp_path / "work.sqlite")
    try:
        advance_production_order(
            "po-001", production_store=production, work_order_store=tasks,
            mission_client=FakeMissionClient(), platform_project_id="factory-project",
            platform_worker_role="applications",
        )
    except ValueError as exc:
        assert "missing ProductSpec" in str(exc)
    else:
        raise AssertionError("expected missing ProductSpec to block execution")
