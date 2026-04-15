"""Dev driver — run the pipeline locally (no Render) for testing.

Usage:
    python scripts/run_local.py 20260414.mnm.riggs@gmail.com

Requires all upstream secrets in the local .env file (same ones that go on
Render in production). Writes output to the local respondent folder.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Make src/ importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pipeline.runner import RespondentNotFound, pull_respondent  # noqa: E402


def main() -> int:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="Run pipeline locally (no Render)")
    parser.add_argument("key3", help="Respondent Key3")
    parser.add_argument(
        "--output-root",
        default=os.getenv("LOCAL_RESPONDENT_ROOT"),
        help="Directory under which to create <key3>/data.xlsx",
    )
    args = parser.parse_args()

    if not args.output_root:
        print("Error: LOCAL_RESPONDENT_ROOT not set", file=sys.stderr)
        return 2

    try:
        xlsx_bytes = pull_respondent(args.key3)
    except RespondentNotFound as exc:
        print(f"Not found: {exc}", file=sys.stderr)
        return 1

    out_dir = Path(args.output_root) / args.key3
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.xlsx"
    out_path.write_bytes(xlsx_bytes)
    print(f"Saved {len(xlsx_bytes):,} bytes -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
