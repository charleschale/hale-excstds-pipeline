"""MySQL client for the Excellence Standards database.

Replaces the earlier HTTP-to-excellence_export.php approach because
SiteGround's sgcaptcha was challenging Render's IPs and returning HTML
redirect pages instead of CSV.

This module mirrors the logic in excellence_export.php but reads from
MySQL directly. The PHP file was the reference implementation; see
MEMORY: the wide table `excellence_survey_responses` has one row per
respondent with columns q104 (email), q105 (name), q106 (title), and
q<N> for each question answer. Key3 is derived on-the-fly as
YYYYMMDD.<email>. The PHP's virtual "Lkup_Key" and "text" tables are
reconstructions of this data in a long format.

Environment variables required:
    MYSQL_HOST          - haleglobal.com (or IP)
    MYSQL_PORT          - defaults to 3306
    MYSQL_DATABASE      - e.g. dbzyh4pyqfo0dq
    MYSQL_USER          - database user
    MYSQL_PASSWORD      - database password

Tables this module reads (but never writes):
    excellence_survey_responses  - wide table, one row per respondent
    excellence_questions          - question metadata, incl. IsScored flag
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

log = logging.getLogger(__name__)

# These column names mirror the hardcoded mapping in excellence_export.php.
# If the physical column names change in MySQL, update both files.
COL_EMAIL = "q104"
COL_NAME = "q105"
COL_TITLE = "q106"


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
    """Open a short-lived MySQL connection using env-var config."""
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


# --- Key3 parsing ---------------------------------------------------------

def _parse_key3(key3: str) -> tuple[str, str]:
    """Split Key3 into (YYYYMMDD, email).

    Key3 format (per excellence_export.php): YYYYMMDD.<email>
    Example: "20260414.mnm.riggs@gmail.com" -> ("20260414", "mnm.riggs@gmail.com")
    """
    if len(key3) < 10 or key3[8] != ".":
        raise ValueError(f"Invalid Key3 format: {key3!r}")
    date_part = key3[:8]
    email_part = key3[9:]
    if not date_part.isdigit():
        raise ValueError(f"Key3 date prefix not numeric: {key3!r}")
    return date_part, email_part


def _sql_date_from_key3_date(date_part: str) -> str:
    """Convert '20260414' to '2026-04-14' for SQL DATE() comparison."""
    return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"


# --- Lkup_Key derivation --------------------------------------------------

def _make_lkup_key_row(raw_row: dict[str, Any]) -> dict[str, Any]:
    """Given a raw excellence_survey_responses row, build the Lkup_Key-shaped
    dict that the PHP endpoint returns. Same field names, same derivations.
    """
    import datetime as dt  # local import: only needed here

    created: dt.datetime = raw_row["created_at"]
    email: str = raw_row.get(COL_EMAIL) or ""
    name: str = raw_row.get(COL_NAME) or ""

    # Key: email + M/D/YY
    key = f"{email}{created.month}/{created.day}/{created.strftime('%y')}"
    # HashKey: YYYYMMDD + first 6 chars of email
    hashkey = f"{created.strftime('%Y%m%d')}{email[:6]}"
    # Key3: YYYYMMDD.email
    key3 = f"{created.strftime('%Y%m%d')}.{email}"
    # Domain: everything after @
    domain = email.split("@", 1)[1] if "@" in email else ""

    return {
        "Key": key,
        "HashKey": hashkey,
        "Key3": key3,
        "Email": email,
        "Name": name,
        "Date": created.strftime("%m/%d/%Y"),
        "Survey": raw_row.get("source") or "",
        "SuccessFlag": raw_row.get("SuccessFlag") or "",
        "Domain": domain,
    }


def lookup_respondent(key3: str) -> dict[str, Any] | None:
    """Return the Lkup_Key-shaped dict for a Key3, or None if not found."""
    date_part, email = _parse_key3(key3)
    sql_date = _sql_date_from_key3_date(date_part)

    sql = f"""
        SELECT *
        FROM `excellence_survey_responses`
        WHERE `{COL_EMAIL}` = %s AND DATE(`created_at`) = %s
        ORDER BY `created_at` DESC
        LIMIT 1
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email, sql_date))
            raw = cur.fetchone()
    if raw is None:
        return None
    return _make_lkup_key_row(raw)


def lookup_respondent_or_diagnose(key3: str) -> dict[str, Any]:
    """Wrap lookup_respondent with a diagnostic exception on miss."""
    try:
        hit = lookup_respondent(key3)
    except ValueError as exc:
        raise RespondentLookupDiagnostic(f"Key3 malformed: {exc}") from exc
    if hit is not None:
        return hit

    date_part, email = _parse_key3(key3)
    sql_date = _sql_date_from_key3_date(date_part)

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM `excellence_survey_responses`"
            )
            total = cur.fetchone()["n"]
            # Try matching just the email, any date
            cur.execute(
                f"SELECT `{COL_EMAIL}` AS e, DATE(`created_at`) AS d "
                f"FROM `excellence_survey_responses` "
                f"WHERE `{COL_EMAIL}` = %s LIMIT 5",
                (email,),
            )
            email_hits = cur.fetchall()
            # Try matching just the date, any email
            cur.execute(
                f"SELECT `{COL_EMAIL}` AS e FROM `excellence_survey_responses` "
                f"WHERE DATE(`created_at`) = %s LIMIT 5",
                (sql_date,),
            )
            date_hits = [r["e"] for r in cur.fetchall()]

    detail = (
        f"Key3 {key3!r} not found. "
        f"parsed email={email!r} date={sql_date!r}. "
        f"total_responses={total} "
        f"rows_with_same_email={[(r['e'], str(r['d'])) for r in email_hits]} "
        f"emails_on_same_date={date_hits}"
    )
    raise RespondentLookupDiagnostic(detail)


# --- Non-scorable text answers --------------------------------------------

def _load_isscored_map(cur: pymysql.cursors.DictCursor) -> dict[str, int]:
    """Return {QuestionNmbr (str): IsScored (0|1)} for IsActive=1 questions.

    Falls back to empty dict if excellence_questions query fails (matching
    PHP's defensive behaviour).
    """
    try:
        cur.execute(
            "SELECT `QuestionNmbr`, `IsScored` FROM `excellence_questions` "
            "WHERE `IsActive` = 1"
        )
        return {str(r["QuestionNmbr"]): int(r["IsScored"]) for r in cur.fetchall()}
    except pymysql.err.MySQLError as exc:  # noqa: BLE001
        log.warning("excellence_questions lookup failed: %s; defaulting all INTs to scored", exc)
        return {}


def _classify_columns(
    cur: pymysql.cursors.DictCursor, scored_map: dict[str, int]
) -> list[tuple[str, str]]:
    """Return list of (column_name, qnum) for columns that belong in 'text'.

    A column goes in 'text' when it's VARCHAR/TEXT-typed OR it's INT-typed
    but registered in excellence_questions with IsScored=0 (matches PHP).
    """
    cur.execute("SHOW FULL COLUMNS FROM `excellence_survey_responses`")
    columns = cur.fetchall()
    text_columns: list[tuple[str, str]] = []

    for col in columns:
        field = col["Field"]
        col_type = col["Type"].upper()
        if not field.startswith("q"):
            continue
        m = re.match(r"^q(\d+)", field)
        if not m:
            continue
        qnum = m.group(1)
        is_int = "INT" in col_type
        # Default to scored (1) if not registered — mirrors PHP
        is_scored = scored_map.get(qnum, 1)
        if not is_int or not is_scored:
            text_columns.append((field, qnum))
    return text_columns


def fetch_text_answers(key3: str) -> list[dict[str, Any]]:
    """Return non-scorable answers for one respondent in the long format
    {Key3, QuestionNmbr, Answer, Memo:Date}. Mirrors the 'text' endpoint
    of excellence_export.php.
    """
    date_part, email = _parse_key3(key3)
    sql_date = _sql_date_from_key3_date(date_part)

    with _connect() as conn:
        with conn.cursor() as cur:
            scored_map = _load_isscored_map(cur)
            text_columns = _classify_columns(cur, scored_map)

            cur.execute(
                f"SELECT * FROM `excellence_survey_responses` "
                f"WHERE `{COL_EMAIL}` = %s AND DATE(`created_at`) = %s "
                f"ORDER BY `created_at` DESC LIMIT 1",
                (email, sql_date),
            )
            row = cur.fetchone()

    if row is None:
        return []

    created = row["created_at"]
    memo_date = created.strftime("%m/%d/%Y")

    output: list[dict[str, Any]] = []
    for field, qnum in text_columns:
        val = row.get(field)
        if val is None or val == "":
            continue
        answer_str = str(val)
        # Strip newlines for CSV safety (mirrors PHP)
        answer_str = answer_str.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        output.append(
            {
                "Key3": key3,
                "QuestionNmbr": qnum,
                "Answer": answer_str,
                "Memo:Date": memo_date,
            }
        )
    return output


# --- Diagnostic -----------------------------------------------------------

def ping() -> dict[str, Any]:
    """Connectivity + schema probe for debugging."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            table_names = [list(r.values())[0] for r in cur.fetchall()]

            result: dict[str, Any] = {
                "total_tables": len(table_names),
                "excellence_tables": [t for t in table_names if t.startswith("excellence_")],
            }

            if "excellence_survey_responses" in table_names:
                cur.execute("SELECT COUNT(*) AS n FROM `excellence_survey_responses`")
                result["survey_responses_rows"] = cur.fetchone()["n"]
                # Show first few q-columns for sanity
                cur.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "  AND TABLE_NAME = 'excellence_survey_responses' "
                    "  AND COLUMN_NAME LIKE 'q%' "
                    "ORDER BY ORDINAL_POSITION LIMIT 20"
                )
                result["first_20_q_columns"] = cur.fetchall()

            if "excellence_questions" in table_names:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM `excellence_questions` WHERE IsActive = 1"
                )
                result["questions_active"] = cur.fetchone()["n"]
                cur.execute(
                    "SELECT COUNT(*) AS n FROM `excellence_questions` "
                    "WHERE IsActive = 1 AND IsScored = 1"
                )
                result["questions_scored"] = cur.fetchone()["n"]

    return result
