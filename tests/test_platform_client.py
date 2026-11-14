import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from product_factory.adapters.platform_client import PlatformAPIError, TensorPlatformClient


class FakeResponse:
    status = 200

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.value).encode()


def test_create_mission_sends_bearer_and_stable_task_key():
    client = TensorPlatformClient("https://example.test/api/v1", "secret", retries=0)
    payload = {"goal": "Do the work", "task_key": "wo-001"}
    with patch("product_factory.adapters.platform_client.urlopen", return_value=FakeResponse({"id": 17})) as call:
        result = client.create_mission(payload)
    assert result == {"id": 17}
    request = call.call_args.args[0]
    assert request.full_url == "https://example.test/api/v1/tensor/missions"
    assert request.get_header("Authorization") == "Bearer secret"
    assert json.loads(request.data) == payload


def test_create_mission_requires_task_key():
    client = TensorPlatformClient("https://example.test/api/v1", "secret")
    with pytest.raises(ValueError, match="task_key"):
        client.create_mission({"goal": "not enough"})


def test_get_mission_validates_id():
    client = TensorPlatformClient("https://example.test/api/v1", "secret")
    with pytest.raises(ValueError, match="integer"):
        client.get_mission("not-an-id")


def test_http_409_is_not_retried_and_preserves_detail():
    client = TensorPlatformClient("https://example.test/api/v1", "secret", retries=3)
    error = HTTPError(
        "https://example.test", 409, "Conflict", {}, BytesIO(b'{"detail":"task_key conflict"}')
    )
    with patch("product_factory.adapters.platform_client.urlopen", side_effect=error) as call:
        with pytest.raises(PlatformAPIError) as caught:
            client.create_mission({"task_key": "wo-1"})
    assert caught.value.status_code == 409
    assert "task_key conflict" in str(caught.value)
    assert call.call_count == 1
