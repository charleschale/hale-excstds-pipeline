"""FastAPI server — thin HTTP wrapper around pipeline.runner.

Deployed to Render; local clients call POST /v1/pull-respondent with the
Key3 and get back an xlsx file as binary.

Auth: simple bearer token in the Authorization header. The token value
lives in the PIPELINE_API_TOKEN env var on Render; local clients read it
from their own .env. This is enough for our use case — the service is not
public, only called by a few trusted clients.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from pipeline.excstds_api import ping as excstds_ping
from pipeline.powerbi import diagnostic_ping as powerbi_ping
from pipeline.runner import RespondentNotFound, pull_respondent

log = logging.getLogger(__name__)

app = FastAPI(
    title="Hale ExcStds Pipeline",
    description="Respondent data pull service — Power BI + excellence_export.php",
    version="0.1.0",
)


class PullRequest(BaseModel):
    key3: str = Field(..., min_length=3, description="Respondent Key3 value")


def _check_auth(authorization: str | None) -> None:
    """Validate bearer token against env. Constant-time compare avoided
    deliberately — our token space is small and attack surface is low."""
    expected = os.getenv("PIPELINE_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server misconfigured: PIPELINE_API_TOKEN not set",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if authorization.removeprefix("Bearer ").strip() != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe for Render."""
    return {"status": "ok"}


@app.get("/v1/powerbi-ping")
def powerbi_ping_endpoint(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    """Diagnostic: verify Power BI auth path with progressively scoped calls."""
    _check_auth(authorization)
    try:
        return powerbi_ping()
    except Exception as exc:  # noqa: BLE001
        log.exception("powerbi ping failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Power BI ping failed: {exc}",
        )


@app.get("/v1/excstds-ping")
def excstds_ping_endpoint(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    """Diagnostic: verify MySQL connectivity + show schema of key tables.

    Useful to call after first deploy or after changing MYSQL_* env vars,
    to confirm the connection works before running a real pull.
    """
    _check_auth(authorization)
    try:
        return excstds_ping()
    except Exception as exc:  # noqa: BLE001
        log.exception("excstds ping failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"MySQL ping failed: {exc}",
        )


@app.post("/v1/pull-respondent")
def pull(
    body: PullRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """Pull all data for a respondent and return the xlsx as binary.

    Returns 404 if the Key3 is not in Lkup_Key. Returns 502 if any of the
    upstream calls (Power BI, PHP endpoint) fail hard.
    """
    _check_auth(authorization)
    try:
        xlsx_bytes = pull_respondent(body.key3)
    except RespondentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        log.exception("Pipeline failed for %s", body.key3)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream failure: {exc}",
        )

    safe_filename = body.key3.replace("/", "_").replace("\\", "_")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}.xlsx"',
        },
    )
