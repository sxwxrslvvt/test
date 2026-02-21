"""robots.txt fetching and matching utilities."""

from __future__ import annotations

import urllib.robotparser
from urllib.parse import urljoin, urlparse

import httpx


class RobotsPolicy:
    """Evaluates if URL can be requested for a specific user-agent."""

    def __init__(self) -> None:
        self._parsers: dict[str, urllib.robotparser.RobotFileParser] = {}

    async def can_fetch(self, url: str, user_agent: str) -> bool:
        """Return True if robots policy allows fetching URL."""

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._parsers:
            robots_url = urljoin(base, "/robots.txt")
            parser = urllib.robotparser.RobotFileParser()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(robots_url)
                parser.parse(response.text.splitlines())
            except Exception:
                # Fail-open for availability in controlled testing labs.
                return True
            self._parsers[base] = parser

        return self._parsers[base].can_fetch(user_agent, url)
