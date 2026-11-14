from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any


class ProductMode(StrEnum):
    STANDARD = "standard"
    PERSONALIZED = "personalized"
    SOFTWARE = "software"


@dataclass(frozen=True)
class ProductSpec:
    product_id: str
    version: str
    name: str
    audience: str
    mode: ProductMode
    delivery_format: str
    currency: str
    list_price: Decimal
    acceptance_profile: str
    description: str = ""
    requirements: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("product_id", "version", "name", "audience", "delivery_format", "currency", "acceptance_profile"):
            if not getattr(self, key).strip():
                raise ValueError(f"{key} must not be empty")
        if self.list_price < 0:
            raise ValueError("list_price must be non-negative")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
