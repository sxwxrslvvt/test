"""Session state management for cookies/localStorage/token context."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionState:
    """Mutable state shared across HTTP and browser scanners."""

    cookies: dict[str, str] = field(default_factory=dict)
    local_storage: dict[str, str] = field(default_factory=dict)
    auth_token: str | None = None

    def as_cookie_header(self) -> str:
        """Format cookies as HTTP Cookie header value."""

        return "; ".join(f"{key}={value}" for key, value in self.cookies.items())
