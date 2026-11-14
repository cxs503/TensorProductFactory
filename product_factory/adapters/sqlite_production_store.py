"""SQLite persistence for immutable ProductSpecs and versioned ProductionOrders."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from product_factory.domain.product import ProductMode, ProductSpec
from product_factory.domain.production_order import ProductionOrder, ProductionOrderStatus


class ConcurrentProductionOrderUpdate(RuntimeError):
    """The production-order revision changed after it was read."""


class SQLiteProductionStore:
    """Single-node catalog/order store with optimistic order updates.

    ProductSpecs are immutable and keyed by (product_id, version). Production
    orders reference an exact ProductSpec version and carry a CAS revision.
    """

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        if self.database_path == ":memory:":
            raise ValueError("SQLiteProductionStore requires a file-backed database path")
        Path(self.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS product_factory_product_specs (
                    product_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (product_id, version)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS product_factory_production_orders (
                    production_order_id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    product_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK (revision >= 1),
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id, product_version)
                      REFERENCES product_factory_product_specs(product_id, version)
                )
            """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.database_path, timeout=10.0)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _encode_product(spec: ProductSpec) -> str:
        value = {
            "product_id": spec.product_id,
            "version": spec.version,
            "name": spec.name,
            "audience": spec.audience,
            "mode": spec.mode.value,
            "delivery_format": spec.delivery_format,
            "currency": spec.currency,
            "list_price": str(spec.list_price),
            "acceptance_profile": spec.acceptance_profile,
            "description": spec.description,
            "requirements": list(spec.requirements),
            "metadata": spec.metadata,
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    @staticmethod
    def _decode_product(payload: str) -> ProductSpec:
        value = json.loads(payload)
        value["mode"] = ProductMode(value["mode"])
        value["list_price"] = Decimal(value["list_price"])
        value["requirements"] = tuple(value["requirements"])
        return ProductSpec(**value)

    @staticmethod
    def _encode_order(order: ProductionOrder) -> str:
        value = {
            "production_order_id": order.production_order_id,
            "product_id": order.product_id,
            "product_version": order.product_version,
            "quantity": order.quantity,
            "budget": order.budget,
            "created_at": order.created_at.isoformat(),
            "due_at": order.due_at.isoformat() if order.due_at else None,
            "status": order.status.value,
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode_order(payload: str) -> ProductionOrder:
        value = json.loads(payload)
        value["created_at"] = datetime.fromisoformat(value["created_at"])
        value["due_at"] = datetime.fromisoformat(value["due_at"]) if value["due_at"] else None
        value["status"] = ProductionOrderStatus(value["status"])
        return ProductionOrder(**value)

    def create_product_spec(self, spec: ProductSpec) -> None:
        with self._connection() as db:
            db.execute(
                """INSERT INTO product_factory_product_specs
                   (product_id, version, payload_json) VALUES (?, ?, ?)""",
                (spec.product_id, spec.version, self._encode_product(spec)),
            )

    def get_product_spec(self, product_id: str, version: str) -> ProductSpec | None:
        with self._connection() as db:
            row = db.execute(
                """SELECT payload_json FROM product_factory_product_specs
                   WHERE product_id = ? AND version = ?""",
                (product_id, version),
            ).fetchone()
        return self._decode_product(row["payload_json"]) if row else None

    def create_production_order(self, order: ProductionOrder) -> int:
        with self._connection() as db:
            db.execute(
                """INSERT INTO product_factory_production_orders
                   (production_order_id, product_id, product_version, payload_json, revision)
                   VALUES (?, ?, ?, ?, 1)""",
                (order.production_order_id, order.product_id, order.product_version,
                 self._encode_order(order)),
            )
        return 1

    def get_production_order(self, production_order_id: str) -> tuple[ProductionOrder, int] | None:
        with self._connection() as db:
            row = db.execute(
                """SELECT payload_json, revision FROM product_factory_production_orders
                   WHERE production_order_id = ?""",
                (production_order_id,),
            ).fetchone()
        if row is None:
            return None
        return self._decode_order(row["payload_json"]), int(row["revision"])

    def update_production_order(
        self, order: ProductionOrder, *, expected_revision: int
    ) -> int:
        if expected_revision < 1:
            raise ValueError("expected_revision must be positive")
        with self._connection() as db:
            cursor = db.execute(
                """UPDATE product_factory_production_orders
                   SET payload_json = ?, revision = revision + 1,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE production_order_id = ? AND product_id = ?
                     AND product_version = ? AND revision = ?""",
                (self._encode_order(order), order.production_order_id,
                 order.product_id, order.product_version, expected_revision),
            )
            if cursor.rowcount != 1:
                exists = db.execute(
                    "SELECT 1 FROM product_factory_production_orders WHERE production_order_id = ?",
                    (order.production_order_id,),
                ).fetchone()
                if exists is None:
                    raise KeyError(order.production_order_id)
                raise ConcurrentProductionOrderUpdate(
                    f"production order {order.production_order_id} changed after revision {expected_revision}"
                )
        return expected_revision + 1
