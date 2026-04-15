"""Thin local client — calls the Render pipeline and saves the xlsx.

Usage:
    python scripts/pull_local.py 20260414.mnm.riggs@gmail.com

Reads the Render URL and API token from the local .env file. The xlsx is
saved to "{OUTPUT_ROOT}/{key3}/data.xlsx" where OUTPUT_ROOT is taken from
the LOCAL_RESPONDENT_ROOT env var (default: a sibling folder named
'respondents').

This client knows nothing about Power BI or MySQL auth — all that lives on
the Render service. Local operator only needs the Render API token.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Pull respondent data via Render pipeline")
    parser.add_argument("key3", help='Respondent Key3, e.g. "20260414.mnm.riggs@gmail.com"')
    parser.add_argument(
        "--output-root",
        default=os.getenv("LOCAL_RESPONDENT_ROOT"),
        help="Directory under which to create <key3>/data.xlsx (default: $LOCAL_RESPONDENT_ROOT)",
    )
    parser.add_argument(
        "--pipeline-url",
        default=os.getenv("PIPELINE_URL"),
        help="Base URL of the Render service (default: $PIPELINE_URL)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("PIPELINE_TIMEOUT", "180")),
        help="HTTP timeout in seconds (default: 180)",
    )
    args = parser.parse_args()

    if not args.pipeline_url:
        print("Error: PIPELINE_URL not set (in .env or --pipeline-url)", file=sys.stderr)
        return 2
    if not args.output_root:
        print("Error: LOCAL_RESPONDENT_ROOT not set (in .env or --output-root)", file=sys.stderr)
        return 2

    token = os.getenv("PIPELINE_API_TOKEN")
    if not token:
        print("Error: PIPELINE_API_TOKEN not set in .env", file=sys.stderr)
        return 2

    url = args.pipeline_url.rstrip("/") + "/v1/pull-respondent"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"POST {url} key3={args.key3}")
    resp = requests.post(url, json={"key3": args.key3}, headers=headers, timeout=args.timeout)
    if resp.status_code == 404:
        print(f"Key3 not found: {args.key3}", file=sys.stderr)
        return 1
    if not resp.ok:
        print(f"Error {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        return 1

    out_dir = Path(args.output_root) / args.key3
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.xlsx"
    out_path.write_bytes(resp.content)
    print(f"Saved {len(resp.content):,} bytes -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
