#!/usr/bin/env python3
"""
Validate Trafficinator configuration and optional Matomo connectivity.

Usage:
    python tools/validate_config.py [--env-file FILE] [--skip-connection] [--timeout SECONDS]

The script loads environment variables (current process + optional env file),
validates them using the existing Control UI validators, and optionally tests
Matomo connectivity before starting the load generator.
"""

import argparse
import asyncio
import os
import sys
from typing import Dict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTROL_UI_PATH = os.path.join(ROOT, "control-ui")

if CONTROL_UI_PATH not in sys.path:
    sys.path.append(CONTROL_UI_PATH)

from config_validator import ConfigValidator  # type: ignore  # noqa: E402

ENV_TO_CONFIG_KEY = {
    "MATOMO_URL": "matomo_url",
    "MATOMO_SITE_ID": "matomo_site_id",
    "MATOMO_TOKEN_AUTH": "matomo_token_auth",
    "TARGET_VISITS_PER_DAY": "target_visits_per_day",
    "PAGEVIEWS_MIN": "pageviews_min",
    "PAGEVIEWS_MAX": "pageviews_max",
    "CONCURRENCY": "concurrency",
    "PAUSE_BETWEEN_PVS_MIN": "pause_between_pvs_min",
    "PAUSE_BETWEEN_PVS_MAX": "pause_between_pvs_max",
    "AUTO_STOP_AFTER_HOURS": "auto_stop_after_hours",
    "MAX_TOTAL_VISITS": "max_total_visits",
    "SITESEARCH_PROBABILITY": "sitesearch_probability",
    "VISIT_DURATION_MIN": "visit_duration_min",
    "VISIT_DURATION_MAX": "visit_duration_max",
    "OUTLINKS_PROBABILITY": "outlinks_probability",
    "DOWNLOADS_PROBABILITY": "downloads_probability",
    "CLICK_EVENTS_PROBABILITY": "click_events_probability",
    "RANDOM_EVENTS_PROBABILITY": "random_events_probability",
    "DIRECT_TRAFFIC_PROBABILITY": "direct_traffic_probability",
    "RANDOMIZE_VISITOR_COUNTRIES": "randomize_visitor_countries",
    "ECOMMERCE_PROBABILITY": "ecommerce_probability",
    "ECOMMERCE_ORDER_VALUE_MIN": "ecommerce_order_value_min",
    "ECOMMERCE_ORDER_VALUE_MAX": "ecommerce_order_value_max",
    "ECOMMERCE_CURRENCY": "ecommerce_currency",
    "TIMEZONE": "timezone",
}


def parse_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def build_config(env: Dict[str, str]) -> Dict[str, str]:
    config: Dict[str, str] = {}
    for env_key, config_key in ENV_TO_CONFIG_KEY.items():
        if env_key in env:
            config[config_key] = env[env_key]
    return config


async def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Trafficinator configuration.")
    parser.add_argument(
        "--env-file",
        help="Optional .env-style file to read additional environment variables from.",
    )
    parser.add_argument(
        "--skip-connection",
        action="store_true",
        help="Skip Matomo connectivity test (validation only).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for Matomo connectivity test (default: 10).",
    )
    args = parser.parse_args()

    env = dict(os.environ)
    if args.env_file:
        env.update(parse_env_file(args.env_file))

    config = build_config(env)
    validation = ConfigValidator.validate_config(config)

    print("Configuration validation:")
    if validation.valid:
        print("  ✅ Valid configuration")
    else:
        print("  ❌ Configuration invalid")
        for error in validation.errors:
            print(f"    - [{error.severity.upper()}] {error.field}: {error.message}")
        return 1

    if validation.warnings:
        for warning in validation.warnings:
            print(f"  ⚠️  {warning.field}: {warning.message}")

    if args.skip_connection:
        return 0

    matomo_url = config.get("matomo_url")
    if not matomo_url:
        print("  ℹ️  Skipping connectivity test (MATOMO_URL not provided).")
        return 0

    print(f"\nTesting Matomo connectivity ({matomo_url})...")
    try:
        result = await ConfigValidator.test_matomo_connection(matomo_url, args.timeout)
    except Exception as exc:  # pragma: no cover
        print(f"  ❌ Connectivity test failed: {exc}")
        return 1

    if result.success:
        rtt = result.response_time_ms
        print(f"  ✅ Matomo reachable (response time: {rtt:.0f} ms)" if rtt else "  ✅ Matomo reachable")
        if result.message:
            print(f"     {result.message}")
        return 0

    print(f"  ❌ Matomo connectivity check failed: {result.message or result.error}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
