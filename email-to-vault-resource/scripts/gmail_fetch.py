#!/usr/bin/env python3
"""Fetch Gmail messages and attachments with raw Gmail REST.

The `gws` CLI is not usable on this machine (its config dir is read-only and it
points at the removed ~/.hermes tree), so this helper talks to the Gmail REST
API directly with the stored OAuth refresh token.

Usage:
    python3 gmail_fetch.py search "subject:invoice" [max]
    python3 gmail_fetch.py show   <message_id> [--out DIR]
"""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gws_token import access_token  # noqa: E402

GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me"


def api(path: str, token: str) -> dict:
    req = urllib.request.Request(GMAIL + path, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.load(resp)


def sanitize(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip() or "attachment"
    return name.replace(" ", "-")


def walk_parts(parts):
    out = []
    for part in parts:
        if part.get("parts"):
            out.extend(walk_parts(part["parts"]))
        elif part.get("filename"):
            out.append(part)
    return out


def cmd_search(query: str, max_results: int, token: str) -> None:
    q = urllib.parse.quote(query)
    listing = api("/messages?q=%s&maxResults=%d" % (q, max_results), token)
    rows = []
    for mid in [m["id"] for m in listing.get("messages", [])]:
        msg = api("/messages/%s?format=metadata" % mid, token)
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        rows.append({
            "id": mid,
            "date": headers.get("Date", ""),
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
        })
    rows.sort(key=lambda r: r["date"])
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def cmd_show(message_id: str, out_dir: str, token: str) -> None:
    msg = api("/messages/%s?format=full" % message_id, token)
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    head = {"id": message_id}
    for k in ("Date", "From", "To", "Subject"):
        head[k] = headers.get(k, "")
    print(json.dumps(head, indent=2))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for part in walk_parts(msg.get("payload", {}).get("parts", [])):
        att_id = (part.get("body") or {}).get("attachmentId")
        if not att_id:
            continue
        data = api("/messages/%s/attachments/%s" % (message_id, att_id), token)
        raw = base64.b64decode(data["data"])
        target = out / sanitize(part["filename"])
        target.write_bytes(raw)
        print("saved %s (%d bytes, mime %s)" % (target, len(raw), part.get("mimeType")))


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    token = access_token()
    cmd = sys.argv[1]
    if cmd == "search":
        cmd_search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20, token)
    elif cmd == "show":
        args = sys.argv[2:]
        out = "/tmp/email-attachments"
        if "--out" in args:
            i = args.index("--out")
            out = args[i + 1]
            del args[i : i + 2]
        cmd_show(args[0], out, token)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
