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

## 3) Quick start (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## 4) Run

```bash
PYTHONPATH=src python -m security_scanner.interfaces.cli --config configs/example.yaml
```

Output is JSON list of results per URL (status code, final URL, response time, headers, errors).

## 5) Как запустить и проверить на сайте безопасно

> Важно: используйте только ваши домены или ресурсы с письменным разрешением.

### Вариант A (безопасная базовая проверка)
1. Оставьте `configs/example.yaml` как есть (там уже спокойные цели: `https://httpbin.org/get` и `https://example.com`).
2. Проверьте, что лимиты низкие:
   - `requests_per_second: 1`
   - `concurrency: 2`
3. Запустите команду из раздела **Run**.
4. Убедитесь, что в выводе есть `status_code` (например, `200`) и нет критических ошибок в `errors`.

### Вариант B (ваш тестовый стенд)
1. Поднимите собственный тестовый сайт (например, staging).
2. Замените `targets` в YAML на ваш URL.
3. Для строгой этики оставьте `obey_robots_txt: true`.
4. Если тест согласован и нужен специальный сценарий, можно временно отключить robots-проверку только для вашего стенда.

### Что делать, если сразу 403/429
- Добавьте рабочие прокси в `proxies`.
- Уменьшите `requests_per_second` и `concurrency`.
- Проверьте, не блокирует ли WAF user-agent/гео/IP.

## 6) Precautions

1. Use only for assets you own or have written authorization to test.
2. Keep `requests_per_second` low and `concurrency` conservative.
3. Keep `obey_robots_txt: true` unless running approved internal tests.
4. Never use this tool for brute-force or denial-of-service activity.
5. Store proxy credentials and tokens securely (vault/secret manager), not in VCS.
