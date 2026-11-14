from datetime import datetime, timezone
from decimal import Decimal

import pytest

from product_factory.domain.product import ProductMode, ProductSpec
from product_factory.domain.qa import QAEvidence, QAReport, QAVerdict
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.work_order_state import transition


def test_product_spec_requires_nonnegative_price():
    with pytest.raises(ValueError):
        ProductSpec("p1", "1.0", "Sample", "families", ProductMode.STANDARD,
                    "ebook", "USD", Decimal("-1"), "ebook-v1")


def test_work_order_requires_acceptance_criteria():
    with pytest.raises(ValueError):
        WorkOrder("w1", "o1", "Create chapter", "writer", ())


def test_work_order_rejects_self_dependency():
    with pytest.raises(ValueError):
        WorkOrder("w1", "o1", "Create chapter", "writer", ("chapter exists",), ("w1",))


def test_work_order_transition_is_explicit():
    assert transition(WorkOrderStatus.DRAFT, WorkOrderStatus.READY) is WorkOrderStatus.READY
    with pytest.raises(ValueError):
        transition(WorkOrderStatus.DRAFT, WorkOrderStatus.ACCEPTED)


def test_producer_cannot_self_approve():
    with pytest.raises(ValueError):
        QAReport("qa1", "o1", "1.0", "agent-a", QAVerdict.PASS,
                 (QAEvidence("content", "pass", ("data://asset/1",)),),
                 datetime.now(timezone.utc), producer_ids=("agent-a",))


def test_pass_evidence_requires_reference():
    with pytest.raises(ValueError):
        QAEvidence("content", "pass", ())
