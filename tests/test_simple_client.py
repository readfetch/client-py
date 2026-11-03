import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

from readfetch import Client
from readfetch_client import client as impl
from readfetch_client.config import normalize_account_hex
from readfetch_client.simple import Client as ClientImpl


def _valid_key() -> str:
    return "0x" + "ab" * 32


class NormalizeKeyTest(unittest.TestCase):
    def test_with_0x_prefix(self) -> None:
        raw = "0x" + "CD" * 32
        self.assertEqual(normalize_account_hex(raw), "0x" + "cd" * 32)

    def test_without_prefix(self) -> None:
        raw = "ee" * 32
        self.assertEqual(normalize_account_hex(raw), f"0x{raw}")

    def test_rejects_short(self) -> None:
        with self.assertRaises(ValueError):
            normalize_account_hex("0x" + "aa" * 16)


class SimpleClientTest(unittest.TestCase):
    def test_import_alias(self) -> None:
        self.assertIs(Client, ClientImpl)

    def test_lazy_import_from_readfetch_client(self) -> None:
        import readfetch_client

        self.assertIs(readfetch_client.Client, ClientImpl)

    def test_private_key_normalized_in_env(self) -> None:
        raw = "ab" * 32
        client = Client(private_key=raw)
        self.assertEqual(client.env["EVM_PRIVATE_KEY"], f"0x{raw}")

    def test_constructor_key_overrides_process_env(self) -> None:
        other = "0x" + "11" * 32
        with patch.dict(os.environ, {"EVM_PRIVATE_KEY": other}, clear=False):
            client = Client(private_key=_valid_key())
        self.assertEqual(client.env["EVM_PRIVATE_KEY"], _valid_key())

    def test_invalid_private_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            Client(private_key="not-a-key")

    def test_optional_overrides(self) -> None:
        client = Client(
            private_key="0x" + "cd" * 32,
            base_url="https://readfetch.com",
            max_payment_usd="0.5",
        )
        self.assertEqual(client.env["READFETCH_BASE_URL"], "https://readfetch.com")
        self.assertEqual(client.env["READFETCH_MAX_PAYMENT_USD"], "0.5")

    def test_text_delegates_to_readfetch_text(self) -> None:
        async def run() -> None:
            with patch.object(
                impl, "readfetch_text", new_callable=AsyncMock
            ) as mock_text:
                mock_text.return_value = {"text": "hello"}
                client = Client(private_key=_valid_key())
                out = await client.text("https://example.com/article")
                mock_text.assert_awaited_once_with(
                    "https://example.com/article", env=client.env
                )
                self.assertEqual(out, {"text": "hello"})

        asyncio.run(run())

    def test_fetch_sync_delegates(self) -> None:
        with patch.object(impl, "readfetch_text", new_callable=AsyncMock) as mock_text:
            mock_text.return_value = {"text": "sync"}
            client = Client(private_key=_valid_key())
            self.assertEqual(client.fetch("https://example.com"), {"text": "sync"})
            mock_text.assert_awaited_once()

    def test_fetch_sync_refuses_inside_asyncio(self) -> None:
        async def run() -> None:
            client = Client(private_key=_valid_key())
            with self.assertRaises(RuntimeError) as ctx:
                client.fetch("https://example.com")
            self.assertIn("asyncio", str(ctx.exception).lower())

        asyncio.run(run())

    def test_probe_sync_delegates(self) -> None:
        with patch.object(impl, "probe", new_callable=AsyncMock) as mock_probe:
            mock_probe.return_value = {"challenge": False}
            check = Client().probe("https://example.com")
            self.assertFalse(check["challenge"])
            mock_probe.assert_awaited_once()

    def test_call_delegates_to_impl(self) -> None:
        async def run() -> None:
            with patch.object(impl, "call", new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {"ok": True}
                rf = Client(private_key=_valid_key())
                out = await rf.call("map", {"url": "https://example.com"})
                mock_call.assert_awaited_once_with(
                    "map",
                    {"url": "https://example.com"},
                    path_params=None,
                    env=rf.env,
                )
                self.assertEqual(out, {"ok": True})

        asyncio.run(run())

    def test_fetch_async_alias(self) -> None:
        async def run() -> None:
            with patch.object(
                impl, "readfetch_text", new_callable=AsyncMock
            ) as mock_text:
                mock_text.return_value = {"text": "async"}
                client = Client(private_key=_valid_key())
                out = await client.fetch_async("https://example.com")
                self.assertEqual(out, {"text": "async"})
                mock_text.assert_awaited_once()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
