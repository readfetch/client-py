# readfetch-client

Python x402 REST client for [readfetch.com](https://readfetch.com) — all published catalog routes plus feedback and claims.

Checkout: `tools/client-py`. GitHub: `./scripts/publish-client-py.sh`.

## Install

```bash
pip install readfetch-client
```

## Use

```bash
export EVM_PRIVATE_KEY=0x…   # paid routes only
```

```python
import asyncio
from readfetch_client import (
    call,
    probe_with_meta,
    readfetch_text,
    readfetch_map,
    readfetch_crawl_status,
    submit_feedback,
    submit_claim,
)

async def main():
    check, request_id = await probe_with_meta("https://example.com")
    if not check.get("challenge"):
        await readfetch_text("https://example.com")
    await readfetch_map({"url": "https://example.com", "max_urls": 20})
    job = await call("crawl", {"url": "https://example.com", "max_pages": 3})
    await readfetch_crawl_status(job["id"])
    if request_id:
        await submit_feedback(request_id, "integration", "…")

asyncio.run(main())
```

Named helpers: `readfetch_text`, `readfetch_map`, `readfetch_scrape`, `readfetch_residential`, `readfetch_fetch`, `readfetch_batch`, `readfetch_pdf`, `readfetch_section`, `readfetch_diff`, `readfetch_screenshot`, `readfetch_search`, `readfetch_crawl`, `readfetch_crawl_status`. Generic: `await call("search", {"query": "…"})`.

## Payment (x402)

Paid routes use **`x402` + `x402HttpxClient`**: on **402**, the client signs and retries. No key is required for quotes.

```python
from readfetch_client import (
    payment_config,
    quote,
    call_with_meta,
    x402_http_client,
)

print(payment_config())  # base_url, network, max_payment_usd, buyer_address, signing_ready

q = await quote("text", {"url": "https://example.com"})  # 402 + payment_required

meta = await call_with_meta("text", {"url": "https://example.com"})
# meta["data"], meta["request_id"], meta["payment"] (receipt, payment_response, …)

async with x402_http_client() as http:
    ...
```

`pay(name, body)` aliases `call()` for paid endpoints.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `EVM_PRIVATE_KEY` / `X402_BUYER_KEY` | — | Required before paid calls |
| `READFETCH_BASE_URL` | `https://readfetch.com` | Production host only unless dev |
| `READFETCH_MAX_PAYMENT_USD` | `1` | Per-payment spend cap |
| `READFETCH_DEV=1` | off | Allow local base URL for integration tests |

MCP: [`@readfetch/mcp-x402-proxy@0.1.12`](https://github.com/readfetch/mcp-x402-proxy). Feedback: [docs#feedback](https://readfetch.com/docs#feedback).
