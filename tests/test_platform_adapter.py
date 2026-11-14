import pytest

from product_factory.adapters.platform import attach_mission, mission_payload
from product_factory.domain.work_order import WorkOrder


def sample_work_order(repository=None):
    return WorkOrder("wo-123", "po-1", "Create and validate the first chapter",
                     "content_producer", ("chapter exists", "sources cited"),
                     budget=7, repository=repository)


def test_platform_payload_maps_work_order_fields():
    payload = mission_payload(sample_work_order("cxs503/OceanLab"), base_ref="main")
    assert payload["repo"] == "cxs503/OceanLab"
    assert payload["task_key"] == "wo-123"
    assert payload["worker_role"] == "content_producer"
    assert payload["acceptance_criteria"] == ["chapter exists", "sources cited"]
    assert payload["budget"] == 7


def test_platform_payload_requires_execution_repository():
    with pytest.raises(ValueError):
        mission_payload(sample_work_order())


def test_attach_mission_returns_linked_copy():
    original = sample_work_order("cxs503/OceanLab")
    linked = attach_mission(original, "mission-456")
    assert linked.platform_mission_id == "mission-456"
    assert original.platform_mission_id is None
