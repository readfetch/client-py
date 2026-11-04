# readfetch-client

Python x402 REST client for [readfetch.com](https://readfetch.com) — all published catalog routes plus feedback and claims.

Checkout: `tools/client-py`. GitHub: `./scripts/publish-client-py.sh`.

## Install

```bash
pip install readfetch-client
```

## Use

```python
from readfetch import Client

rf = Client(private_key="0x…")  # funded account with USDC on Base; or export EVM_PRIVATE_KEY
result = rf.fetch("https://example.com/article")
print(result["text"])
```

`fetch()` calls **`/v1/text`** (article `text` in the JSON). x402 **402 → sign → retry** is automatic. Inside asyncio, use `await rf.text(url)` instead of sync `fetch()`.

Lower-level API (async helpers, every catalog route):

```bash
export EVM_PRIVATE_KEY=0x…   # paid routes only
```

```python
import asyncio
from readfetch import Client

async def main():
    rf = Client()
    check = await rf.probe_async("https://example.com")
    if not check.get("challenge"):
        await rf.fetch_async("https://example.com")
    page = await rf.call("map", {"url": "https://example.com", "limit": 20})
    job = await rf.call("crawl", {"url": "https://example.com", "max_pages": 3})
    await rf.call("crawl_status", None, path_params={"id": job["job_id"]})

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

MCP: [`@readfetch/mcp-x402-proxy@0.1.14`](https://github.com/readfetch/mcp-x402-proxy). Feedback: [docs#feedback](https://readfetch.com/docs#feedback).
