import unittest

from readfetch_client.config import payment_config
from readfetch_client.payment import payment_from_response


class PaymentTest(unittest.TestCase):
    def test_load_account_hex_normalizes_case(self) -> None:
        from readfetch_client.config import load_account_hex

        upper = "0x" + "A" * 64
        lower = "0x" + "a" * 64
        self.assertEqual(load_account_hex({"EVM_PRIVATE_KEY": upper}), lower)

    def test_payment_config_without_key(self) -> None:
        cfg = payment_config({"READFETCH_BASE_URL": "https://readfetch.com"})
        self.assertEqual(cfg["base_url"], "https://readfetch.com")
        self.assertEqual(cfg["network"], "eip155:8453")
        self.assertFalse(cfg["signing_ready"])
        self.assertIsNone(cfg["buyer_address"])

    def test_payment_config_invalid_hex_no_raise(self) -> None:
        cfg = payment_config({"EVM_PRIVATE_KEY": "0x" + "z" * 64})
        self.assertFalse(cfg["signing_ready"])
        self.assertIsNone(cfg["buyer_address"])

    def test_payment_from_response_headers(self) -> None:
        import httpx

        response = httpx.Response(
            200,
            headers={
                "receipt": "r1",
                "payment-response": "p1",
                "x-credit-applied": "0.002",
            },
        )
        pay = payment_from_response(response)
        self.assertEqual(pay["receipt"], "r1")
        self.assertEqual(pay["payment_response"], "p1")
        self.assertEqual(pay["credit_applied"], "0.002")


if __name__ == "__main__":
    unittest.main()
