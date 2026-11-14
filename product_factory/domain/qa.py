from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class QAVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REWORK = "needs_rework"


@dataclass(frozen=True)
class QAEvidence:
    rule_id: str
    outcome: str
    evidence_refs: tuple[str, ...]
    note: str = ""

    def __post_init__(self) -> None:
        if not self.rule_id.strip() or not self.outcome.strip():
            raise ValueError("rule_id and outcome are required")
        if self.outcome not in {"pass", "fail", "needs_rework"}:
            raise ValueError(f"unsupported QA evidence outcome: {self.outcome}")
        if self.outcome == "pass" and not self.evidence_refs:
            raise ValueError("passing QA evidence must cite at least one evidence reference")


@dataclass(frozen=True)
class QAReport:
    report_id: str
    production_order_id: str
    product_version: str
    reviewer_id: str
    verdict: QAVerdict
    evidence: tuple[QAEvidence, ...]
    reviewed_at: datetime
    producer_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.report_id, self.production_order_id, self.product_version, self.reviewer_id)):
            raise ValueError("QA report identifiers and reviewer are required")
        if self.reviewer_id in self.producer_ids:
            raise ValueError("producer cannot approve their own product")
        if not self.evidence:
            raise ValueError("QA report must contain evidence")
        rule_ids = [item.rule_id for item in self.evidence]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("QA evidence rule_id values must be unique")
        if self.verdict is QAVerdict.PASS and any(item.outcome != "pass" for item in self.evidence):
            raise ValueError("a passing QA report may contain only passing evidence")
