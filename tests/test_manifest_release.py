from datetime import datetime, timezone

import pytest

from product_factory.domain.manifest import AssetEntry, ProductManifest, RightsStatus
from product_factory.domain.qa import QAEvidence, QAReport, QAVerdict
from product_factory.domain.release import validate_release_candidate


def asset(rights=RightsStatus.CLEARED, required=True, asset_id="asset-1"):
    return AssetEntry(asset_id, "v1", "chapter", "tensor-data://asset-1", "a" * 64,
                      "source://origin", rights, required)


def qa(verdict=QAVerdict.PASS, version="1.0"):
    return QAReport("qa-1", "order-1", version, "reviewer",
                    verdict, (QAEvidence("content", "pass", ("evidence://1",)),),
                    datetime.now(timezone.utc), producer_ids=("writer-agent",))


def test_manifest_blocks_uncleared_required_asset():
    manifest = ProductManifest("m1", "p1", "1.0", (asset(RightsStatus.PENDING),))
    assert "required asset asset-1 rights are pending" in manifest.release_blockers()


def test_optional_uncleared_asset_does_not_block_release():
    manifest = ProductManifest("m1", "p1", "1.0", (asset(RightsStatus.UNKNOWN, required=False),))
    assert manifest.release_blockers() == ()


def test_release_requires_passing_qa_and_matching_version():
    manifest = ProductManifest("m1", "p1", "1.0", (asset(),))
    assert validate_release_candidate(manifest, qa()) == ()
    assert "QA verdict is fail" in validate_release_candidate(manifest, qa(QAVerdict.FAIL))
    assert "QA report product version does not match manifest" in validate_release_candidate(manifest, qa(version="2.0"))


def test_asset_checksum_must_be_sha256():
    with pytest.raises(ValueError):
        AssetEntry("a", "v1", "image", "uri", "not-a-hash", "source", RightsStatus.CLEARED)


def test_manifest_rejects_duplicate_asset_ids():
    with pytest.raises(ValueError):
        ProductManifest("m1", "p1", "1.0", (asset(), asset(asset_id="asset-1")))
