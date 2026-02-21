"""Application orchestrator for HTTP + browser fallback workflows."""

from __future__ import annotations

import asyncio

import structlog

from security_scanner.core.config import ScannerConfig
from security_scanner.core.models import ScanResult
from security_scanner.domain.interfaces import CaptchaSolver, ManualCaptchaSolver
from security_scanner.infrastructure.browser_renderer import BrowserRenderer
from security_scanner.infrastructure.http_client import AsyncHTTPScanner
from security_scanner.infrastructure.proxy_pool import ProxyPool
from security_scanner.infrastructure.session_store import SessionState

logger = structlog.get_logger(__name__)


class ScannerService:
    """Coordinates scanning, captcha strategy, and dynamic rendering fallback."""

    def __init__(self, config: ScannerConfig, captcha_solver: CaptchaSolver | None = None) -> None:
        self._config = config
        self._session = SessionState(auth_token=config.auth_token)
        self._proxy_pool = ProxyPool(config.proxies)
        self._http = AsyncHTTPScanner(config, self._session, self._proxy_pool)
        self._browser = BrowserRenderer(config, self._session)
        self._captcha_solver = captcha_solver or ManualCaptchaSolver()

    async def _scan_single(self, url: str) -> ScanResult:
        result = await self._http.fetch(url)
        if result.status_code in {401, 403} and self._config.use_browser_fallback:
            # Common signal that anti-bot controls triggered challenge page.
            rendered = await self._browser.render(url)
            result.metadata["browser_title"] = rendered.title
            result.metadata["rendered_html_length"] = len(rendered.html)

        if result.status_code == 403:
            # CAPTCHA placeholder integration point.
            captcha_token = await self._captcha_solver.solve(page_url=url)
            result.metadata["captcha_token_received"] = bool(captcha_token)

        return result

    async def run(self) -> list[ScanResult]:
        """Run scan for all configured targets."""

        if not self._config.disclaimer_acknowledged:
            raise ValueError("Set disclaimer_acknowledged=true in config for authorized usage.")

        tasks = [self._scan_single(str(target)) for target in self._config.targets]
        results = await asyncio.gather(*tasks)
        logger.info("scan_finished", targets=len(tasks))
        return results
