from __future__ import annotations

import httpx


def payment_from_response(response: httpx.Response) -> dict[str, str | None]:
    """Headers after a successful paid call (200) or on 402 quote."""
    return {
        "receipt": response.headers.get("receipt") or response.headers.get("RECEIPT"),
        "payment_response": (
            response.headers.get("payment-response")
            or response.headers.get("PAYMENT-RESPONSE")
            or response.headers.get("x-payment-response")
            or response.headers.get("X-PAYMENT-RESPONSE")
        ),
        "payment_required": (
            response.headers.get("payment-required")
            or response.headers.get("PAYMENT-REQUIRED")
        ),
        "credit_applied": response.headers.get("x-credit-applied")
        or response.headers.get("X-CREDIT-APPLIED"),
    }
