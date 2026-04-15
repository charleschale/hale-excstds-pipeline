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

    When PBI_IMPERSONATED_USER env var is set, its value is sent as
    impersonatedUserName in the request body. This is REQUIRED when calling
    executeQueries with a service principal against a dataset that has
    row-level security (RLS) configured — without it, Power BI returns
    401 PowerBINotAuthorizedException even when the SP is a workspace
    admin. The value should be the UPN (email) of a user with access to
    the dataset.
    """
    workspace = _require_env("PBI_WORKSPACE_ID")
    dataset = _require_env("PBI_DATASET_ID")
    token = _acquire_token()

    url = EXECUTE_QUERIES_URL.format(workspace=workspace, dataset=dataset)
    body: dict[str, Any] = {
        "queries": [{"query": dax}],
        "serializerSettings": {"includeNulls": True},
    }
    impersonated = os.getenv("PBI_IMPERSONATED_USER")
    if impersonated:
        body["impersonatedUserName"] = impersonated

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


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    """Decode the payload section of a JWT without verifying the signature.

    Used only for diagnostics — we trust the token because we just got it
    from msal, so signature verification isn't adding anything here.
    Returns a filtered set of the claims most relevant to auth debugging.
    """
    import base64
    import json

    parts = token.split(".")
    if len(parts) != 3:
        return {"error": f"token has {len(parts)} parts, expected 3"}
    # JWT payload is base64url-encoded and may lack padding
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except Exception as exc:  # noqa: BLE001
        return {"error": f"decode failed: {exc}"}
    # Surface the claims that tell us if the token is valid for Power BI
    return {
        "aud": payload.get("aud"),
        "iss": payload.get("iss"),
        "tid": payload.get("tid"),
        "appid": payload.get("appid"),
        "oid": payload.get("oid"),
        "roles": payload.get("roles"),
        "scp": payload.get("scp"),
        "idtyp": payload.get("idtyp"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
    }


def diagnostic_ping() -> dict[str, Any]:
    """Test PBI auth by making progressively more-permissioned calls.

    Returns a dict showing which calls succeeded / failed. Used to
    isolate 401s — membership problems look different from tenant-setting
    problems look different from dataset-specific problems.
    """
    out: dict[str, Any] = {}
    try:
        token = _acquire_token()
        out["token_acquired"] = True
        out["token_length"] = len(token)
        out["token_claims"] = _decode_jwt_claims(token)
    except Exception as exc:  # noqa: BLE001
        out["token_acquired"] = False
        out["token_error"] = str(exc)
        return out

    headers = {"Authorization": f"Bearer {token}"}
    workspace = os.getenv("PBI_WORKSPACE_ID", "")
    dataset = os.getenv("PBI_DATASET_ID", "")

    # Can we list workspaces at all? (basic read permission)
    try:
        r = requests.get(
            "https://api.powerbi.com/v1.0/myorg/groups",
            headers=headers,
            timeout=30,
        )
        out["list_groups_status"] = r.status_code
        if r.ok:
            groups = r.json().get("value", [])
            out["list_groups_count"] = len(groups)
            out["target_workspace_visible"] = any(
                g.get("id", "").lower() == workspace.lower() for g in groups
            )
        else:
            out["list_groups_body"] = r.text[:300]
    except Exception as exc:  # noqa: BLE001
        out["list_groups_error"] = str(exc)

    # Can we list datasets inside the target workspace?
    try:
        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets",
            headers=headers,
            timeout=30,
        )
        out["list_datasets_status"] = r.status_code
        if r.ok:
            datasets = r.json().get("value", [])
            out["list_datasets_count"] = len(datasets)
            out["target_dataset_visible"] = any(
                d.get("id", "").lower() == dataset.lower() for d in datasets
            )
        else:
            out["list_datasets_body"] = r.text[:300]
    except Exception as exc:  # noqa: BLE001
        out["list_datasets_error"] = str(exc)

    # Can we execute a trivial query? This is the actual capability we need.
    # Includes impersonatedUserName when configured — required for RLS.
    body: dict[str, Any] = {"queries": [{"query": "EVALUATE ROW(\"ping\", 1)"}]}
    impersonated = os.getenv("PBI_IMPERSONATED_USER")
    if impersonated:
        body["impersonatedUserName"] = impersonated
        out["impersonated_user"] = impersonated
    try:
        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets/{dataset}/executeQueries",
            headers={**headers, "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        out["trivial_query_status"] = r.status_code
        out["trivial_query_body"] = r.text[:500]
    except Exception as exc:  # noqa: BLE001
        out["trivial_query_error"] = str(exc)

    return out
