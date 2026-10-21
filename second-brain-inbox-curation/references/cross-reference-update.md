# Cross-Reference Update Pattern

When a row moves, is retired, or is re-filed, all cross-references to it must be updated.

## Where cross-references hide in Notion

1. **Relation properties** - `Related`, `Sources`, `Project`, `Area`, `Supersedes`
2. **Inline mentions** in a page body:
   `<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>`
3. **The `Source URL` property** (a plain link - it is not a relation)
4. **The `Original Path` property** on Archive rows

## Steps

1. **Find the referring rows.** There is no "search by relation" endpoint, so query the data
   sources and filter in the response:
   ```bash
   nb POST "/v1/data_sources/$NOTES_DS/query" '{"page_size":100}' > /tmp/notes.json
   python3 - <<'PY'
   import json
   OLD = "<old_page_id>"
   d = json.load(open("/tmp/notes.json"))
   for r in d["results"]:
       for prop in ("Related", "Sources", "Project", "Area"):
           rel = r["properties"].get(prop, {}).get("relation", [])
           if any(x["id"] == OLD for x in rel):
               print(prop, r["id"], r["properties"]["Name"]["title"][0]["text"]["content"])
   PY
   ```
2. **Repoint the relation** (one side only - Notion mirrors it):
   ```bash
   nb PATCH /v1/pages/<referring_page_id> '{"properties":{
     "Related": {"relation":[{"id":"<new_page_id>"}]}}}'
   ```
3. **Fix inline mentions** in bodies with a targeted replace:
   ```bash
   nb PATCH /v1/pages/<referring_page_id>/markdown '{"type":"update_content","update_content":{
     "content_updates":[{"old_str":"<mention-page url=\"https://www.notion.so/<old_id>\">Title</mention-page>",
       "new_str":"<mention-page url=\"https://www.notion.so/<new_id>\">Title</mention-page>"}]}}'
   ```
4. **No reindex needed** - there is no QMD, no index, no reindex step.
5. **No git commit** - the vault is not a git repo any more.

## Pitfall: escaping

A mention contains quotes and angle brackets. Inside a JSON body string they must be escaped
(\\\" and the quote character), and the JSON itself must survive the shell - build the body in a
file and `curl --data @file` when in doubt.
