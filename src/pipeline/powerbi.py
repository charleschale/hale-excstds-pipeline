"""Power BI executeQueries REST client.

Uses a service principal (client credentials flow) to authenticate and fires
DAX queries against the Excellence Standards dataset. Returns rows as plain
Python dicts; the caller is responsible for assembling them into output
formats.

Environment variables required:
    PBI_TENANT_ID      - Azure tenant GUID
    PBI_CLIENT_ID      - Service principal app (client) ID
    PBI_CLIENT_SECRET  - Service principal secret value
    PBI_WORKSPACE_ID   - Power BI workspace (group) GUID
    PBI_DATASET_ID     - Power BI dataset GUID

See README for setup. Secrets never live in code or in the repo.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import msal  # type: ignore[import-untyped]
import requests

log = logging.getLogger(__name__)

SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
EXECUTE_QUERIES_URL = (
    "https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets/{dataset}/executeQueries"
)


class PowerBIConfigError(RuntimeError):
    """Raised when a required env var is missing."""


class PowerBIQueryError(RuntimeError):
    """Raised when executeQueries returns a non-2xx response."""


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise PowerBIConfigError(f"Missing required env var: {name}")
    return value


def _acquire_token() -> str:
    """Return a bearer token for the Power BI REST API.

    Uses msal's in-memory token cache so repeated calls in the same process
    are cheap.
    """
    tenant = _require_env("PBI_TENANT_ID")
    client_id = _require_env("PBI_CLIENT_ID")
    client_secret = _require_env("PBI_CLIENT_SECRET")

    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        raise PowerBIQueryError(
            f"Token acquisition failed: {result.get('error')} — {result.get('error_description')}"
        )
    return str(result["access_token"])


def execute_dax(dax: str, *, timeout: int = 90) -> list[dict[str, Any]]:
    """Execute a single DAX query and return rows as dicts.

    The first (and only) table in the response is returned. If the query
    returns no tables, an empty list is returned.
    """
    workspace = _require_env("PBI_WORKSPACE_ID")
    dataset = _require_env("PBI_DATASET_ID")
    token = _acquire_token()

    url = EXECUTE_QUERIES_URL.format(workspace=workspace, dataset=dataset)
    body = {
        "queries": [{"query": dax}],
        "serializerSettings": {"includeNulls": True},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    log.debug("POST %s (dax %d chars)", url, len(dax))
    resp = requests.post(url, json=body, headers=headers, timeout=timeout)
    if not resp.ok:
        raise PowerBIQueryError(
            f"executeQueries {resp.status_code}: {resp.text[:500]}"
        )
    payload = resp.json()
    results = payload.get("results") or []
    if not results:
        return []
    tables = results[0].get("tables") or []
    if not tables:
        return []
    return list(tables[0].get("rows") or [])


def load_query(name: str) -> str:
    """Load a DAX file from the dax/ folder bundled with this package."""
    here = Path(__file__).resolve().parent.parent.parent  # repo root
    path = here / "dax" / f"{name}.dax"
    if not path.exists():
        raise FileNotFoundError(f"DAX file not found: {path}")
    return path.read_text(encoding="utf-8")


def render_query(name: str, *, key3: str) -> str:
    """Load a named DAX template and substitute {KEY3} with a real value.

    Key3 is inserted as a bare string inside double quotes in the DAX. The
    value is rejected if it contains a double quote to prevent accidental
    injection. Excellence Standards Key3 values never contain quotes in the
    observed dataset.
    """
    if '"' in key3:
        raise ValueError("Key3 must not contain a double quote character")
    template = load_query(name)
    return template.replace("{KEY3}", key3)


def run_named_query(name: str, *, key3: str) -> list[dict[str, Any]]:
    """Convenience: render + execute a named DAX query for a respondent."""
    dax = render_query(name, key3=key3)
    return execute_dax(dax)
