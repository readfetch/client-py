from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from typing import Any

import httpx
from eth_account import Account
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

from readfetch_client.config import max_payment_usd, readfetch_base, readfetch_url, require_account_hex, x402_network
from readfetch_client.endpoints import BY_NAME, endpoint_path
from readfetch_client.feedback_validation import normalize_feedback
from readfetch_client.http_json import assert_response_size, json_object_from_response
from readfetch_client.payment import payment_from_response

_TIMEOUT = 120.0
_USER_AGENT = "readfetch-client-py/0.1.15"

_x402_clients: dict[tuple[str, str, str], x402Client] = {}


def request_id_from_response(response: httpx.Response) -> str | None:
    return response.headers.get("x-request-id") or response.headers.get("X-Request-Id")


def _load_private_key(env: Mapping[str, str] | None = None) -> str:
    try:
        return require_account_hex(env)
    except ValueError as error:
        raise RuntimeError(str(error)) from error


def _x402_client(env: Mapping[str, str] | None = None) -> x402Client:
    env = os.environ if env is None else env
    hex_key = _load_private_key(env)
    fingerprint = hashlib.sha256(hex_key.encode()).hexdigest()
    network = x402_network(env)
    cap = max_payment_usd(env)
    cache_key = (fingerprint, network, cap)
    cached = _x402_clients.get(cache_key)
    if cached is not None:
        return cached
    client = x402Client().set_spend_controls(
        {"max_amount_per_payment": f"${cap}"}
    )
    account = Account.from_key(hex_key)
    register_exact_evm_client(client, EthAccountSigner(account), networks=network)
    _x402_clients[cache_key] = client
    return client


async def _request_json(
    *,
    method: str,
    url: str,
    body: dict[str, Any] | None,
    paid: bool,
    accept: tuple[int, ...],
    env: Mapping[str, str],
) -> tuple[dict[str, Any], str | None, httpx.Response]:
    headers = {"user-agent": _USER_AGENT}
    if method != "GET":
        headers["content-type"] = "application/json"
    if paid:
        async with x402HttpxClient(_x402_client(env)) as http:
            if method == "GET":
                response = await http.get(url, headers=headers, timeout=_TIMEOUT)
            else:
                response = await http.post(
                    url, json=body or {}, headers=headers, timeout=_TIMEOUT
                )
            await response.aread()
    else:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            if method == "GET":
                response = await http.get(url, headers=headers)
            else:
                response = await http.post(url, json=body or {}, headers=headers)
            await response.aread()
    if response.status_code not in accept:
        assert_response_size(response)
        raise RuntimeError(
            f"{response.status_code}: {(response.text or '')[:400]}"
        )
    data: dict[str, Any] = json_object_from_response(response)
    return data, request_id_from_response(response), response


def x402_http_client(env: Mapping[str, str] | None = None) -> x402HttpxClient:
    """Paid `httpx` client — signs x402 on 402 and retries (custom URLs)."""
    return x402HttpxClient(_x402_client(env))


async def call(
    name: str,
    body: dict[str, Any] | None = None,
    *,
    path_params: dict[str, str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    meta = await call_with_meta(
        name, body, path_params=path_params, env=env
    )
    return meta["data"]


async def call_with_meta(
    name: str,
    body: dict[str, Any] | None = None,
    *,
    path_params: dict[str, str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    spec = BY_NAME.get(name)
    if spec is None:
        raise ValueError(f"unknown endpoint `{name}`")
    env = os.environ if env is None else env
    path = endpoint_path(name, path_params)
    url = readfetch_url(env, path)
    accept = spec.accept if spec.accept else (200,)
    data, rid, response = await _request_json(
        method=spec.method,
        url=url,
        body=body,
        paid=not spec.free,
        accept=accept,
        env=env,
    )
    return {
        "data": data,
        "request_id": rid,
        "payment": payment_from_response(response),
    }


async def quote(
    name: str,
    body: dict[str, Any] | None = None,
    *,
    path_params: dict[str, str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """402 quote — no wallet. Paid catalog routes only."""
    spec = BY_NAME.get(name)
    if spec is None:
        raise ValueError(f"unknown endpoint `{name}`")
    if spec.free:
        raise ValueError(f"`{name}` is free — use call() instead of quote()")
    env = os.environ if env is None else env
    path = endpoint_path(name, path_params)
    url = readfetch_url(env, path)
    headers = {"user-agent": _USER_AGENT}
    if spec.method != "GET":
        headers["content-type"] = "application/json"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
        if spec.method == "GET":
            response = await http.get(url, headers=headers)
        else:
            response = await http.post(url, json=body or {}, headers=headers)
        await response.aread()
    if response.status_code != 402:
        assert_response_size(response)
        raise RuntimeError(
            f"expected 402 quote, got {response.status_code}: "
            f"{(response.text or '')[:400]}"
        )
    return {
        "status": 402,
        "body": json_object_from_response(response),
        "payment_required": payment_from_response(response)["payment_required"],
        "request_id": request_id_from_response(response),
    }


async def pay(
    name: str,
    body: dict[str, Any] | None = None,
    *,
    path_params: dict[str, str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Sign x402 and complete a paid call (alias for `call`)."""
    return await call(name, body, path_params=path_params, env=env)


async def probe(url: str, *, env: Mapping[str, str] | None = None) -> dict:
    data, _ = await probe_with_meta(url, env=env)
    return data


async def probe_with_meta(
    url: str, *, env: Mapping[str, str] | None = None
) -> tuple[dict, str | None]:
    meta = await call_with_meta("probe", {"url": _required_string(url, "url")}, env=env)
    return meta["data"], meta["request_id"]


async def submit_feedback(
    request_id: str,
    category: str,
    message: str,
    *,
    env: Mapping[str, str] | None = None,
) -> dict:
    rid, cat, msg = normalize_feedback(request_id, category, message)
    return await call(
        "feedback",
        {"request_id": rid, "category": cat, "message": msg},
        env=env,
    )


async def submit_claim(
    claim: dict[str, Any], *, env: Mapping[str, str] | None = None
) -> dict:
    return await call("claims", _normalize_claim(claim), env=env)


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def _normalize_claim(claim: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(claim, dict):
        raise ValueError("claim must be an object")
    for name in ("receipt", "reason", "address", "signature"):
        _required_string(claim.get(name), name)
    if claim["reason"] not in {"empty", "truncated", "stale", "wrong_content"}:
        raise ValueError("reason must be empty, truncated, stale, or wrong_content")
    note = claim.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > 500):
        raise ValueError("note must be at most 500 characters")
    return claim


async def readfetch_text(
    url: str | dict[str, Any], *, env: Mapping[str, str] | None = None
) -> dict:
    body = {"url": url} if isinstance(url, str) else url
    return await call("text", body, env=env)


async def readfetch_map(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("map", body, env=env)


async def readfetch_scrape(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("scrape", body, env=env)


async def readfetch_residential(
    body: dict[str, Any], *, env: Mapping[str, str] | None = None
) -> dict:
    return await call("residential", body, env=env)


async def readfetch_fetch(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("fetch", body, env=env)


async def readfetch_batch(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("batch", body, env=env)


async def readfetch_pdf(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("pdf", body, env=env)


async def readfetch_section(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("section", body, env=env)


async def readfetch_diff(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("diff", body, env=env)


async def readfetch_screenshot(
    body: dict[str, Any], *, env: Mapping[str, str] | None = None
) -> dict:
    return await call("screenshot", body, env=env)


async def readfetch_search(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("search", body, env=env)


async def readfetch_crawl(body: dict[str, Any], *, env: Mapping[str, str] | None = None) -> dict:
    return await call("crawl", body, env=env)


async def readfetch_crawl_status(
    job_id: str, *, env: Mapping[str, str] | None = None
) -> dict:
    return await call("crawl_status", None, path_params={"id": job_id}, env=env)
