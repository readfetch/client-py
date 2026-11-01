import os
import unittest

from readfetch_client.config import max_payment_usd, readfetch_base


class ConfigTest(unittest.TestCase):
    def test_readfetch_base_production(self) -> None:
        self.assertEqual(
            readfetch_base({"READFETCH_BASE_URL": "https://readfetch.com"}),
            "https://readfetch.com",
        )

    def test_readfetch_base_dev_local(self) -> None:
        env = {"READFETCH_BASE_URL": "http://127.0.0.1:8080", "READFETCH_DEV": "1"}
        self.assertEqual(readfetch_base(env), "http://127.0.0.1:8080")

    def test_readfetch_base_rejects_http_prod(self) -> None:
        with self.assertRaises(ValueError):
            readfetch_base({"READFETCH_BASE_URL": "http://readfetch.com"})

    def test_readfetch_base_rejects_userinfo(self) -> None:
        with self.assertRaises(ValueError):
            readfetch_base({"READFETCH_BASE_URL": "https://user:pass@readfetch.com"})

    def test_readfetch_base_rejects_non_http_scheme(self) -> None:
        with self.assertRaises(ValueError):
            readfetch_base({"READFETCH_BASE_URL": "file:///etc/passwd"})

    def test_readfetch_base_rejects_prod_path(self) -> None:
        with self.assertRaises(ValueError):
            readfetch_base({"READFETCH_BASE_URL": "https://readfetch.com/evil"})

    def test_readfetch_base_dev_ipv6(self) -> None:
        env = {
            "READFETCH_BASE_URL": "http://[::1]:8080",
            "READFETCH_DEV": "1",
        }
        self.assertEqual(readfetch_base(env), "http://::1:8080")

    def test_readfetch_url_joins_catalog_path(self) -> None:
        from readfetch_client.config import readfetch_url

        url = readfetch_url(
            {"READFETCH_BASE_URL": "https://readfetch.com"},
            "/v1/probe",
        )
        self.assertEqual(url, "https://readfetch.com/v1/probe")

    def test_readfetch_url_rejects_bad_path(self) -> None:
        from readfetch_client.config import readfetch_url

        with self.assertRaises(ValueError):
            readfetch_url({"READFETCH_BASE_URL": "https://readfetch.com"}, "v1/probe")

    def test_max_payment_usd_defaults(self) -> None:
        self.assertEqual(max_payment_usd({}), "1")

    def test_max_payment_usd_cap(self) -> None:
        with self.assertRaises(ValueError):
            max_payment_usd({"READFETCH_MAX_PAYMENT_USD": "101"})


if __name__ == "__main__":
    unittest.main()
