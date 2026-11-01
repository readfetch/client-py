import unittest

from readfetch_client.endpoints import endpoint_path


class EndpointPathTest(unittest.TestCase):
    def test_crawl_status_rejects_blank_id(self) -> None:
        with self.assertRaises(ValueError):
            endpoint_path("crawl_status", {"id": "   "})

    def test_crawl_status_encodes_id(self) -> None:
        self.assertEqual(
            endpoint_path("crawl_status", {"id": "job-1"}),
            "/v1/crawl/job-1",
        )


    def test_crawl_status_rejects_long_id(self) -> None:
        with self.assertRaises(ValueError):
            endpoint_path("crawl_status", {"id": "x" * 513})


if __name__ == "__main__":
    unittest.main()
