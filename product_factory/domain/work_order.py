from dataclasses import dataclass, field
from enum import StrEnum


class WorkOrderStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    production_order_id: str
    objective: str
    worker_role: str
    acceptance_criteria: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    budget: int = 1
    repository: str | None = None
    platform_mission_id: str | None = None
    output_refs: tuple[str, ...] = ()
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("work_order_id", "production_order_id", "objective", "worker_role"):
            if not getattr(self, key).strip():
                raise ValueError(f"{key} must not be empty")
        if self.budget < 0:
            raise ValueError("budget must be non-negative")
        if not self.acceptance_criteria:
            raise ValueError("at least one acceptance criterion is required")
        if self.work_order_id in self.dependencies:
            raise ValueError("a work order cannot depend on itself")
