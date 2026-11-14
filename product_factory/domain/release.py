from dataclasses import dataclass
from datetime import datetime

from product_factory.domain.manifest import ProductManifest
from product_factory.domain.qa import QAReport, QAVerdict


@dataclass(frozen=True)
class Release:
    release_id: str
    product_id: str
    product_version: str
    manifest_id: str
    qa_report_id: str
    package_uri: str
    package_sha256: str
    released_at: datetime

    def __post_init__(self) -> None:
        if not all((self.release_id, self.product_id, self.product_version,
                    self.manifest_id, self.qa_report_id, self.package_uri)):
            raise ValueError("release identifiers and package URI are required")
        digest = self.package_sha256.lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("package_sha256 must be a 64-character hexadecimal digest")


def validate_release_candidate(
    manifest: ProductManifest,
    qa_report: QAReport,
) -> tuple[str, ...]:
    blockers = list(manifest.release_blockers())
    if qa_report.verdict is not QAVerdict.PASS:
        blockers.append(f"QA verdict is {qa_report.verdict.value}")
    if qa_report.product_version != manifest.product_version:
        blockers.append("QA report product version does not match manifest")
    return tuple(blockers)
