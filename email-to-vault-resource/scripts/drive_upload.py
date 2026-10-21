#!/usr/bin/env python3
"""Upload a binary to Google Drive with raw Drive REST (multipart).

The `gws` CLI is unusable on this machine, so this helper calls the Drive v3
files.create endpoint directly with the stored OAuth refresh token. The
authorized_user credential carries the drive.file and drive scopes, so uploads
work.

Usage:
    python3 drive_upload.py <local-file> [parent-folder-id] [--name NAME]
    python3 drive_upload.py --list [parent-folder-id]
"""
from __future__ import annotations

import json
import mimetypes
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gws_token import access_token  # noqa: E402

UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
META = "https://www.googleapis.com/drive/v3/files"
CRLF = chr(13) + chr(10)
BOUNDARY = "===notion-migration-boundary"


def upload(path: str, parent, name) -> dict:
    token = access_token()
    p = Path(path)
    payload = p.read_bytes()
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    meta = {"name": name or p.name, "mimeType": mime}
    if parent:
        meta["parents"] = [parent]
    head = ("--" + BOUNDARY + CRLF + "Content-Type: application/json; charset=UTF-8" + CRLF + CRLF)
    mid = ("--" + BOUNDARY + CRLF + "Content-Type: " + mime + CRLF + CRLF)
    tail = (CRLF + "--" + BOUNDARY + "--")
    body = head.encode() + json.dumps(meta).encode() + mid.encode() + payload + tail.encode()
    req = urllib.request.Request(
        UPLOAD + "?uploadType=multipart&fields=id,name,webViewLink,parents",
        data=body,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "multipart/related; boundary=" + BOUNDARY,
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def list_files(parent) -> list:
    token = access_token()
    q = ("%r in parents and trashed=false" % parent) if parent else "trashed=false"
    url = META + "?" + urllib.parse.urlencode({
        "q": q,
        "fields": "files(id,name,mimeType,webViewLink,parents)",
        "pageSize": 50,
    })
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp).get("files", [])


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    if args[0] == "--list":
        print(json.dumps(list_files(args[1] if len(args) > 1 else None), indent=2))
        return
    name = None
    if "--name" in args:
        i = args.index("--name")
        name = args[i + 1]
        del args[i : i + 2]
    parent = args[1] if len(args) > 1 else None
    print(json.dumps(upload(args[0], parent, name), indent=2))


if __name__ == "__main__":
    main()
