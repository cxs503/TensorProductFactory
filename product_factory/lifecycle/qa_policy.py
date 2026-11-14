"""Rule-profile driven, independent product QA."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone

from product_factory.domain.manifest import ProductManifest
from product_factory.domain.qa import QAEvidence, QAReport, QAVerdict
from product_factory.domain.qa_profile import QARuleProfile


_ALLOWED_OUTCOMES = {"pass", "fail", "needs_rework"}


def evaluate_qa_profile(
    *,
    report_id: str,
    production_order_id: str,
    product_version: str,
    reviewer_id: str,
    producer_ids: Iterable[str],
    required_rule_ids: Iterable[str] | None = None,
    profile: QARuleProfile | None = None,
    evidence_by_rule: Mapping[str, QAEvidence],
    manifest: ProductManifest,
    reviewed_at: datetime | None = None,
) -> QAReport:
    """Create an auditable QA report from a versioned rule profile's evidence.

    Required rules absent from the evidence map become explicit needs_rework
    findings. Extra rule IDs are rejected to catch profile/evidence drift.
    """
    if profile is not None:
        if required_rule_ids is not None and tuple(required_rule_ids) != profile.required_rule_ids:
            raise ValueError("required_rule_ids conflict with the supplied QA profile")
        required_rule_ids = profile.required_rule_ids
    required = tuple(dict.fromkeys(required_rule_ids or ()))
    if not required:
        raise ValueError("QA profile must define at least one required rule")
    unexpected = sorted(set(evidence_by_rule) - set(required))
    if unexpected:
        raise ValueError(f"evidence references rules outside the active profile: {unexpected}")

    findings: list[QAEvidence] = []
    for rule_id in required:
        evidence = evidence_by_rule.get(rule_id)
        if evidence is None:
            findings.append(
                QAEvidence(
                    rule_id=rule_id,
                    outcome="needs_rework",
                    evidence_refs=(),
                    note="Required QA evidence was not supplied",
                )
            )
            continue
        if evidence.rule_id != rule_id:
            raise ValueError(f"evidence key/rule_id mismatch for {rule_id}")
        if evidence.outcome not in _ALLOWED_OUTCOMES:
            raise ValueError(f"unsupported QA outcome for {rule_id}: {evidence.outcome}")
        findings.append(evidence)

    if product_version != manifest.product_version:
        findings.append(
            QAEvidence(
                rule_id="system.manifest.version_match",
                outcome="fail",
                evidence_refs=(manifest.manifest_id,),
                note="QA product version does not match the asset manifest",
            )
        )
    for blocker in manifest.release_blockers():
        findings.append(
            QAEvidence(
                rule_id=f"system.manifest.release_blocker.{len(findings) + 1}",
                outcome="fail",
                evidence_refs=(manifest.manifest_id,),
                note=blocker,
            )
        )

    outcomes = {item.outcome for item in findings}
    verdict = (
        QAVerdict.FAIL if "fail" in outcomes
        else QAVerdict.NEEDS_REWORK if "needs_rework" in outcomes
        else QAVerdict.PASS
    )
    return QAReport(
        report_id=report_id,
        production_order_id=production_order_id,
        product_version=product_version,
        reviewer_id=reviewer_id,
        verdict=verdict,
        evidence=tuple(findings),
        reviewed_at=reviewed_at or datetime.now(timezone.utc),
        producer_ids=tuple(producer_ids),
        qa_profile_id=profile.profile_id if profile else "",
        qa_profile_version=profile.version if profile else "",
    )
