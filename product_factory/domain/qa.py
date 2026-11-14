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
