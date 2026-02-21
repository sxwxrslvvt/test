"""Browser renderer for JS challenges and dynamic content."""

from __future__ import annotations

import structlog
from playwright.async_api import BrowserContext, Page, async_playwright
from playwright_stealth import stealth_async

from security_scanner.core.config import ScannerConfig
from security_scanner.core.models import BrowserRenderResult
from security_scanner.infrastructure.session_store import SessionState

logger = structlog.get_logger(__name__)


class BrowserRenderer:
    """Playwright-based renderer with stealth and explicit waits."""

    def __init__(self, config: ScannerConfig, session_state: SessionState) -> None:
        self._config = config
        self._session = session_state

    async def _prime_context(self, context: BrowserContext) -> None:
        if self._session.cookies:
            await context.add_cookies(
                [
                    {
                        "name": name,
                        "value": value,
                        "url": str(self._config.targets[0]),
                    }
                    for name, value in self._session.cookies.items()
                ]
            )

    async def _set_local_storage(self, page: Page) -> None:
        if self._session.local_storage:
            await page.evaluate(
                """
                (entries) => {
                    for (const [k, v] of Object.entries(entries)) {
                        localStorage.setItem(k, v);
                    }
                }
                """,
                self._session.local_storage,
            )

    async def render(self, url: str) -> BrowserRenderResult:
        """Open page in stealth context and capture rendered DOM state."""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            await self._prime_context(context)
            page = await context.new_page()
            await stealth_async(page)
            await self._set_local_storage(page)

            await page.goto(url, wait_until="domcontentloaded")
            if self._config.browser_wait_selector:
                await page.wait_for_selector(self._config.browser_wait_selector, timeout=15_000)
            else:
                await page.wait_for_load_state("networkidle")

            storage = await page.evaluate(
                """() => {
                    const out = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        out[key] = localStorage.getItem(key);
                    }
                    return out;
                }"""
            )
            cookies = await context.cookies()
            html = await page.content()
            title = await page.title()
            await browser.close()

        logger.info("browser_render", url=url, title=title)
        return BrowserRenderResult(
            url=url,
            html=html,
            title=title,
            cookies=cookies,
            local_storage=storage,
        )
