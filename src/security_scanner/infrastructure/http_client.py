"""Asynchronous HTTP scanner with retry/backoff, RPS limits, and evasive headers."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any

import httpx
import structlog
from aiolimiter import AsyncLimiter
from fake_useragent import UserAgent

from security_scanner.core.config import ScannerConfig
from security_scanner.core.models import ScanResult
from security_scanner.infrastructure.proxy_pool import ProxyPool
from security_scanner.infrastructure.robots import RobotsPolicy
from security_scanner.infrastructure.session_store import SessionState

logger = structlog.get_logger(__name__)


class AsyncHTTPScanner:
    """Core async HTTP scanner implementation."""

    def __init__(self, config: ScannerConfig, session_state: SessionState, proxy_pool: ProxyPool) -> None:
        self._config = config
        self._session = session_state
        self._proxy_pool = proxy_pool
        self._robots = RobotsPolicy()
        self._ua = UserAgent()
        self._limiter = AsyncLimiter(max_rate=max(1, int(config.requests_per_second)), time_period=1)
        self._sem = asyncio.Semaphore(config.concurrency)

    def _build_headers(self) -> dict[str, str]:
        headers = dict(self._config.headers)
        headers["User-Agent"] = self._ua.random
        if self._session.auth_token:
            headers["Authorization"] = f"Bearer {self._session.auth_token}"
        if self._session.cookies:
            headers["Cookie"] = self._session.as_cookie_header()
        if self._config.referers:
            headers["Referer"] = random.choice(self._config.referers)
        if self._config.origins:
            headers["Origin"] = random.choice(self._config.origins)
        return headers

    async def fetch(self, url: str) -> ScanResult:
        """Fetch URL with retry/backoff/proxy-rotation and log all attempts."""

        async with self._sem:
            if self._config.obey_robots_txt:
                sample_ua = self._build_headers()["User-Agent"]
                if not await self._robots.can_fetch(url, sample_ua):
                    return ScanResult(
                        url=url,
                        status_code=None,
                        content_length=None,
                        response_time_ms=0,
                        errors=["Blocked by robots.txt policy"],
                    )

            for attempt in range(1, self._config.retry.max_attempts + 1):
                async with self._limiter:
                    await asyncio.sleep(random.uniform(0.15, 0.8))
                    proxy = self._proxy_pool.current or self._proxy_pool.next()
                    headers = self._build_headers()
                    start = time.perf_counter()
                    try:
                        async with httpx.AsyncClient(timeout=self._config.timeout_seconds, follow_redirects=True) as client:
                            response = await client.get(url, headers=headers, proxy=proxy)
                        elapsed = (time.perf_counter() - start) * 1000

                        for cookie in response.cookies.jar:
                            self._session.cookies[cookie.name] = cookie.value

                        self._proxy_pool.handle_blocking_status(response.status_code)

                        logger.info(
                            "http_fetch",
                            url=url,
                            status=response.status_code,
                            attempt=attempt,
                            proxy=proxy,
                            elapsed_ms=round(elapsed, 2),
                        )
                        return ScanResult(
                            url=url,
                            status_code=response.status_code,
                            content_length=len(response.content),
                            response_time_ms=elapsed,
                            final_url=str(response.url),
                            headers={k: v for k, v in response.headers.items()},
                        )
                    except Exception as exc:
                        backoff = min(
                            self._config.retry.base_backoff_seconds * (2 ** (attempt - 1)),
                            self._config.retry.max_backoff_seconds,
                        )
                        logger.warning(
                            "http_fetch_error",
                            url=url,
                            attempt=attempt,
                            error=str(exc),
                            next_backoff=backoff,
                        )
                        if attempt < self._config.retry.max_attempts:
                            await asyncio.sleep(backoff)
                        else:
                            return ScanResult(
                                url=url,
                                status_code=None,
                                content_length=None,
                                response_time_ms=0,
                                errors=[str(exc)],
                                metadata={"attempts": attempt},
                            )

        return ScanResult(url=url, status_code=None, content_length=None, response_time_ms=0)
