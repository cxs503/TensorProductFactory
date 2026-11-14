from product_factory.domain.work_order import WorkOrderStatus


_ALLOWED = {
    WorkOrderStatus.DRAFT: {WorkOrderStatus.READY, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.READY: {WorkOrderStatus.DISPATCHED, WorkOrderStatus.BLOCKED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.DISPATCHED: {WorkOrderStatus.RUNNING, WorkOrderStatus.BLOCKED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.RUNNING: {WorkOrderStatus.SUBMITTED, WorkOrderStatus.BLOCKED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.SUBMITTED: {WorkOrderStatus.ACCEPTED, WorkOrderStatus.REJECTED},
    WorkOrderStatus.REJECTED: {WorkOrderStatus.READY, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.BLOCKED: {WorkOrderStatus.READY, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.ACCEPTED: set(),
    WorkOrderStatus.CANCELLED: set(),
}


def transition(current: WorkOrderStatus, target: WorkOrderStatus) -> WorkOrderStatus:
    if target not in _ALLOWED[current]:
        raise ValueError(f"invalid work-order transition: {current.value} -> {target.value}")
    return target
