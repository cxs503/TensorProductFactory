import pytest

from product_factory.domain.manifest import RightsStatus
from product_factory.domain.work_order import WorkOrder, WorkOrderStatus
from product_factory.lifecycle.manifest_builder import build_product_manifest


def _accepted_order():
    return WorkOrder(
        work_order_id="wo-1",
        production_order_id="po-1",
        objective="Produce asset",
        worker_role="implementer",
        acceptance_criteria=("Asset is reviewed",),
        output_refs=("data://asset/a",),
        status=WorkOrderStatus.ACCEPTED,
    )


def _metadata(**overrides):
    value = {
        "asset_id": "asset-a",
        "version": "1.0.0",
        "role": "chapter",
        "sha256": "a" * 64,
        "source_ref": "mission://73/output/1",
        "rights_status": "pending",
        "required": True,
    }
    value.update(overrides)
    return value


def test_manifest_aggregates_accepted_outputs_and_explicit_metadata():
    manifest = build_product_manifest(
        manifest_id="manifest-1",
        product_id="ocean-lab",
        product_version="1.0.0",
        work_orders=[_accepted_order(), _accepted_order()],
        asset_metadata_by_uri={"data://asset/a": _metadata()},
    )
    assert len(manifest.assets) == 1
    assert manifest.assets[0].rights_status is RightsStatus.PENDING
    assert manifest.release_blockers()


def test_manifest_rejects_unaccepted_work_order():
    order = WorkOrder(
        work_order_id="wo-draft",
        production_order_id="po-1",
        objective="Produce asset",
        worker_role="implementer",
        acceptance_criteria=("Asset exists",),
    )
    with pytest.raises(ValueError, match="has not submitted its outputs"):
        build_product_manifest(
            manifest_id="m", product_id="p", product_version="1",
            work_orders=[order], asset_metadata_by_uri={},
        )


def test_manifest_requires_hash_and_provenance_metadata():
    with pytest.raises(ValueError, match="metadata fields"):
        build_product_manifest(
            manifest_id="m", product_id="p", product_version="1",
            work_orders=[_accepted_order()],
            asset_metadata_by_uri={"data://asset/a": {"asset_id": "asset-a"}},
        )


def test_manifest_can_be_built_before_final_product_acceptance():
    order = WorkOrder(
        work_order_id="wo-submitted", production_order_id="po-1",
        objective="Submit product asset", worker_role="implementer",
        acceptance_criteria=("Asset is ready for review",),
        output_refs=("data://asset/a",), status=WorkOrderStatus.SUBMITTED,
    )
    manifest = build_product_manifest(
        manifest_id="m", product_id="p", product_version="1",
        work_orders=[order], asset_metadata_by_uri={"data://asset/a": _metadata()},
    )
    assert manifest.assets[0].uri == "data://asset/a"
