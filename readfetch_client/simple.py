"""High-level Client — private_key in, paid x402 handled on 402."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from typing import Any

from readfetch_client.config import normalize_account_hex
from readfetch_client import client as _impl


class Client:
    """Pass ``private_key`` (or ``EVM_PRIVATE_KEY``); paid routes sign x402 on 402 and retry."""

    def __init__(
        self,
        *,
        private_key: str | None = None,
        base_url: str | None = None,
        max_payment_usd: str | None = None,
    ) -> None:
        env: dict[str, str] = {
            k: v for k, v in os.environ.items() if isinstance(v, str)
        }
        if private_key is not None:
            env["EVM_PRIVATE_KEY"] = normalize_account_hex(private_key)
        if base_url is not None:
            env["READFETCH_BASE_URL"] = base_url.rstrip("/")
        if max_payment_usd is not None:
            env["READFETCH_MAX_PAYMENT_USD"] = str(max_payment_usd).strip()
        self._env: Mapping[str, str] = env

    @property
    def env(self) -> Mapping[str, str]:
        return self._env

    async def text(self, url: str | dict[str, Any]) -> dict[str, Any]:
        """``POST /v1/text`` — article Markdown in ``text``."""
        return await _impl.readfetch_text(url, env=self._env)

    async def fetch_async(self, url: str | dict[str, Any]) -> dict[str, Any]:
        """Async alias for ``text`` (same route; name matches JS ``fetch``)."""
        return await self.text(url)

    def fetch(self, url: str | dict[str, Any]) -> dict[str, Any]:
        """Read a URL via ``/v1/text``; 402 → sign → retry (sync)."""
        return self._run_sync(self.text(url))

    async def probe_async(self, url: str) -> dict[str, Any]:
        """``POST /v1/probe`` — free, no wallet."""
        return await _impl.probe(url, env=self._env)

    def probe(self, url: str) -> dict[str, Any]:
        """Free preflight (sync)."""
        return self._run_sync(self.probe_async(url))

    async def call(
        self,
        name: str,
        body: dict[str, Any] | None = None,
        *,
        path_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Any catalog route — same as ``readfetch_client.call`` with this client's env."""
        return await _impl.call(
            name, body, path_params=path_params, env=self._env
        )

    @staticmethod
    def _run_sync(coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        raise RuntimeError(
            "sync Client methods cannot run inside asyncio — "
            "use the async variants (`text`, `probe_async`, `fetch_async`)"
        )
