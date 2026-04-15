"""Orchestrator — Key3 in, xlsx bytes out.

Calls Power BI for the 6 scored queries and the Excellence Standards
MySQL database for respondent metadata and non-scorable text answers,
then assembles everything into one xlsx workbook.

Runs queries in parallel with a thread pool — both upstreams are I/O bound.
"""

from __future__ import annotations

import concurrent.futures as cf
import logging
from typing import Any

from .excel_output import build_workbook
from .excstds_api import (
    RespondentLookupDiagnostic,
    fetch_text_answers,
    lookup_respondent_or_diagnose,
)
from .powerbi import run_named_query

log = logging.getLogger(__name__)

POWERBI_QUERIES = [
    ("L1", "L1"),
    ("L2", "L2"),
    ("Flags", "flags"),
    ("Skinny", "skinny"),
    ("ImpactTop10", "impact_top10"),
    ("TeachTop10", "teach_top10"),
]


class RespondentNotFound(RuntimeError):
    """Raised when the Key3 is not present in Lkup_Key."""


def pull_respondent(key3: str) -> bytes:
    """Run the full pipeline for one Key3 and return xlsx bytes.

    Raises RespondentNotFound if Key3 isn't in Lkup_Key (usually a typo).
    The RespondentNotFound message includes a diagnostic string so the
    caller can tell lookup_miss apart from fetch_failure.
    """
    # Validate up front — if the Key3 isn't real, there's no point hitting PBI.
    try:
        metadata = lookup_respondent_or_diagnose(key3)
    except RespondentLookupDiagnostic as exc:
        raise RespondentNotFound(str(exc)) from exc

    pull: dict[str, list[dict[str, Any]]] = {
        "Metadata": [metadata],
    }

    # Fan out the six Power BI queries and the text-answer pull in parallel.
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        pbi_futures = {
            pool.submit(run_named_query, dax_name, key3=key3): tab_name
            for tab_name, dax_name in POWERBI_QUERIES
        }
        text_future = pool.submit(fetch_text_answers, key3)

        for fut in cf.as_completed(pbi_futures):
            tab = pbi_futures[fut]
            try:
                pull[tab] = fut.result()
            except Exception as exc:  # noqa: BLE001
                log.exception("Query %s failed", tab)
                pull[tab] = [{"error": str(exc)}]

        try:
            pull["Non-Scorable"] = text_future.result()
        except Exception as exc:  # noqa: BLE001
            log.exception("Non-Scorable fetch failed")
            pull["Non-Scorable"] = [{"error": str(exc)}]

    return build_workbook(pull)
