"""HTTP client for haleglobal.com/excellence_export.php.

The PHP endpoint returns CSV for three tables: Lkup_Key, scores, text. We use
it to pull respondent metadata and non-scorable answers — the computed
scoring lives in Power BI, not here.

Environment variables required:
    EXCSTDS_EXPORT_BASE   - Default: https://haleglobal.com/excellence_export.php
    EXCSTDS_EXPORT_TOKEN  - Auth token (passed as a query parameter)

The token is a query parameter in the upstream design, not a header. This is
a known weakness of the upstream endpoint but changing it is out of scope
for this pipeline.
"""

from __future__ import annotations

import csv
import io
import logging
import os
from typing import Any, Iterable

import requests

log = logging.getLogger(__name__)

DEFAULT_BASE = "https://haleglobal.com/excellence_export.php"

VALID_TABLES = frozenset({"Lkup_Key", "scores", "text"})

# haleglobal.com's WAF returns 403 to requests from Python's default
# User-Agent. Send a realistic UA so the request is accepted. This value
# rotates occasionally; keep it close to a real browser or a common
# HTTP client like curl. Anything but "python-requests/..." works today.
_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


class ExcStdsConfigError(RuntimeError):
    """Raised when a required env var is missing."""


class ExcStdsFetchError(RuntimeError):
    """Raised when the PHP endpoint returns a non-2xx response."""


def _config() -> tuple[str, str]:
    base = os.getenv("EXCSTDS_EXPORT_BASE", DEFAULT_BASE)
    token = os.getenv("EXCSTDS_EXPORT_TOKEN")
    if not token:
        raise ExcStdsConfigError("Missing required env var: EXCSTDS_EXPORT_TOKEN")
    return base, token


def fetch_table(table: str, *, timeout: int = 60) -> list[dict[str, str]]:
    """Fetch a full table from the export endpoint as a list of dicts.

    The endpoint does not support server-side filtering by Key3; the full
    table is returned and callers filter client-side. Sizes observed in
    April 2026: Lkup_Key ~170 KB, scores ~4.5 MB, text ~900 KB.
    """
    if table not in VALID_TABLES:
        raise ValueError(f"Unknown table: {table!r}. Allowed: {sorted(VALID_TABLES)}")
    base, token = _config()
    params = {"token": token, "table": table}
    log.debug("GET %s table=%s", base, table)
    resp = requests.get(
        base,
        params=params,
        timeout=timeout,
        allow_redirects=True,
        headers=_REQUEST_HEADERS,
    )
    if not resp.ok:
        raise ExcStdsFetchError(f"{base} table={table} returned {resp.status_code}")
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


def filter_by_key3(rows: Iterable[dict[str, Any]], key3: str) -> list[dict[str, Any]]:
    """Client-side filter — the PHP endpoint doesn't support WHERE clauses."""
    return [row for row in rows if row.get("Key3") == key3]


def lookup_respondent(key3: str) -> dict[str, str] | None:
    """Return the Lkup_Key row for a Key3, or None if not found.

    Logs diagnostic info on miss so we can distinguish "endpoint returned
    nothing" from "endpoint returned data but no match."
    """
    rows = fetch_table("Lkup_Key")
    log.info("Lkup_Key returned %d rows", len(rows))
    if rows:
        sample_columns = list(rows[0].keys())
        log.info("Lkup_Key columns: %s", sample_columns)
        # Is our target there by substring (to catch whitespace / case issues)?
        needle = key3.lower()
        hits = [r.get("Key3") for r in rows if needle in str(r.get("Key3", "")).lower()]
        if hits:
            log.info("Found %d rows containing %r: first=%r", len(hits), needle, hits[0])
    for row in rows:
        if row.get("Key3") == key3:
            return row
    return None


class RespondentLookupDiagnostic(RuntimeError):
    """Raised in place of a bare None-return to surface diagnostic context
    when a Key3 lookup fails. The server converts this into a detail-rich
    404 response so the caller can see what actually happened."""


def lookup_respondent_or_diagnose(key3: str) -> dict[str, str]:
    """Wrap lookup_respondent with a diagnostic exception on miss."""
    rows = fetch_table("Lkup_Key")
    for row in rows:
        if row.get("Key3") == key3:
            return row
    # Miss — build diagnostic payload
    sample_key3s = [r.get("Key3") for r in rows[:3]]
    needle = key3.lower()
    hits = [r.get("Key3") for r in rows if needle in str(r.get("Key3", "")).lower()]
    detail = (
        f"Key3 {key3!r} not found. fetched {len(rows)} rows from Lkup_Key. "
        f"columns={list(rows[0].keys()) if rows else []}. "
        f"first 3 Key3 values={sample_key3s}. "
        f"substring hits on {needle!r}={hits[:5]}"
    )
    raise RespondentLookupDiagnostic(detail)


def fetch_text_answers(key3: str) -> list[dict[str, str]]:
    """Return only the non-scorable answers for a single respondent."""
    rows = fetch_table("text")
    return filter_by_key3(rows, key3)


def fetch_scored_answers(key3: str) -> list[dict[str, str]]:
    """Return only the scored (1-5) answers for a single respondent.

    Mostly redundant with the Power BI 'skinny' pull, which also includes
    Impact/Teach ranks and Z_Delta. Kept for corroboration / debugging.
    """
    rows = fetch_table("scores")
    return filter_by_key3(rows, key3)
