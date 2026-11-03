"""readfetch x402 REST client."""

from __future__ import annotations

from typing import Any

__all__ = [
    "Client",
    "buyer_address",
    "call",
    "call_with_meta",
    "pay",
    "payment_config",
    "payment_from_response",
    "probe",
    "probe_with_meta",
    "quote",
    "readfetch_batch",
    "readfetch_crawl",
    "readfetch_crawl_status",
    "readfetch_diff",
    "readfetch_fetch",
    "readfetch_map",
    "readfetch_pdf",
    "readfetch_residential",
    "readfetch_scrape",
    "readfetch_search",
    "readfetch_section",
    "readfetch_screenshot",
    "readfetch_text",
    "readfetch_url",
    "request_id_from_response",
    "submit_claim",
    "submit_feedback",
    "x402_http_client",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if name == "Client":
        from readfetch_client.simple import Client

        return Client
    if name in ("payment_config", "buyer_address", "readfetch_url"):
        from readfetch_client import config as cfg

        return getattr(cfg, name)
    if name == "payment_from_response":
        from readfetch_client import payment as pay_mod

        return pay_mod.payment_from_response
    from readfetch_client import client as impl

    return getattr(impl, name)
