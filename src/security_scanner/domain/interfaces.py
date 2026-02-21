"""Abstract interfaces for pluggable anti-bot handling components."""

from __future__ import annotations

from abc import ABC, abstractmethod


class CaptchaSolver(ABC):
    """Defines CAPTCHA solving integration contract."""

    @abstractmethod
    async def solve(self, page_url: str, site_key: str | None = None) -> str | None:
        """Return CAPTCHA token if solved, else None."""


class ManualCaptchaSolver(CaptchaSolver):
    """Safe default: do not auto-solve CAPTCHAs, require manual flow."""

    async def solve(self, page_url: str, site_key: str | None = None) -> str | None:
        """Always returns None to force manual intervention."""

        return None
