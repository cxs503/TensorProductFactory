"""Versioned, product-type-specific QA rule profiles."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QARuleProfile:
    profile_id: str
    version: str
    product_mode: str
    required_rule_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("profile_id", "version", "product_mode"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.product_mode not in {"standard", "personalized", "software"}:
            raise ValueError(f"unsupported product_mode: {self.product_mode}")
        if not self.required_rule_ids:
            raise ValueError("QA rule profile must contain at least one required rule")
        if any(not rule_id.strip() for rule_id in self.required_rule_ids):
            raise ValueError("QA rule IDs must not be empty")
        if len(self.required_rule_ids) != len(set(self.required_rule_ids)):
            raise ValueError("QA rule IDs must be unique")
