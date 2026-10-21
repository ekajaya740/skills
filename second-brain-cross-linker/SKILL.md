---
name: second-brain-cross-linker
description: "Cross-link pages in the migrated second brain in Notion - find orphaned notes, add bidirectional relations, and maintain connectivity. Use when the user says 'find orphans', 'cross-link my notes', 'connect related notes', 'link audit', 'check for orphaned notes'. NOT for: creating new content (use second-brain-inbox-curation or second-brain-clipping-processor), or summarizing content (use second-brain-summary)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Cross-Linking, Relations, API]
    related_skills: [notion-second-brain, second-brain-synthesis, second-brain-weekly-review, second-brain-operations]
---

# Second-Brain Cross-Linker

Maintain connectivity by finding orphaned notes, adding bidirectional relations, and ensuring
every note has at least one relation.

The second brain lives in **Notion**. A "link" is now a **relation property** (`Related` on
Notes) plus, when a human should see it, an inline **mention**
(`<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>`). There are no
`[[wikilinks]]` any more.

**Contract: `notion-second-brain`.** Read it before any call - data-source ids, property names,
the markdown dialect, the rate limit and the token location.

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
ds() { python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$LEDGER" "$1"; }
NOTES_DS=$(ds Notes); PROJECTS_DS=$(ds Projects); AREAS_DS=$(ds Areas)
```

3 requests/second - space calls ~350 ms.

## Prerequisites

1. **No search index needed.** There is no QMD, no index, no reindex step. Candidates come from
   property queries and `POST /v1/search`.
2. **Search for candidate links:**
   ```bash
   nb POST /v1/search '{"query":"<topic keywords>","page_size":30}'
   ```

## What This Skill Does

1. **Find orphaned notes** - notes with 0 inbound or outbound relations
2. **Find weakly connected notes** - notes with only 1 relation
3. **Suggest connections** - based on content similarity
4. **Add bidirectional links** - connect related content
5. **Report** - summary of what was connected

## Workflow

### Phase 1: Find Orphans

Scan the Notes data source for rows with no relations. A row whose `Related` relation is empty
AND which appears in nobody else's `Related` is an orphan:

```bash
nb POST "/v1/data_sources/$NOTES_DS/query" '{"page_size":100}' > /tmp/notes.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/notes.json"))
linked = set()
for r in d["results"]:
    for rel in r["properties"].get("Related", {}).get("relation", []):
        linked.add(rel["id"])
orphans = [r for r in d["results"]
           if not r["properties"].get("Related", {}).get("relation", [])
           and r["id"] not in linked]
for r in orphans:
    print(r["id"], r["properties"]["Name"]["title"][0]["text"]["content"])
print("orphans:", len(orphans))
PY
```

**Exclude from the orphan check:**
- Rows in the **Templates** data source - templates don't need links
- Pages whose Name is one of the index pages (Decision Log, Tasks Dashboard) - they are views
- Rows with `Status` = Archived (they are archived, not orphans)

### Phase 2: Find Weakly Connected Notes

Notes with only 1 relation are nearly orphans - same query, count relations per row:

```bash
python3 - <<'PY'
import json
d = json.load(open("/tmp/notes.json"))
weak = [r for r in d["results"]
        if len(r["properties"].get("Related", {}).get("relation", [])) == 1]
for r in weak:
    print(r["id"], r["properties"]["Name"]["title"][0]["text"]["content"])
print("weakly connected:", len(weak))
PY
```

### Phase 3: Suggest Connections

For each orphan or weakly-connected note:

1. **Read the note content** - `GET /v1/pages/{id}/markdown` - understand the topic
2. **Find related content:**
   ```bash
   nb POST /v1/search '{"query":"<topic keywords>","page_size":20}'
   ```
3. **Check the Projects and Areas data sources** for obvious matches:
   ```bash
   nb POST "/v1/data_sources/$PROJECTS_DS/query" '{"page_size":100}'
   nb POST "/v1/data_sources/$AREAS_DS/query" '{"page_size":100}'
   ```
4. **Suggest 1-3 connection candidates**

### Phase 4: Add Links

For each connection, set the `Related` relation on **one side only** - Notion relations are
bidirectional, so writing both sides duplicates the link:

```bash
nb PATCH /v1/pages/<orphan_page_id> '{"properties":{
  "Related": {"relation":[{"id":"<target_page_id>"}]}}}'
```

That single call gives both sides the link in Notion's UI. Never hand-write a backlink.

When a human should see the link, add an inline mention in the body as well:

```bash
nb PATCH /v1/pages/<orphan_page_id>/markdown '{"type":"update_content","update_content":{
  "content_updates":[{"old_str":"## Related Notes",
    "new_str":"## Related Notes\n- <mention-page url=\"https://www.notion.so/<target_page_id>\">Target title</mention-page>"}]}}'
```

**Linking rules:**
- Prefer a plain `Related` relation; add a mention only when a reader benefits
- Set relations on one side only - Notion mirrors them
- For project/area notes, relate them to the owning Projects/Areas row
- For standalone notes, relate them to related projects/areas
- Don't force links - if a note genuinely has no relation, leave it unlinked

### Phase 5: Report

```markdown
## 🔗 Cross-Linking Report

**Date:** YYYY-MM-DD

### Orphans Found: <N>
- <Note title> -> linked to <Target title> (topic match: <reason>)
- <Note title> -> no match found, left unlinked

### Weakly Connected: <N>
- <Note title> (1 link) -> added <Target title> (topic match: <reason>)

### Total Links Added: <N>
```

Use page titles in the report; add the page id in parentheses so the reader can open the row:
`<Note title> (<page_id>)`.

## Edge Cases

- **Note genuinely has no relation:** Leave it unlinked. Report it as "no match found."
- **Note is a template:** Skip - templates don't need links.
- **Note is an index page** (Decision Log, Tasks Dashboard): Skip - these are views.
- **Note already has 3+ relations:** Skip - sufficiently connected.
- **Target already links back:** skip the write - the relation is already there.
- **Large second brain:** the Notes data source has hundreds of rows - page through the query
  result with `page_size` 100 and follow `next_cursor`; don't try to hold every row in memory.

## Integration

- **notion-second-brain:** the contract - data sources, properties, relations, mentions, rate limit.
- **second-brain-synthesis:** Use for deep content analysis. This skill is for structural
  connectivity.
- **second-brain-weekly-review:** Includes a cross-link pass as part of the weekly review. This
  skill is for standalone link maintenance.
- **second-brain-operations:** The control panel. This skill is one of the periodic maintenance
  tasks.

## Anti-Patterns

- Don't add links to unrelated notes just to satisfy the "every note needs a link" rule
- Don't skip relations - every suggested connection must be written to the `Related` property
- Don't write both sides of a relation - that duplicates the link
- Don't modify templates - they're structural, not content
- Don't add links to archived notes from active notes (reverse is fine)
- Don't write a `[[wikilink]]` or a `notion://` URI - use relations and mentions
