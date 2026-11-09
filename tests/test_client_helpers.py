import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from readfetch_client.endpoints import export_name
from readfetch_client.http_json import json_object_from_response


class ClientHelpersTest(unittest.TestCase):
    def test_probe_and_claim_fail_before_network(self) -> None:
        from readfetch_client import client

        async def run() -> None:
            with self.assertRaisesRegex(ValueError, "url is required"):
                await client.probe("")
            with self.assertRaisesRegex(ValueError, "receipt is required"):
                await client.submit_claim({})
            with self.assertRaisesRegex(ValueError, "reason must be"):
                await client.submit_claim(
                    {"receipt": "r", "reason": "bad", "address": "a", "signature": "s"}
                )

        __import__("asyncio").run(run())

    def test_official_client_sets_a_versioned_user_agent(self) -> None:
        from readfetch_client import client

        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        pkg_ver = next(
            line.split('"')[1]
            for line in pyproject.read_text(encoding="utf-8").splitlines()
            if line.startswith("version = ")
        )
        expected_ua = f"readfetch-client-py/{pkg_ver}"

        async def run() -> None:
            response = __import__("httpx").Response(200, json={"billed": False})
            http = AsyncMock()
            http.__aenter__.return_value.post.return_value = response
            with patch("readfetch_client.client.httpx.AsyncClient", return_value=http):
                await client._request_json(
                    method="POST", url="https://readfetch.com/v1/probe", body={},
                    paid=False, accept=(200,), env={}
                )
            self.assertEqual(
                http.__aenter__.return_value.post.call_args.kwargs["headers"]["user-agent"],
                expected_ua,
            )

        __import__("asyncio").run(run())

    def test_json_from_response_invalid(self) -> None:
        import httpx

        response = httpx.Response(200, text="<html>not json</html>")
        with self.assertRaises(RuntimeError) as ctx:
            json_object_from_response(response)
        self.assertIn("invalid JSON", str(ctx.exception))

    def test_assert_response_size_without_content_length(self) -> None:
        import httpx

        from readfetch_client.http_json import MAX_JSON_RESPONSE_BYTES, assert_response_size

        response = httpx.Response(
            500,
            content=b"x" * (MAX_JSON_RESPONSE_BYTES + 1),
        )
        with self.assertRaises(RuntimeError) as ctx:
            assert_response_size(response)
        self.assertIn("exceeds", str(ctx.exception))

    def test_json_oversized_body(self) -> None:
        import httpx

        from readfetch_client.http_json import MAX_JSON_RESPONSE_BYTES

        response = httpx.Response(200, content=b"x" * (MAX_JSON_RESPONSE_BYTES + 1))
        with self.assertRaises(RuntimeError) as ctx:
            json_object_from_response(response)
        self.assertIn("exceeds", str(ctx.exception))

    def test_export_name_matches_js(self) -> None:
        self.assertEqual(export_name("crawl_status"), "readfetchCrawlStatus")


if __name__ == "__main__":
    unittest.main()
