"""One-time interactive bootstrap to obtain an MSAL refresh token.

Run this locally (NOT on Render). It uses the device-code flow: you visit a
URL, enter a code, and sign in as charles@haleglobal.com. The script then
prints the refresh token which you paste into Render as MSAL_REFRESH_TOKEN.

Prerequisites:
    - Azure Portal → App Registrations → PowerBIEmbedApp → Authentication →
      "Allow public client flows" must be set to **Yes**.
    - pip install msal python-dotenv

Usage:
    python scripts/bootstrap_user_auth.py

The script reads PBI_TENANT_ID and PBI_CLIENT_ID from .env (same values the
pipeline already uses). No client secret is needed — device-code flow is a
public-client flow.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

# Load .env from repo root (one level up from scripts/)
load_dotenv()

try:
    import msal  # type: ignore[import-untyped]
except ImportError:
    print("Error: msal not installed. Run: pip install msal", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    tenant = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    if not tenant or not client_id:
        print("Error: PBI_TENANT_ID and PBI_CLIENT_ID must be set in .env", file=sys.stderr)
        return 2

    authority = f"https://login.microsoftonline.com/{tenant}"
    scopes = ["https://analysis.windows.net/powerbi/api/.default", "offline_access"]

    app = msal.PublicClientApplication(client_id=client_id, authority=authority)

    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        print(f"Error initiating device flow: {flow.get('error_description', flow)}", file=sys.stderr)
        return 1

    print()
    print("=" * 60)
    print("  SIGN-IN REQUIRED")
    print("=" * 60)
    print()
    print(f"  1. Open:  {flow['verification_uri']}")
    print(f"  2. Enter: {flow['user_code']}")
    print(f"  3. Sign in as charles@haleglobal.com")
    print()
    print("  Waiting for you to complete sign-in...")
    print()

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        print(f"Auth failed: {result.get('error')} — {result.get('error_description')}", file=sys.stderr)
        return 1

    refresh_token = result.get("refresh_token")
    if not refresh_token:
        print("Warning: no refresh token returned. The app registration may not", file=sys.stderr)
        print("have 'offline_access' scope enabled, or public client flows may", file=sys.stderr)
        print("not be turned on.", file=sys.stderr)
        return 1

    print("=" * 60)
    print("  SUCCESS — refresh token obtained")
    print("=" * 60)
    print()
    print("  Copy the token below and add it to Render as env var:")
    print("    MSAL_REFRESH_TOKEN=<token>")
    print()
    print("-" * 60)
    print(refresh_token)
    print("-" * 60)
    print()
    print("  Token length:", len(refresh_token), "chars")
    print("  This token is valid for ~90 days. Re-run this script to renew.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
