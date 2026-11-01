import unittest

from readfetch_client.endpoints import export_name
from readfetch_client.http_json import json_object_from_response


class ClientHelpersTest(unittest.TestCase):
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
