#!/usr/bin/env python3
"""Refresh a Google OAuth access token from the stored authorized_user credentials.

Credentials live in ~/.config/gws/credentials.json (client_id, client_secret,
refresh_token). The access token stored there is usually expired; this helper
refreshes it and prints the fresh access token on stdout.

Usage:
    python3 gws_token.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

CREDS = Path(os.environ.get("GWS_CREDENTIALS", "~/.config/gws/credentials.json")).expanduser()
TOKEN_URL = "https://oauth2.googleapis.com/token"


def access_token() -> str:
    creds = json.loads(CREDS.read_text())
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen(TOKEN_URL, data, timeout=30) as resp:
        return json.load(resp)["access_token"]


if __name__ == "__main__":
    try:
        print(access_token())
    except Exception as exc:  # noqa: BLE001
        print("token refresh failed: %s" % exc, file=sys.stderr)
        sys.exit(1)
