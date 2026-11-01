import unittest

from readfetch_client.feedback_validation import normalize_feedback


class FeedbackValidationTest(unittest.TestCase):
    def test_rejects_delivery_category(self) -> None:
        with self.assertRaises(ValueError):
            normalize_feedback("req-1", "delivery", "wrong lane")

    def test_requires_request_id(self) -> None:
        with self.assertRaises(ValueError):
            normalize_feedback("  ", "integration", "ok")

    def test_rejects_long_request_id(self) -> None:
        with self.assertRaises(ValueError):
            normalize_feedback("x" * 257, "integration", "ok")


if __name__ == "__main__":
    unittest.main()
