import pytest

from product_factory.adapters.platform import attach_mission, mission_payload
from product_factory.domain.work_order import WorkOrder


def sample_work_order():
    return WorkOrder("wo-123", "po-1", "Create and validate the first chapter",
                     "content_producer", ("chapter exists", "sources cited"),
                     budget=7)


def test_platform_payload_uses_profile_project_id_and_explicit_platform_role():
    payload = mission_payload(
        sample_work_order(),
        platform_project_id="factory-project",
        platform_worker_role="applications",
        platform_budget={"max_tool_calls": 20},
        base_ref="main",
    )
    assert payload["repo"] == "factory-project"
    assert payload["task_key"] == "wo-123"
    assert payload["worker_role"] == "applications"
    assert payload["acceptance_criteria"] == ["chapter exists", "sources cited"]
    assert payload["budget"] == {"max_tool_calls": 20}
    assert payload["origin"] == "owner"
    assert payload["runner"] == "native"


def test_platform_payload_rejects_unknown_platform_role():
    with pytest.raises(ValueError):
        mission_payload(sample_work_order(), platform_project_id="factory-project",
                        platform_worker_role="content_producer")


def test_platform_payload_rejects_duplicate_or_same_co_project():
    with pytest.raises(ValueError):
        mission_payload(sample_work_order(), platform_project_id="factory-project",
                        platform_worker_role="applications",
                        co_project_ids=("factory-project",))


def test_attach_mission_returns_linked_copy():
    original = sample_work_order()
    linked = attach_mission(original, "mission-456")
    assert linked.platform_mission_id == "mission-456"
    assert original.platform_mission_id is None
