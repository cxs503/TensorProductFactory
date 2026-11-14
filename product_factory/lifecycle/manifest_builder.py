"""Build a product manifest from accepted task outputs and verified asset metadata.

Mission output references are pointers, not proof of ownership, integrity, or
license. Every reference must be accompanied by explicit metadata supplied by
the ingestion/rights workflow; this module never invents hashes or rights.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from product_factory.domain.manifest import AssetEntry, ProductManifest, RightsStatus
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus


_REQUIRED_METADATA = {
    "asset_id", "version", "role", "sha256", "source_ref", "rights_status"
}


def build_product_manifest(
    *,
    manifest_id: str,
    product_id: str,
    product_version: str,
    work_orders: Iterable[WorkOrder],
    asset_metadata_by_uri: Mapping[str, Mapping[str, Any]],
) -> ProductManifest:
    """Aggregate accepted WorkOrder outputs; reject missing or ambiguous metadata."""
    outputs: list[str] = []
    for order in work_orders:
        if order.status not in {WorkOrderStatus.SUBMITTED, WorkOrderStatus.ACCEPTED}:
            raise ValueError(f"work order {order.work_order_id} has not submitted its outputs")
        outputs.extend(order.output_refs)

    unique_outputs = tuple(dict.fromkeys(outputs))
    if not unique_outputs:
        raise ValueError("no accepted WorkOrder output references were supplied")

    missing_refs = sorted(set(unique_outputs) - set(asset_metadata_by_uri))
    if missing_refs:
        raise ValueError(f"asset metadata missing for output references: {missing_refs}")

    assets: list[AssetEntry] = []
    for uri in unique_outputs:
        metadata = asset_metadata_by_uri[uri]
        missing_fields = sorted(_REQUIRED_METADATA - set(metadata))
        if missing_fields:
            raise ValueError(f"asset {uri} is missing metadata fields: {missing_fields}")
        required_value = metadata.get("required", True)
        if not isinstance(required_value, bool):
            raise ValueError(f"asset {uri} required flag must be a boolean")
        assets.append(
            AssetEntry(
                asset_id=str(metadata["asset_id"]),
                version=str(metadata["version"]),
                role=str(metadata["role"]),
                uri=uri,
                sha256=str(metadata["sha256"]),
                source_ref=str(metadata["source_ref"]),
                rights_status=RightsStatus(str(metadata["rights_status"])),
                required=required_value,
            )
        )
    return ProductManifest(
        manifest_id=manifest_id,
        product_id=product_id,
        product_version=product_version,
        assets=tuple(assets),
    )
