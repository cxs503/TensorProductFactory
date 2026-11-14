from datetime import datetime, timezone

import pytest

from product_factory.domain.manifest import AssetEntry, ProductManifest, RightsStatus
from product_factory.domain.qa import QAEvidence, QAVerdict
from product_factory.lifecycle.qa_policy import evaluate_qa_profile


def _manifest(rights=RightsStatus.CLEARED):
    return ProductManifest(
        manifest_id="m-1",
        product_id="p-1",
        product_version="1.0.0",
        assets=(
            AssetEntry(
                asset_id="a-1", version="1.0.0", role="main",
                uri="data://a-1", sha256="b" * 64,
                source_ref="mission://1/output/1", rights_status=rights,
            ),
        ),
    )


def _evaluate(manifest=None, evidence=None, **kwargs):
    return evaluate_qa_profile(
        report_id="qa-1",
        production_order_id="po-1",
        product_version="1.0.0",
        reviewer_id="independent-reviewer",
        producer_ids=("agent-producer",),
        required_rule_ids=("content.accuracy", "delivery.complete"),
        evidence_by_rule=evidence or {
            "content.accuracy": QAEvidence("content.accuracy", "pass", ("bench://accuracy/1",)),
            "delivery.complete": QAEvidence("delivery.complete", "pass", ("test://delivery/1",)),
        },
        manifest=manifest or _manifest(),
        reviewed_at=datetime(2026, 11, 14, tzinfo=timezone.utc),
        **kwargs,
    )


def test_all_required_evidence_and_cleared_assets_can_pass():
    report = _evaluate()
    assert report.verdict is QAVerdict.PASS


def test_missing_required_evidence_needs_rework():
    report = _evaluate(evidence={
        "content.accuracy": QAEvidence("content.accuracy", "pass", ("bench://accuracy/1",)),
    })
    assert report.verdict is QAVerdict.NEEDS_REWORK
    assert any(item.outcome == "needs_rework" for item in report.evidence)


def test_unresolved_asset_rights_block_qa_pass():
    report = _evaluate(manifest=_manifest(RightsStatus.PENDING))
    assert report.verdict is QAVerdict.FAIL


def test_profile_rejects_unexpected_evidence_rule():
    with pytest.raises(ValueError, match="outside the active profile"):
        _evaluate(evidence={
            "content.accuracy": QAEvidence("content.accuracy", "pass", ("bench://1",)),
            "delivery.complete": QAEvidence("delivery.complete", "pass", ("test://1",)),
            "random.rule": QAEvidence("random.rule", "pass", ("evidence://1",)),
        })


def test_producer_cannot_review_own_product():
    with pytest.raises(ValueError, match="cannot approve"):
        evaluate_qa_profile(
            report_id="qa-1", production_order_id="po-1", product_version="1.0.0",
            reviewer_id="agent-producer", producer_ids=("agent-producer",),
            required_rule_ids=("content.accuracy",),
            evidence_by_rule={"content.accuracy": QAEvidence("content.accuracy", "pass", ("evidence://1",))},
            manifest=_manifest(),
        )


def test_qa_report_cannot_claim_pass_with_nonpassing_evidence():
    from datetime import datetime, timezone
    from product_factory.domain.qa import QAReport

    with pytest.raises(ValueError, match="only passing evidence"):
        QAReport(
            report_id="qa-invalid", production_order_id="po-1", product_version="1.0.0",
            reviewer_id="reviewer", verdict=QAVerdict.PASS,
            evidence=(QAEvidence("content.accuracy", "needs_rework", ()),),
            reviewed_at=datetime.now(timezone.utc),
        )
