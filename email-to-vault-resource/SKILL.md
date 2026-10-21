---
name: email-to-vault-resource
description: "Pull a document-bearing email (ticket, policy, receipt, contract) from Gmail and file it into the second brain as a Notion Notes row (Type=Reference) with a Drive link, related to the owning Project/Area - or deliver its attachments straight to chat ('pull all X invoices and send it here'). Use when the user says 'pull the latest email from X and put it on the resources / reference it in area Y', or wants an emailed PDF saved into a project/area. Covers Gmail retrieval (incl. when himalaya/gws is unavailable), attachment download, Notion Notes authoring, and bidirectional relations. NOT for: general web clippings (use second-brain-clipping-processor), or sending/replying to email (not supported by this skill)."
version: 3.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Email, Gmail, Notion, Second-Brain, PARA, Resources, Attachments]
    related_skills: [notion-second-brain, second-brain-clipping-processor, second-brain-project-area-creator]
---

# Email -> Second Brain Resource (Notion)

File a document-bearing email (ticket, insurance policy, e-ticket, receipt, contract, statement) into
the second brain as a **Notion Notes row** (`Type=Reference`) that links the owning **Project/Area**
and carries the attachment as a **Google Drive** link.

Knowledge lives in **Notion**; binaries live in **Google Drive**. There is no vault file, no
wikilink, and no git step.

Worked example that motivated this skill: *Return-to-Bali <- "E-Policy Asuransi & E-Tiket Return
Terbaru" from Admin Sum (SUM Digital)* - pulled the latest SUM email, downloaded 2 insurance
e-policies + 2 return e-tickets, uploaded them to Drive, and created a Notes row related to both
the Return-to-Bali **Project** and the PT-SUM-Digital-Konsultan **Area**.

## Environment

```bash
export WORKSPACE="${WORKSPACE:-$HOME/Documents/01-Projects/Notion-Migration}"
[ -f "$WORKSPACE/.env" ] && set -a && . "$WORKSPACE/.env" && set +a
export NOTION_API_VERSION=2026-03-11
export NOTION_API_TOKEN="${NOTION_API_KEY:?NOTION_API_KEY missing - put it in $WORKSPACE/.env}"

nb() {  # nb METHOD PATH [json-body]
  curl -sS -X "$1" "https://api.notion.com$2" \
    -H "Authorization: Bearer $NOTION_API_TOKEN" \
    -H "Notion-Version: $NOTION_API_VERSION" \
    -H "Content-Type: application/json" \
    ${3:+-d "$3"}
}

LEDGER="$WORKSPACE/migration/ledger/notion_db_ids.json"
NOTES_DS=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['Notes'])" "$LEDGER")
```

Never inline the token. The token lives in `$WORKSPACE/.env` as `NOTION_API_KEY` (or an exported
env var) - `~/.hermes` no longer exists. The data-source ids live in
`$WORKSPACE/migration/ledger/notion_db_ids.json`. Contract: `notion-second-brain`.

3 requests/second - space calls ~350 ms.

## Phase 1 - Fetch the email (Gmail)

`himalaya` and `gws` are not installed on this machine. The reliable path is **raw Gmail REST
with the stored OAuth token** - the helper scripts in `scripts/` do it
(`scripts/gmail_fetch.py`, `scripts/gws_token.py`). Short version:

1. Credentials live at `~/.config/gws/credentials.json` (`client_id`, `client_secret`,
   `refresh_token`).
2. Refresh the (often expired) access token via `oauth2.googleapis.com/token` with
   `refresh_token` + client secret, then call Gmail REST. `scripts/gws_token.py` does exactly
   that and prints the access token.
   Ready-made commands:
   `python3 scripts/gmail_fetch.py search "subject:invoice" 10` and
   `python3 scripts/gmail_fetch.py show <message_id> --out /tmp/email-attachments`.
3. **Find "the latest from X":** `from:domain.com` often returns 0 (envelope-from differs).
   Prefer `subject:<keyword>` or a bare keyword (`SUM`, `insurance`, `asuransi`), then sort
   candidates by the `Date` header. Attachments (`E-Policy`, `E-Ticket`) are the real signal of
   "the document wanted".

## Phase 2 - Download attachments

- Walk `msg['payload'].parts`; parts with a `filename` carry a `body.attachmentId`. Fetch bytes
  from `.../messages/{id}/attachments/{attid}` and `base64` decode into `/tmp/<slug>/`.
- **Rename generic originals** to clarify owner + type:
  `E-Polis Eka New.pdf` -> `E-Policy-Insurance-Eka.pdf`,
  `0795..._PUTRA I PUTU EKAJAYA....pdf` -> `E-Ticket-Return-Eka.pdf`.
- **CRITICAL: run the download from a script file via `terminal`** (`python3 /tmp/dl_email.py`),
  NOT from `execute_code`. Inside `execute_code`, the Gmail network calls hit a consent gate and
  silently time out.
- Validate each download: `head -c 8 file.pdf` must start with `%PDF`.

## Phase 3 - Upload the binaries to Drive

```bash
python3 scripts/drive_upload.py /tmp/<slug>/E-Policy-Insurance-Eka.pdf <target_folder_id> --name "E-Policy-Insurance-Eka.pdf"
# list the folders first:
python3 scripts/drive_upload.py --list
```
- Project attachments -> the project's Drive folder; area attachments -> the area's Drive
  folder. Discover the folder id with `scripts/drive_upload.py --list` (there is no
  hard-coded folder map on this machine).
- Capture the `webViewLink` from the JSON; verify the real parent with `?fields=parents` (the
  upload response's `parents` lies - see `drive-upload-semantics.md`).
- Drive, not Notion, holds the binary: **Notion file URLs are pre-signed and expire**, so never
  link a Notion-hosted file from the page body.

## Phase 4 - Create the Notion Notes row

**Search first** (dedupe on `Source URL`, then title), then create - one request, properties +
body:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$NOTES_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"SUM Return Ticket & Insurance"}}]},
    "Type": {"select":{"name":"Reference"}},
    "Status": {"select":{"name":"Active"}},
    "Date": {"date":{"start":"2026-07-09"}},
    "Source URL": {"url":"mailto:billing@example.com"},
    "Project": {"relation":[{"id":"<return-to-bali-page-id>"}]},
    "Area": {"relation":[{"id":"<pt-sum-page-id>"}]},
    "Confidential": {"checkbox":true}
  },
  "markdown": "# SUM Return Ticket & Insurance\n\n**Source:** Email from **Admin Sum** - \"E-Policy Asuransi & E-Tiket Return Terbaru\" (2026-07-09)\n\n## Attachments\n| File | Description | For |\n|------|-------------|-----|\n| [E-Ticket-Return-Eka.pdf](<drive link>) | Return e-ticket (rescheduled) | I Putu Ekajaya Awidya Putra |\n| [E-Policy-Insurance-Eka.pdf](<drive link>) | Travel insurance e-policy | I Putu Ekajaya Awidya Putra |"
}'
```

**Properties carry the metadata; the body carries the summary + Drive links.** Keep the original
filenames noted for traceability. Split the body if any rich-text value would exceed 2,000 chars,
and keep a single markdown payload under 5000 blocks.

## Phase 5 - Link from both ends (relations)

- Set the **`Project`** relation on the new row (e.g. Return-to-Bali) and the **`Area`** relation
  (e.g. PT-SUM-Digital-Konsultan). Relations are bidirectional in Notion - you do NOT hand-edit the
  other side.
- If the owning Project/Area row does not exist, say so and offer to create it
  (`second-brain-project-area-creator`) instead of inventing a relation.

## Phase 6 - Verify + report

- `head -c 8 file.pdf` -> `%PDF`; the Drive file sits in the intended folder
  (`python3 scripts/drive_upload.py --list <folder_id>`).
- `nb GET /v1/pages/<page-id>` and `nb GET /v1/pages/<page-id>/markdown` read the saved row back
  with both relations populated.
- Report what was pulled, where the binaries live, and which rows were related.

## Pitfalls

- `execute_code` blocks Gmail-attachment downloads (consent gate -> silent timeout). Use
  `terminal` + a script file.
- Gmail's `format=full` body can be empty for HTML-rich emails (Render receipts) - walk the
  MIME parts (`payload.parts`) and reach the PDFs via the attachment ids.
- `mid` from search results is a `{"id":...}` dict - extract `m['id']` before building URLs or you
  get `http.client.InvalidURL`.
- `from:` query misses emails whose envelope-from differs from the visible From - search by
  subject/keyword.
- Don't overwrite the user's only copy - keep originals noted; downloaded PDFs are independent
  copies.
- **Never write a vault file, a `[[wikilink]]`, or a git commit.** Notion holds text + relations;
  Drive holds the binary.
- Set `Confidential` for insurance/policy/personal-document rows.

## Variant - deliver attachments to chat instead of Notion

When the user says "pull all <vendor> invoices and send it here" (no filing):

1. **Completeness search** - run several query variants (`from:<billing-addr>`,
   `subject:receipt/invoice <vendor>`, `from:<vendor-domain>`) and dedupe by message id. Billing
   receipts often come from a sub-address (`invoice+statements@example.com`); the broad `from:`
   query returns marketing/alert noise to filter out (server-failure, action-required, "new
   features").
2. Download via raw REST (Phase 2) into `/tmp/<vendor>_invoices/`.
3. **Rename before sending** - copy originals to descriptive names:
   `Invoice-XE6JSYVE-0002-Apr2026.pdf`, `Receipt-2651-9915-Apr2026.pdf` (vendor + number +
   month/year).
4. Deliver each file with `MEDIA:/abs/path` in the reply - PDFs send as native attachments on
   Discord/Telegram.
5. Flag adjacent alerts worth the user's attention (e.g. an "[Action Required] Invalid payment info"
   email sitting next to unpaid-balance invoices).
