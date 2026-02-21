"""Core data models for the security scanner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ScanResult:
    """Represents the output of a single scan operation."""

    url: str
    status_code: int | None
    content_length: int | None
    response_time_ms: float
    final_url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BrowserRenderResult:
    """Represents result of browser-based rendering for JS-heavy pages."""

    url: str
    html: str
    title: str | None
    cookies: list[dict[str, Any]]
    local_storage: dict[str, str]
