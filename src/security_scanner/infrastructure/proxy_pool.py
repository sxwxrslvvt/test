"""Proxy pool with rotation for handling IP blocking responses."""

from __future__ import annotations

from itertools import cycle


class ProxyPool:
    """Round-robin proxy provider with failure-triggered rotation."""

    def __init__(self, proxies: list[str]) -> None:
        self._proxies = proxies
        self._cycle = cycle(proxies) if proxies else None
        self._current: str | None = None

    @property
    def current(self) -> str | None:
        """Return currently selected proxy."""

        return self._current

    def next(self) -> str | None:
        """Rotate and return next proxy if available."""

        if self._cycle is None:
            self._current = None
            return None
        self._current = next(self._cycle)
        return self._current

    def handle_blocking_status(self, status_code: int) -> str | None:
        """Rotate proxy when server returns likely blocking statuses."""

        if status_code in {403, 429}:
            return self.next()
        return self._current
