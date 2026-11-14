import pytest

from product_factory.domain.qa_profile import QARuleProfile


def test_profile_is_versioned_and_product_type_specific():
    profile = QARuleProfile(
        profile_id="digital-book", version="1.2.0", product_mode="standard",
        required_rule_ids=("content.accuracy", "rights.cleared", "delivery.complete"),
    )
    assert profile.version == "1.2.0"
    assert "rights.cleared" in profile.required_rule_ids


def test_profile_rejects_duplicate_rules():
    with pytest.raises(ValueError, match="unique"):
        QARuleProfile(
            profile_id="software", version="1", product_mode="software",
            required_rule_ids=("security.scan", "security.scan"),
        )
