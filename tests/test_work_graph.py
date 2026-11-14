import pytest

from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.work_graph import dispatchable_work_orders, topological_order


def order(order_id, dependencies=(), status=WorkOrderStatus.READY):
    return WorkOrder(order_id, "po-1", f"Do {order_id}", "implementer",
                     ("output is verifiable",), tuple(dependencies), status=status)


def test_topological_order_respects_dependencies():
    orders = (order("publish", ("qa",)), order("qa", ("build",)), order("build"))
    assert topological_order(orders) == ("build", "qa", "publish")


def test_topological_order_rejects_unknown_dependency():
    with pytest.raises(ValueError, match="unknown dependency"):
        topological_order((order("a", ("missing",)),))


def test_topological_order_rejects_cycle():
    with pytest.raises(ValueError, match="cycle"):
        topological_order((order("a", ("b",)), order("b", ("a",))))


def test_dispatchable_requires_accepted_dependencies():
    orders = (order("first"), order("second", ("first",)), order("draft", status=WorkOrderStatus.DRAFT))
    assert tuple(o.work_order_id for o in dispatchable_work_orders(orders, set())) == ("first",)
    assert tuple(o.work_order_id for o in dispatchable_work_orders(orders, {"first"})) == ("first", "second")
