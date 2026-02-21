# Universal Modular Web Security Scanner (Python 3.10+)

## 1) Architecture (Clean-ish layering)

```text
src/security_scanner/
  application/
    scanner_service.py        # Use-case orchestration (HTTP + browser fallback)
  core/
    config.py                 # Pydantic configuration models + loader
    models.py                 # Domain DTOs/results
  domain/
    interfaces.py             # CAPTCHA solver interface and safe default stub
  infrastructure/
    http_client.py            # Async HTTP scanner, retries, proxy rotation, RPS
    browser_renderer.py       # Playwright renderer, stealth, explicit waits
    proxy_pool.py             # IP/proxy rotation strategy
    robots.py                 # robots.txt policy checks
    session_store.py          # Cookies/localStorage/token state
    logging_setup.py          # JSON structured logging
  interfaces/
    cli.py                    # CLI entrypoint + legal disclaimer
configs/
  example.yaml                # Scanner configuration example
requirements.txt
```

## 2) Implemented security-auditing capabilities

- **Session management:** cookies, localStorage, bearer token support.
- **Basic anti-bot bypass (for legal testing):** user-agent rotation, dynamic headers (`Referer`, `Origin`), randomized delays.
- **Proxy support:** HTTP/SOCKS5 proxy list, rotation on 403/429 (IP blocking signals).
- **Error handling:** exponential backoff retry strategy.
- **Structured logging:** JSON logs using `structlog`.
- **Ethics controls:** `robots.txt` compliance (toggle), hard RPS throttling.
- **JS challenges:** Playwright + `playwright-stealth`.
- **Fingerprinting mitigation:** stealth mode + randomized request profile.
- **Dynamic content:** explicit waits (`wait_for_selector` / `networkidle`).
- **CAPTCHA strategy:** pluggable interface + safe manual solver stub.

## 3) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## 4) Run

```bash
PYTHONPATH=src python -m security_scanner.interfaces.cli --config configs/example.yaml
```

## 5) Precautions

1. Use only for assets you own or have written authorization to test.
2. Keep `requests_per_second` low and `concurrency` conservative.
3. Keep `obey_robots_txt: true` unless running approved internal tests.
4. Never use this tool for brute-force or denial-of-service activity.
5. Store proxy credentials and tokens securely (vault/secret manager), not in VCS.
