import pytest

from product_factory.adapters.sqlite_store import (
    ConcurrentWorkOrderUpdate,
    SQLiteWorkOrderStore,
)
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


def _order():
    return WorkOrder(
        work_order_id="wo-001",
        production_order_id="po-001",
        objective="Create the first product asset",
        worker_role="implementer",
        acceptance_criteria=("Asset is present",),
        metadata={"language": "en"},
    )


def test_create_get_and_list_round_trip(tmp_path):
    store = SQLiteWorkOrderStore(tmp_path / "factory.sqlite")
    order = _order()
    assert store.create(order) == 1
    loaded, revision = store.get("wo-001")
    assert loaded == order
    assert revision == 1
    assert store.list_for_production_order("po-001") == (order,)


def test_update_uses_optimistic_revision(tmp_path):
    store = SQLiteWorkOrderStore(tmp_path / "factory.sqlite")
    order = _order()
    store.create(order)
    updated = WorkOrder(
        **{
            **order.__dict__,
            "status": WorkOrderStatus.DISPATCHED,
            "platform_mission_id": "42",
        }
    )
    assert store.update(updated, expected_revision=1) == 2
    loaded, revision = store.get("wo-001")
    assert revision == 2
    assert loaded.platform_mission_id == "42"
    assert loaded.status is WorkOrderStatus.DISPATCHED
    with pytest.raises(ConcurrentWorkOrderUpdate):
        store.update(order, expected_revision=1)


def test_update_unknown_order_raises_key_error(tmp_path):
    store = SQLiteWorkOrderStore(tmp_path / "factory.sqlite")
    with pytest.raises(KeyError):
        store.update(_order(), expected_revision=1)
