"""Assemble the respondent xlsx workbook.

Tab structure matches what we produce by hand in DAX Studio today (see
Book1.xlsx from the Meriste build): one tab per query, plus a Non-Scorable
tab for the text-answer pull.
"""

from __future__ import annotations

import io
import logging
from typing import Any

from openpyxl import Workbook

log = logging.getLogger(__name__)


TAB_ORDER = [
    "L1",
    "L2",
    "Flags",
    "Skinny",
    "ImpactTop10",
    "TeachTop10",
    "Non-Scorable",
    "Metadata",
]


def _write_tab(wb: Workbook, name: str, rows: list[dict[str, Any]]) -> None:
    """Create a tab and populate it from a list of dicts.

    If rows is empty, the tab is created with a single 'empty' placeholder
    row so the hiring team doesn't see a blank tab and assume the pull
    failed. The placeholder row says 'no rows'.
    """
    ws = wb.create_sheet(title=name)
    if not rows:
        ws.append(["(no rows returned for this query)"])
        return
    columns = list(rows[0].keys())
    ws.append(columns)
    for row in rows:
        ws.append([row.get(col) for col in columns])


def build_workbook(pull: dict[str, list[dict[str, Any]]]) -> bytes:
    """Build an xlsx as bytes from a dict of tab_name -> rows.

    Tabs not in TAB_ORDER are appended after the standard ones, preserving
    insertion order.
    """
    wb = Workbook()
    # openpyxl creates a default "Sheet"; remove it.
    default = wb.active
    if default is not None:
        wb.remove(default)

    # Write known tabs in order, then anything extra
    for tab in TAB_ORDER:
        if tab in pull:
            _write_tab(wb, tab, pull[tab])
    for tab, rows in pull.items():
        if tab not in TAB_ORDER:
            _write_tab(wb, tab, rows)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
