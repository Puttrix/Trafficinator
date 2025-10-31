#!/usr/bin/env python3
"""
Export funnel definitions from the Control UI to a JSON file.

Usage:
    python tools/export_funnels.py --api-base http://localhost:8000 --api-key change-me --output control-ui/data/funnels.json

This script calls the Control UI `/api/funnels` endpoint and dumps the current funnel
definitions into a JSON array suitable for the loader (`FUNNEL_CONFIG_PATH`).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def fetch_funnels(api_base: str, api_key: str) -> list:
    url = f"{api_base.rstrip('/')}/api/funnels"
    request = urllib.request.Request(url, headers={"X-API-Key": api_key})
    with urllib.request.urlopen(request) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected status code {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    funnels = payload.get("funnels", [])
    detailed = []
    for item in funnels:
        detail_url = f"{api_base.rstrip('/')}/api/funnels/{item['id']}"
        detail_req = urllib.request.Request(detail_url, headers={"X-API-Key": api_key})
        with urllib.request.urlopen(detail_req) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to fetch funnel {item['id']}: {resp.status}")
            detailed.append(json.loads(resp.read().decode("utf-8")))
    return detailed


def main() -> int:
    parser = argparse.ArgumentParser(description="Export funnels from Control UI to JSON")
    parser.add_argument("--api-base", default="http://localhost:8000", help="Control UI base URL (default: http://localhost:8000)")
    parser.add_argument("--api-key", required=True, help="API key for Control UI")
    parser.add_argument("--output", required=True, help="Path to write JSON output (e.g., control-ui/data/funnels.json)")
    args = parser.parse_args()

    try:
        funnels = fetch_funnels(args.api_base, args.api_key)
    except urllib.error.HTTPError as exc:
        print(f"❌ HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"❌ Connection error: {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"❌ Unexpected error: {exc}", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    export_payload = []
    for funnel in funnels:
        config = funnel.get("config", {})
        export_payload.append(
            {
                "name": funnel.get("name"),
                "description": funnel.get("description"),
                "probability": config.get("probability", 0.0),
                "priority": config.get("priority", 0),
                "enabled": config.get("enabled", True),
                "exit_after_completion": config.get("exit_after_completion", True),
                "steps": config.get("steps", []),
            }
        )

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(export_payload, handle, indent=2)

    print(f"✅ Exported {len(export_payload)} funnel(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
