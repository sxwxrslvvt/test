"""Configuration models and loader."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, HttpUrl


class RetryConfig(BaseModel):
    """Retry behavior configuration."""

    max_attempts: int = 4
    base_backoff_seconds: float = 0.5
    max_backoff_seconds: float = 8.0


class ScannerConfig(BaseModel):
    """Main scanner configuration object."""

    disclaimer_acknowledged: bool = False
    targets: list[HttpUrl]
    concurrency: int = 5
    requests_per_second: float = 2.0
    timeout_seconds: float = 20.0
    obey_robots_txt: bool = True
    use_browser_fallback: bool = True
    browser_wait_selector: str | None = None
    retry: RetryConfig = Field(default_factory=RetryConfig)
    proxies: list[str] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    auth_token: str | None = None
    referers: list[str] = Field(default_factory=list)
    origins: list[str] = Field(default_factory=list)


def load_config(path: str | Path) -> ScannerConfig:
    """Load scanner config from YAML file."""

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ScannerConfig.model_validate(data)
