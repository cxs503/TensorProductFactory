from collections import deque
from collections.abc import Iterable

from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


def topological_order(work_orders: Iterable[WorkOrder]) -> tuple[str, ...]:
    """Return deterministic dependency order, rejecting missing refs and cycles."""
    orders = tuple(work_orders)
    by_id = {order.work_order_id: order for order in orders}
    if len(by_id) != len(orders):
        raise ValueError("work_order_id values must be unique")

    indegree = {order_id: 0 for order_id in by_id}
    children: dict[str, list[str]] = {order_id: [] for order_id in by_id}
    for order in orders:
        for dependency in order.dependencies:
            if dependency not in by_id:
                raise ValueError(f"unknown dependency {dependency!r} for {order.work_order_id}")
            indegree[order.work_order_id] += 1
            children[dependency].append(order.work_order_id)

    ready = deque(order.work_order_id for order in orders if indegree[order.work_order_id] == 0)
    result: list[str] = []
    while ready:
        current = ready.popleft()
        result.append(current)
        for child in children[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if len(result) != len(orders):
        cyclic = sorted(order_id for order_id, degree in indegree.items() if degree > 0)
        raise ValueError(f"work-order dependency cycle detected: {', '.join(cyclic)}")
    return tuple(result)


def dispatchable_work_orders(
    work_orders: Iterable[WorkOrder],
    accepted_work_order_ids: set[str] | frozenset[str],
) -> tuple[WorkOrder, ...]:
    """Return READY tasks whose full dependency set has been independently accepted."""
    orders = tuple(work_orders)
    topological_order(orders)
    return tuple(
        order for order in orders
        if order.status is WorkOrderStatus.READY
        and set(order.dependencies).issubset(accepted_work_order_ids)
    )
