from __future__ import annotations

import os
import re
from urllib.parse import urlparse

from collections.abc import Mapping

_PRODUCTION_HOSTS = frozenset({"readfetch.com", "www.readfetch.com"})
_DEV_HOSTS = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})


def is_dev_host(hostname: str) -> bool:
    return _normalize_hostname(hostname) in _DEV_HOSTS


_MAX_PAYMENT_RE = re.compile(r"^\d+(\.\d{1,6})?$")
_HEX_KEY_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")


def _normalize_hostname(hostname: str) -> str:
    return hostname.rstrip(".").lower()


def _format_origin(scheme: str, parsed) -> str:
    host = parsed.hostname
    if not host:
        raise ValueError("READFETCH_BASE_URL must include a hostname")
    host = _normalize_hostname(host)
    if parsed.port:
        return f"{scheme}://{host}:{parsed.port}"
    return f"{scheme}://{host}"


def readfetch_base(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    raw = env.get("READFETCH_BASE_URL", "https://readfetch.com").rstrip("/")
    parsed = urlparse(raw)
    if parsed.username or parsed.password:
        raise ValueError("READFETCH_BASE_URL must not include userinfo")
    if parsed.scheme not in ("http", "https"):
        raise ValueError("READFETCH_BASE_URL must use http or https")
    host = _normalize_hostname(parsed.hostname or "")
    if not host:
        raise ValueError("READFETCH_BASE_URL must include a hostname")
    if host in _PRODUCTION_HOSTS:
        if parsed.scheme != "https":
            raise ValueError("READFETCH_BASE_URL must use https for readfetch.com")
        path = parsed.path or ""
        if path not in ("", "/"):
            raise ValueError(
                "READFETCH_BASE_URL must not include a path on readfetch.com"
            )
        if parsed.port is not None and parsed.port != 443:
            raise ValueError(
                "READFETCH_BASE_URL must use default https port for readfetch.com"
            )
        return _format_origin("https", parsed)
    if env.get("READFETCH_DEV") == "1" and is_dev_host(host):
        scheme = parsed.scheme or "http"
        return _format_origin(scheme, parsed)
    raise ValueError(
        "READFETCH_BASE_URL must be https://readfetch.com "
        "(or localhost with READFETCH_DEV=1)"
    )


def readfetch_url(env: Mapping[str, str] | None, path: str) -> str:
    base = readfetch_base(env)
    if not path.startswith("/"):
        raise ValueError("endpoint path must start with /")
    url = f"{base}{path}"
    if urlparse(url).netloc != urlparse(base).netloc:
        raise ValueError("request URL origin must match READFETCH_BASE_URL")
    return url


def max_payment_usd(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    raw = (env.get("READFETCH_MAX_PAYMENT_USD") or "1").strip()
    if not _MAX_PAYMENT_RE.fullmatch(raw):
        raise ValueError("READFETCH_MAX_PAYMENT_USD must be a decimal amount")
    amount = float(raw)
    if amount <= 0 or amount > 100:
        raise ValueError("READFETCH_MAX_PAYMENT_USD must be between 0 and 100")
    return raw


def x402_network(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    base = readfetch_base(env)
    host = _normalize_hostname(urlparse(base).hostname or "")
    if env.get("READFETCH_DEV") == "1" and is_dev_host(host):
        return "eip155:84532"
    return "eip155:8453"


def load_account_hex(env: Mapping[str, str] | None = None) -> str | None:
    """Return normalized key hex, or None if unset or invalid (no raise)."""
    env = os.environ if env is None else env
    raw = (env.get("EVM_PRIVATE_KEY") or env.get("X402_BUYER_KEY") or "").strip()
    if not raw:
        return None
    hex_key = raw if raw.startswith("0x") else f"0x{raw}"
    if not _HEX_KEY_RE.fullmatch(hex_key):
        return None
    return hex_key.lower()


def require_account_hex(env: Mapping[str, str] | None = None) -> str:
    """Strict key load for paid calls — raises if missing or malformed."""
    hex_key = load_account_hex(env)
    if hex_key is None:
        env = os.environ if env is None else env
        if not (env.get("EVM_PRIVATE_KEY") or env.get("X402_BUYER_KEY") or "").strip():
            raise ValueError("Set EVM_PRIVATE_KEY (Base wallet with USDC)")
        raise ValueError("EVM_PRIVATE_KEY must be 64 hex bytes (optional 0x prefix)")
    return hex_key


def buyer_address(env: Mapping[str, str] | None = None) -> str | None:
    hex_key = load_account_hex(env)
    if not hex_key:
        return None
    try:
        from eth_account import Account

        return Account.from_key(hex_key).address
    except (ValueError, TypeError):
        return None


def payment_config(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env = os.environ if env is None else env
    address = buyer_address(env)
    return {
        "base_url": readfetch_base(env),
        "network": x402_network(env),
        "max_payment_usd": max_payment_usd(env),
        "buyer_address": address,
        "signing_ready": address is not None,
    }
