"""MySQL client for the Excellence Standards database.

Replaces the earlier HTTP-to-excellence_export.php approach because
SiteGround's sgcaptcha was challenging Render's IPs and returning HTML
redirect pages instead of CSV. Direct MySQL is simpler, faster (no CSV
parsing, server-side WHERE), and reuses the existing MySQL Remote Access
whitelist flow.

Environment variables required:
    MYSQL_HOST          - haleglobal.com (or IP)
    MYSQL_PORT          - defaults to 3306
    MYSQL_DATABASE      - e.g. dbzyh4pyqfo0dq
    MYSQL_USER          - database user
    MYSQL_PASSWORD      - database password

Tables this module reads (but never writes):
    Lkup_Key                - respondent index (columns: Key, HashKey, Key3,
                              Email, Name, Date, Survey, SuccessFlag, Domain)
    Answers_Non-Scorable    - free-text / non-scored answers per respondent
                              (Key3, QuestionNmbr, Answer, and optionally a
                              memo/date column)

All queries filter server-side by Key3. We never download full tables — a
departure from the PHP-endpoint approach that made us pull ~5 MB per run.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

log = logging.getLogger(__name__)


class ExcStdsConfigError(RuntimeError):
    """Raised when a required env var is missing."""


class ExcStdsFetchError(RuntimeError):
    """Raised when a query fails or returns unexpected shape."""


class RespondentLookupDiagnostic(RuntimeError):
    """Raised in place of a bare None-return to surface diagnostic context
    when a Key3 lookup fails. The server converts this into a detail-rich
    404 response so the caller can see what actually happened."""


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ExcStdsConfigError(f"Missing required env var: {name}")
    return value


def _connect() -> pymysql.connections.Connection:
    """Open a short-lived MySQL connection using env-var config.

    Caller is responsible for closing. Uses DictCursor so query results
    come back as dicts rather than tuples.
    """
    host = _require_env("MYSQL_HOST")
    user = _require_env("MYSQL_USER")
    password = _require_env("MYSQL_PASSWORD")
    database = _require_env("MYSQL_DATABASE")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def lookup_respondent(key3: str) -> dict[str, Any] | None:
    """Return the Lkup_Key row for a Key3, or None if not found."""
    sql = "SELECT * FROM `Lkup_Key` WHERE `Key3` = %s LIMIT 1"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (key3,))
            row = cur.fetchone()
    return row


def lookup_respondent_or_diagnose(key3: str) -> dict[str, Any]:
    """Wrap lookup_respondent with a diagnostic exception on miss.

    The diagnostic includes row counts and a sample of Key3 values in the
    table so we can distinguish (a) table empty, (b) table populated but
    no match for this specific Key3 — probably a typo.
    """
    hit = lookup_respondent(key3)
    if hit is not None:
        return hit

    # Miss — gather diagnostic context
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM `Lkup_Key`")
            total = cur.fetchone()
            total_rows = total["n"] if total else 0
            cur.execute("SELECT `Key3` FROM `Lkup_Key` ORDER BY `Date` DESC LIMIT 5")
            recent = [r["Key3"] for r in cur.fetchall()]
            # Substring search to catch whitespace / case issues
            cur.execute(
                "SELECT `Key3` FROM `Lkup_Key` WHERE LOWER(`Key3`) LIKE %s LIMIT 5",
                (f"%{key3.lower()}%",),
            )
            hits = [r["Key3"] for r in cur.fetchall()]

    detail = (
        f"Key3 {key3!r} not found in Lkup_Key. "
        f"total_rows={total_rows} "
        f"recent_key3s={recent} "
        f"substring_matches={hits}"
    )
    raise RespondentLookupDiagnostic(detail)


def fetch_text_answers(key3: str) -> list[dict[str, Any]]:
    """Return non-scorable answers for one respondent.

    Reads the Answers_Non-Scorable table (the PowerBI model's name for
    the table also exposed as `text` via the PHP endpoint). Server-side
    filtered by Key3.
    """
    sql = (
        "SELECT * FROM `Answers_Non-Scorable` "
        "WHERE `Key3` = %s "
        "ORDER BY `QuestionNmbr`"
    )
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (key3,))
            rows = list(cur.fetchall())
    return rows


def ping() -> dict[str, Any]:
    """Minimal connectivity + schema probe for debugging.

    Returns the row count of Lkup_Key and the columns on both tables.
    Used by diagnostic endpoints; not called in the normal pull flow.
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM `Lkup_Key`")
            lkup_count = cur.fetchone()
            cur.execute("DESCRIBE `Lkup_Key`")
            lkup_columns = [r["Field"] for r in cur.fetchall()]
            try:
                cur.execute("DESCRIBE `Answers_Non-Scorable`")
                ans_columns = [r["Field"] for r in cur.fetchall()]
            except pymysql.err.ProgrammingError as exc:
                ans_columns = [f"ERROR: {exc}"]
    return {
        "Lkup_Key_rows": lkup_count["n"] if lkup_count else 0,
        "Lkup_Key_columns": lkup_columns,
        "Answers_Non-Scorable_columns": ans_columns,
    }
