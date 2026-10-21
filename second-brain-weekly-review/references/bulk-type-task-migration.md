# Bulk Task Status Migration

## The old convention

Actionable items used to carry a `#type/task` prefix so the Obsidian Tasks plugin could query
them across the vault:

```
- [ ] #type/task Do the thing
- [x] #type/task Done thing
```

That plugin and that prefix are gone. **A task is a row in the Tasks data source** and its state
lives in properties:

| Old | New |
|---|---|
| `- [ ]` (open) | `Status` = Todo |
| `- [ ]` (in progress) | `Status` = In progress |
| `- [ ]` (blocked) | `Status` = Blocked |
| `- [x]` (done) | `Status` = Done |
| `#type/task` tag | `Tags` = `type/task` (keep it for filtering) |
| due date in the text | `Due` date property |
| owner in the text | `Context` (Computer/Home/Errands/Calls/Anywhere) + priority in the name |

## Migration procedure

1. **Find the rows missing a status** - a Task row always has `Status`; the rows to migrate are
   the checkbox lines still sitting inside **Notes** and **Daily Notes** bodies.
2. **Create a Task row** for each one:
   ```bash
   nb POST /v1/pages '{
     "parent": {"type":"data_source_id","data_source_id":"'"$TASKS_DS"'"},
     "properties": {
       "Name": {"title":[{"text":{"content":"Do the thing"}}]},
       "Status": {"select":{"name":"Todo"}},
       "Tags": {"multi_select":[{"name":"type/task"}]},
       "Source": {"relation":[{"id":"'"$NOTE_PAGE_ID"'"}]}
     }
   }'
   ```
3. **Remove the checkbox line from the body** with a targeted replace:
   ```bash
   nb PATCH /v1/pages/<note_page_id>/markdown '{"type":"update_content","update_content":{
     "content_updates":[{"old_str":"- [ ] #type/task Do the thing\n","new_str":""}]}}'
   ```
4. **Space the calls** ~350 ms apart (3 requests/second).

## Verification

```bash
# no stray checkbox lines left in note bodies
nb POST "/v1/data_sources/$NOTES_DS/query" '{"page_size":100}' > /tmp/notes.json
python3 - <<'PY'
import json, re
d = json.load(open("/tmp/notes.json"))
print(len(d["results"]), "rows to scan")
PY
# then GET the bodies you care about and grep for "- [ ]"
```

## Notes

- Notion markdown supports `- [ ]` / `- [x]` inside a page body. Keep a checkbox when it is
  purely informational; create a Task row when the item must be tracked.
- A Task row is the source of truth for state. The dashboard views filter on the property, so a
  checkbox in a note never shows up in "Due Today".
