from __future__ import annotations

from typing import Any

import httpx

MAX_JSON_RESPONSE_BYTES = 16 * 1024 * 1024


def assert_response_size(response: httpx.Response) -> None:
    raw = response.headers.get("content-length")
    if raw:
        try:
            n = int(raw)
        except ValueError:
            n = -1
        if n > MAX_JSON_RESPONSE_BYTES:
            raise RuntimeError(
                f"{response.status_code}: content-length {n} exceeds "
                f"{MAX_JSON_RESPONSE_BYTES} bytes"
            )
    if response.content and len(response.content) > MAX_JSON_RESPONSE_BYTES:
        raise RuntimeError(
            f"{response.status_code}: response body exceeds "
            f"{MAX_JSON_RESPONSE_BYTES} bytes"
        )


def json_object_from_response(response: httpx.Response) -> dict[str, Any]:
    assert_response_size(response)
    if not response.content:
        return {}
    try:
        parsed = response.json()
    except Exception as error:
        raise RuntimeError(
            f"{response.status_code}: {(response.text or '')[:400]} (invalid JSON)"
        ) from error
    if not isinstance(parsed, dict):
        raise RuntimeError(
            f"{response.status_code}: expected JSON object, got {type(parsed).__name__}"
        )
    return parsed
