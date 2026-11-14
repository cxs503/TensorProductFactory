"""Independent product-level acceptance gate for submitted production work."""
from __future__ import annotations

from dataclasses import replace
from collections.abc import Iterable

from product_factory.domain.manifest import ProductManifest
from product_factory.domain.qa import QAReport, QAVerdict
from product_factory.domain.release import validate_release_candidate
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


def accept_submitted_work_orders(
    work_orders: Iterable[WorkOrder],
    *,
    manifest: ProductManifest,
    qa_report: QAReport,
) -> tuple[WorkOrder, ...]:
    """Accept a production order's submitted tasks only after product QA passes."""
    orders = tuple(work_orders)
    if not orders:
        raise ValueError("cannot accept an empty production order")
    production_ids = {order.production_order_id for order in orders}
    if len(production_ids) != 1:
        raise ValueError("all work orders must belong to the same production order")
    production_order_id = next(iter(production_ids))
    if qa_report.production_order_id != production_order_id:
        raise ValueError("QA report belongs to a different production order")
    if any(order.status is not WorkOrderStatus.SUBMITTED for order in orders):
        raise ValueError("every work order must be SUBMITTED before product acceptance")

    blockers = validate_release_candidate(manifest, qa_report)
    if blockers:
        raise ValueError(f"product acceptance blocked: {list(blockers)}")
    return tuple(replace(order, status=WorkOrderStatus.ACCEPTED) for order in orders)
