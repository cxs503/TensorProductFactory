"""SQLite persistence adapter for ProductFactory work orders.

SQLite is a durable single-node adapter for the MVP. The domain layer remains
storage-agnostic; deployments can replace this adapter with a shared database.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


class ConcurrentWorkOrderUpdate(RuntimeError):
    """The stored revision changed since the caller last read it."""


class SQLiteWorkOrderStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        if self.database_path == ":memory:":
            raise ValueError("SQLiteWorkOrderStore requires a file-backed database path")
        Path(self.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS product_factory_work_orders (
                    work_order_id TEXT PRIMARY KEY,
                    production_order_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK (revision >= 1),
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_pf_work_orders_production
                ON product_factory_work_orders(production_order_id, work_order_id)
            """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.database_path, timeout=10.0)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _encode(order: WorkOrder) -> str:
        value = {
            "work_order_id": order.work_order_id,
            "production_order_id": order.production_order_id,
            "objective": order.objective,
            "worker_role": order.worker_role,
            "acceptance_criteria": list(order.acceptance_criteria),
            "dependencies": list(order.dependencies),
            "budget": order.budget,
            "repository": order.repository,
            "platform_mission_id": order.platform_mission_id,
            "output_refs": list(order.output_refs),
            "status": order.status.value,
            "metadata": order.metadata,
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode(payload: str) -> WorkOrder:
        value = json.loads(payload)
        value["acceptance_criteria"] = tuple(value["acceptance_criteria"])
        value["dependencies"] = tuple(value["dependencies"])
        value["output_refs"] = tuple(value["output_refs"])
        value["status"] = WorkOrderStatus(value["status"])
        return WorkOrder(**value)

    def create(self, order: WorkOrder) -> int:
        with self._connection() as db:
            db.execute(
                """INSERT INTO product_factory_work_orders
                   (work_order_id, production_order_id, payload_json, revision)
                   VALUES (?, ?, ?, 1)""",
                (order.work_order_id, order.production_order_id, self._encode(order)),
            )
            return 1

    def get(self, work_order_id: str) -> tuple[WorkOrder, int] | None:
        with self._connection() as db:
            row = db.execute(
                """SELECT payload_json, revision FROM product_factory_work_orders
                   WHERE work_order_id = ?""",
                (work_order_id,),
            ).fetchone()
        if row is None:
            return None
        return self._decode(row["payload_json"]), int(row["revision"])

    def update(self, order: WorkOrder, *, expected_revision: int) -> int:
        if expected_revision < 1:
            raise ValueError("expected_revision must be positive")
        with self._connection() as db:
            cursor = db.execute(
                """UPDATE product_factory_work_orders
                   SET production_order_id = ?, payload_json = ?,
                       revision = revision + 1, updated_at = CURRENT_TIMESTAMP
                   WHERE work_order_id = ? AND revision = ?""",
                (
                    order.production_order_id,
                    self._encode(order),
                    order.work_order_id,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                exists = db.execute(
                    "SELECT 1 FROM product_factory_work_orders WHERE work_order_id = ?",
                    (order.work_order_id,),
                ).fetchone()
                if exists is None:
                    raise KeyError(order.work_order_id)
                raise ConcurrentWorkOrderUpdate(
                    f"work order {order.work_order_id} changed after revision {expected_revision}"
                )
            return expected_revision + 1

    def list_for_production_order(self, production_order_id: str) -> tuple[WorkOrder, ...]:
        with self._connection() as db:
            rows = db.execute(
                """SELECT payload_json FROM product_factory_work_orders
                   WHERE production_order_id = ? ORDER BY work_order_id""",
                (production_order_id,),
            ).fetchall()
        return tuple(self._decode(row["payload_json"]) for row in rows)
