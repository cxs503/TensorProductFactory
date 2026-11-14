"""Small synchronous client for the TensorPlatform Mission API.

The caller owns persistence and scheduling. POST retries are safe only because
ProductFactory sends a stable task_key and TensorPlatform enforces task_key
idempotency within the authenticated organization.
"""
from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PlatformAPIError(RuntimeError):
    def __init__(self, status_code: int | None, message: str, response_body: Any = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"TensorPlatform API error ({self.status_code}): {self.message}"


class TensorPlatformClient:
    def __init__(
        self,
        api_base_url: str,
        token: str,
        *,
        timeout_seconds: float = 20.0,
        retries: int = 2,
        retry_backoff_seconds: float = 0.4,
    ) -> None:
        if not api_base_url.strip():
            raise ValueError("api_base_url must not be empty")
        if not token.strip():
            raise ValueError("token must not be empty")
        if timeout_seconds <= 0 or retries < 0 or retry_backoff_seconds < 0:
            raise ValueError("invalid timeout/retry configuration")
        self.api_base_url = api_base_url.rstrip("/")
        self.token = token.strip()
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_backoff_seconds = retry_backoff_seconds

    def create_mission(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create or idempotently retrieve a mission using its stable task_key."""
        task_key = payload.get("task_key")
        if not isinstance(task_key, str) or not task_key.strip():
            raise ValueError("payload.task_key is required for safe dispatch")
        return self._request("POST", "/tensor/missions", payload, retry_post=True)

    def get_mission(self, mission_id: int | str) -> dict[str, Any]:
        try:
            parsed_id = int(mission_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("mission_id must be an integer") from exc
        if parsed_id < 1:
            raise ValueError("mission_id must be positive")
        return self._request("GET", f"/tensor/missions/{parsed_id}")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        retry_post: bool = False,
    ) -> dict[str, Any]:
        body = None if payload is None else json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        request = Request(
            f"{self.api_base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
        )
        attempts = self.retries + 1 if method == "GET" or retry_post else 1
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = response.read()
                    decoded = json.loads(raw.decode("utf-8")) if raw else {}
                    if not isinstance(decoded, dict):
                        raise PlatformAPIError(response.status, "expected a JSON object", decoded)
                    return decoded
            except HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    detail: Any = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    detail = raw
                message = detail.get("detail", detail) if isinstance(detail, dict) else detail
                # Never retry client/auth/conflict errors. Retry only transient server failures.
                if exc.code not in {500, 502, 503, 504} or attempt + 1 >= attempts:
                    raise PlatformAPIError(exc.code, str(message), detail) from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt + 1 >= attempts:
                    raise PlatformAPIError(None, str(exc)) from exc
            if self.retry_backoff_seconds:
                time.sleep(self.retry_backoff_seconds * (2**attempt))
        raise AssertionError("unreachable")
