from __future__ import annotations

FEEDBACK_CATEGORIES = frozenset({"integration", "docs", "site", "other"})
MAX_FEEDBACK_REQUEST_ID_LEN = 256


def normalize_feedback(
    request_id: str, category: str, message: str
) -> tuple[str, str, str]:
    rid = (request_id or "").strip()
    cat = (category or "").strip()
    msg = (message or "").strip()
    if not rid:
        raise ValueError("request_id is required")
    if len(rid) > MAX_FEEDBACK_REQUEST_ID_LEN:
        raise ValueError(
            f"request_id exceeds {MAX_FEEDBACK_REQUEST_ID_LEN} characters"
        )
    if cat not in FEEDBACK_CATEGORIES:
        raise ValueError("category must be integration, docs, site, or other")
    if not msg or len(msg) > 500:
        raise ValueError("message is required (max 500 characters)")
    return rid, cat, msg
