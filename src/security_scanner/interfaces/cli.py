"""CLI entrypoint for the security scanner."""

# ============================================================================
# DISCLAIMER / LEGAL NOTICE
# This tool is strictly for authorized security auditing, resilience testing,
# and monitoring of web resources that you own or for which you have explicit
# written permission. Unauthorized scanning may violate laws, regulations,
# contracts, and organizational policies. The authors/operators are responsible
# for lawful and ethical use. Do NOT use this tool for DDoS, brute-force login
# attacks, credential stuffing, or attacks against third-party infrastructure.
# ============================================================================

from __future__ import annotations

import argparse
import asyncio
import json

from security_scanner.application.scanner_service import ScannerService
from security_scanner.core.config import load_config
from security_scanner.infrastructure.logging_setup import configure_logging


def build_parser() -> argparse.ArgumentParser:
    """Create command-line parser."""

    parser = argparse.ArgumentParser(description="Modular security web scanner")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    return parser


async def _run(config_path: str) -> None:
    config = load_config(config_path)
    service = ScannerService(config)
    results = await service.run()
    print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))


def main() -> None:
    """Program entry point."""

    configure_logging()
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(_run(args.config))


if __name__ == "__main__":
    main()
