from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ProductionOrderStatus(StrEnum):
    PLANNED = "planned"
    PRODUCING = "producing"
    QA = "qa"
    RELEASED = "released"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ProductionOrder:
    production_order_id: str
    product_id: str
    product_version: str
    quantity: int
    budget: int
    created_at: datetime
    due_at: datetime | None = None
    status: ProductionOrderStatus = ProductionOrderStatus.PLANNED

    def __post_init__(self) -> None:
        if not self.production_order_id or not self.product_id or not self.product_version:
            raise ValueError("order, product, and version identifiers are required")
        if self.quantity < 1:
            raise ValueError("quantity must be at least one")
        if self.budget < 0:
            raise ValueError("budget must be non-negative")
        if self.due_at and self.due_at < self.created_at:
            raise ValueError("due_at cannot precede created_at")
