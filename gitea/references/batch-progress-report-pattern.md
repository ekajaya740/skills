# Batch Progress Report Pattern

Used when the user provides a list of Gitea issue URLs pre-grouped by status (Done / On Progress / etc.), with the instruction "1 link = 1 row".

## Interpretation
- If URLs are grouped by status AND the user says "1 link = 1 row," the instruction is:
  **One row per status group** (not per issue).
- The Notes column holds ALL links for that status.
- The Task Details column stays empty (summary rows).
- Request Date = **today** (the date the report is being written), NOT each issue's `created_at`.

## Working Deduped URL Builder (Python)

```python
urls_done = [
    "https://code.re-creation.co.jp/MIPS/work_assignments/issues/306",
    "https://code.re-creation.co.jp/MIPS/work_assignments/issues/307",
    # ... etc
]
# Remove duplicates while preserving order
def dedupe_ordered(urls):
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out

done_urls = dedupe_ordered(urls_done)
done_notes   = "Issues:\n" + "\n".join(done_urls)
progress_notes = "Issues:\n" + "\n".join(in_progress_urls)
```

## Working gws Write Path

```python
import json, os, subprocess

SHEET = os.environ.get("SHEET_ID", "...")
GWS   = os.path.join(os.path.expanduser("~"), ".hermes", "node", "bin", "gws")
env   = dict(os.environ, PATH=os.path.dirname(GWS) + os.pathsep + os.environ.get("PATH", ""))

rows = [
    ["26", "2026-05-25", "Bug Fixing",    "", "", "", "", "", "", "", "", "Done",        done_notes],
    ["27", "2026-05-25", "Investigating", "", "", "", "", "", "", "", "", "On Progress", progress_notes],
]

body_json   = json.dumps({"values": rows})
params_json = json.dumps({"spreadsheetId": SHEET, "range": "'Tasks Details'!A27:M28", "valueInputOption": "USER_ENTERED"})

res = subprocess.run(
    [GWS, "sheets", "spreadsheets", "values", "update",
     "--params", params_json, "--json", body_json],
    capture_output=True, text=True, env=env)
```

## Verification
After writing, read back the M column to confirm `\n` newlines were preserved:

```python
r = subprocess.run([GWS, "sheets", "+read", "--spreadsheet", SHEET, "--range", "'Tasks Details'!M27:M28"],
                   capture_output=True, text=True, env=env)
print(json.loads(r.stdout).get("values"))
```

## Result
- **26 cells updated**, `updatedRows: 2`, `updatedRange: 'Tasks Details'!A27:M28`.
- Notes cells contain multi-line URLs as intended.
