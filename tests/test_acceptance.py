from datetime import datetime, timezone

import pytest

from product_factory.domain.manifest import AssetEntry, ProductManifest, RightsStatus
from product_factory.domain.qa import QAEvidence, QAReport, QAVerdict
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.acceptance import accept_submitted_work_orders


def _order(status=WorkOrderStatus.SUBMITTED):
    return WorkOrder(
        work_order_id="wo-1", production_order_id="po-1",
        objective="Deliver product content", worker_role="implementer",
        acceptance_criteria=("Complete deliverable",), output_refs=("data://a",),
        status=status,
    )


def _manifest():
    return ProductManifest(
        manifest_id="m-1", product_id="p-1", product_version="1.0.0",
        assets=(AssetEntry(
            asset_id="a-1", version="1.0.0", role="main", uri="data://a",
            sha256="c" * 64, source_ref="mission://1/output/1",
            rights_status=RightsStatus.CLEARED,
        ),),
    )


def _qa(verdict=QAVerdict.PASS):
    return QAReport(
        report_id="qa-1", production_order_id="po-1", product_version="1.0.0",
        reviewer_id="independent-reviewer", verdict=verdict,
        evidence=(QAEvidence("content.accuracy", "pass", ("bench://1",)),),
        reviewed_at=datetime(2026, 11, 14, tzinfo=timezone.utc),
        producer_ids=("agent-producer",),
        qa_profile_id="standard-digital-product", qa_profile_version="1.0.0",
    )


def test_acceptance_requires_passed_independent_qa():
    accepted = accept_submitted_work_orders([_order()], manifest=_manifest(), qa_report=_qa(), acceptance_profile_id="standard-digital-product")
    assert accepted[0].status is WorkOrderStatus.ACCEPTED


def test_failed_qa_cannot_accept_work_order():
    with pytest.raises(ValueError, match="acceptance blocked"):
        accept_submitted_work_orders(
            [_order()], manifest=_manifest(), qa_report=_qa(QAVerdict.NEEDS_REWORK), acceptance_profile_id="standard-digital-product"
        )


def test_draft_work_order_cannot_be_accepted():
    with pytest.raises(ValueError, match="SUBMITTED"):
        accept_submitted_work_orders(
            [_order(WorkOrderStatus.READY)], manifest=_manifest(), qa_report=_qa(), acceptance_profile_id="standard-digital-product"
        )


def test_qa_report_must_match_production_order():
    qa = QAReport(
        report_id="qa-2", production_order_id="another-order", product_version="1.0.0",
        reviewer_id="independent-reviewer", verdict=QAVerdict.PASS,
        evidence=(QAEvidence("content.accuracy", "pass", ("bench://1",)),),
        reviewed_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError, match="different production order"):
        accept_submitted_work_orders([_order()], manifest=_manifest(), qa_report=qa, acceptance_profile_id="standard-digital-product")


def test_acceptance_requires_manifest_to_cover_all_submitted_outputs():
    empty_manifest = ProductManifest(
        manifest_id="m-empty", product_id="p-1", product_version="1.0.0", assets=()
    )
    with pytest.raises(ValueError, match="missing from manifest"):
        accept_submitted_work_orders(
            [_order()], manifest=empty_manifest, qa_report=_qa(), acceptance_profile_id="standard-digital-product"
        )


def test_acceptance_rejects_wrong_product_qa_profile():
    with pytest.raises(ValueError, match="does not match the ProductSpec"):
        accept_submitted_work_orders(
            [_order()], manifest=_manifest(), qa_report=_qa(),
            acceptance_profile_id="software-release",
        )
