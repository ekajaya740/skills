---
name: second-brain-clipping-processor
description: "Process web clippings from the Notion inbox: add metadata, link to related projects/areas, and file them as Notes rows. Use when the user wants to process clippings or as a daily cron task. Triggers on: 'process clippings', 'process web clippings', 'organize clippings', 'clip processor'. NOT for: general inbox curation (use second-brain-inbox-curation skill), extracting action items (use second-brain-action-items skill), or weekly review (use second-brain-weekly-review skill)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Clippings, Inbox, API]
    related_skills: [notion-second-brain, second-brain-inbox-curation, second-brain-action-items, second-brain-weekly-review, second-brain-cross-linker]
---

# Second-Brain Clipping Processor

Process web clippings from the inbox. For each clipping found, add proper properties, link it to
related projects or areas, and file it as a row in the **Notes** data source.

The second brain lives in **Notion**. A clipping arrives as an **Inbox** row with `Kind` = Clipping
and a `Source URL`; it leaves as a **Notes** row with `Type` = Reference. No `04-Resources/`
folder, no file to rename.

**Contract: `notion-second-brain`.** Read it first - data-source ids, property names, select
options, markdown dialect, rate limit, token location.

## When to Use This Skill

Use when the user says "process clippings" / "organize clippings", when the daily cron job runs, or
when you find Inbox rows with a `Source URL`. Do NOT use for: general inbox curation
(`second-brain-inbox-curation`); extracting action items (`second-brain-action-items`); weekly
review (`second-brain-weekly-review`).

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
INBOX_DS=$(ds Inbox); NOTES_DS=$(ds Notes); PROJECTS_DS=$(ds Projects); AREAS_DS=$(ds Areas)
```

3 requests/second - space calls ~350 ms. The ledger holds the data-source ids; refresh it with
`POST /v1/search` filtered on `object = data_source` when a name is missing.

## Workflow

### Phase 1: Find Clippings

No vault path to resolve any more. Source the token, read the ledger, read the conventions: the
property vocabulary lives in the contract skill and in notion-scaffold-and-beautify.md (migration
workspace). There is no vault AGENTS.md any more - see references/notion-conventions-check.md.

```bash
nb POST "/v1/data_sources/$INBOX_DS/query" '{"filter":{"and":[
  {"property":"Kind","select":{"equals":"Clipping"}},
  {"property":"Status","select":{"equals":"Untriaged"}}]},
  "sorts":[{"property":"Captured","direction":"ascending"}],"page_size":50}'
```

A row without a `Source URL` is not a clipping - skip it. Other `Kind` values belong to
`second-brain-inbox-curation`.

### Phase 2: For Each Clipping

#### 2a/2b. Read the Content, Determine the Title

The clipping body lives in the `Raw` rich-text property and sometimes in the page body
(`nb GET /v1/pages/<inbox_page_id>`, `nb GET /v1/pages/<inbox_page_id>/markdown`). Pick the
original title, shortened to one line (the Notion title is the page name, not a slug). No date
prefix, no extensions, no slashes.

#### 2c. Find Related Projects or Areas

**⚠️ Confidential Project Guard (Check BEFORE Linking)** - confidential rows carry the
**Confidential** checkbox. Only whitelisted models - **Anthropic Claude** (all models) and
**Ollama Cloud** (all models) - may read or write confidential content; any other provider
(OpenAI, OpenRouter, xAI, etc.) is forbidden. Read the target Projects/Areas row's `Confidential`
property first. If it is true AND the session is on a non-whitelisted model -> **do not relate the
clipping to it and do not read its body**; file it standalone (Option A) or relate it to a
non-confidential project/area, and note the skip in the report.

```bash
nb POST /v1/search '{"query":"<topic keywords>","page_size":20}'
nb POST "/v1/data_sources/$PROJECTS_DS/query" '{"page_size":100}'
nb POST "/v1/data_sources/$AREAS_DS/query" '{"page_size":100}'
```

(one query per data source, then read the bodies of the best candidates)

**Linking rules:** a technology/tool used in a project -> relate to that project; a domain that
is an area -> relate to that area; no match -> leave `Related` empty. Add a relation when a match
exists.

#### 2d. Determine Destination: Standalone Note vs. Project/Area Note

Both destinations are rows in the **Notes** data source; they differ in how they are linked.

| Option | Use when | Properties |
|---|---|---|
| **A - standalone** | article, tutorial, guide, pure reference material, tech overviews, cheatsheets - anything that stands alone as a knowledge base entry, with no project/area claiming it | no Project/Area relation |
| **B - project/area note** | content that directly informs or influences an existing project/area; philosophical, cultural or strategic material that shapes the work (a video essay on masculinity -> Work-Of-Ekajaya; a skincare routine clipping -> Skincare area) | `Project` or `Area` relation set (one side only - Notion mirrors it) |

**Decision test:** *"Would I file this under a project/area if I were retrieving it later while
working on that thing?"* -> yes = Option B, no = Option A.

#### 2e. Build the Properties

**Option A - standalone reference:**

```json
{
  "Name":   {"title":[{"text":{"content":"<Original title>"}}]},
  "Type":   {"select":{"name":"Reference"}},
  "Status": {"select":{"name":"Active"}},
  "Date":   {"date":{"start":"2026-10-21"}},
  "Tags":   {"multi_select":[{"name":"status/seed"},{"name":"type/reference"}]},
  "Source URL": {"url":"<URL from the Inbox row>"}
}
```

**Option B - project/area note:** same, but `Type` = Note, `Tags` = `status/note`, and
`"Project": {"relation":[{"id":"<project_page_id>"}]}` (or `Area`).

Property rules: `Date` = the processing date; `Source URL` = the original source URL;
`Tags` = status/* and type/* only, no topic tags. Vault statuses with no Notion select option
(seed, note, seedling, evergreen, investigation, resolved, processed) live as `status/<value>`
tags; `Status` stays `Active`. `Related` carries note-to-note links, `Sources` carries
provenance - use `Source URL` for a web link.

#### 2f. Format the Body

The body is enhanced markdown written with the page `markdown` param. First line a single `# H1`
title; a `**Source:** <URL>` attribution line; preserve transcript/curated content; **over ~300
lines** condense into a structured summary (outline, key quotes, code snippets, resource links -
see `references/long-clipping-condensation.md`); add a **## My Take** section for Option B (2-5
sentences connecting the dots); clean whitespace; add inline mentions where relevant
(`<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>`); escape
\ * ~ $ [ ] < > { } | ^ with a backslash outside code blocks, and use four backticks as the outer
fence when the content contains three-backtick runs.

#### 2g. Write, Then Retire the Inbox Row

Create the Notes row - one request, properties + body:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$NOTES_DS"'"},
  "properties": { ...as built in 2e... },
  "markdown": "# <Title>\\n\\n**Source:** <URL>\\n\\n..."
}'
```

Notion has no move endpoint, so the Inbox row is retired separately - set `Status` = `Filed`
(`Dropped` for a deliberate skip) with
`nb PATCH /v1/pages/<inbox_page_id> '{"properties":{"Status":{"select":{"name":"Filed"}}}}'`.
Never delete a page - archive it and log it.

#### 2h. Fix Cross-References

Any page that referenced the Inbox row must now point at the new Notes row. Find pages whose
`Related` or `Sources` relation contains the old Inbox page id, then PATCH the new target id
(`{"properties":{"Related":{"relation":[{"id":"<new_notes_page_id>"}]}}}`). Fix inline mentions of
the old id with `PATCH /v1/pages/{id}/markdown` using `update_content` (old mention as
`old_str`).

### Phase 3: Duplicate Detection by Source URL

Build a map of every existing `Source URL` once (one query of the Notes data source, collecting
each row's `Source URL` property into a dict), then check each clipping against it. If the
clipping's `Source URL` is already in the map -> **skip it** and log it as a duplicate; do not
create a second row. See `references/duplicate-detection-by-source-url.md`.

## Output Format

Clipping content lives in Notion, not in a git repo - there is no git commit for clippings. The
run report is the record.

```markdown
## 📋 Clipping Processing Report

**Date:** YYYY-MM-DD

**Clippings found:** <N>
**Processed:** <N>
**Skipped (duplicates):** <N>
**Errors:** <N>

### Processed
- **<original Inbox title>** -> Notes row "<new title>" (Type=Reference) - linked to <Project/Area>
- **<original Inbox title>** -> Notes row "<new title>" - no project/area match, standalone

### Skipped (duplicates)
- **<original Inbox title>** -> duplicate of "<existing note title>" (same Source URL)

### Errors
- **<original Inbox title>** -> <error>
```

**Cron delivery rule:** always deliver the report, even when empty. Never suppress it with
`[SILENT]`. If nothing was found, send the report with zeros.

## Edge Cases

- **No clippings:** report "Clippings found: 0" and still deliver the report.
- **No `Source URL`:** skip the row (not a clipping), note it in the report.
- **Duplicate `Source URL`:** skip, log as duplicate, no second row.
- **Ambiguous topic:** use the most prominent topic as the title, add extra tags.
- **No related project/area:** leave `Related` empty, report "no project/area match".
- **Very long clipping:** read the body in chunks, condense before writing.
- **Not a clipping:** skip - other kinds belong to `second-brain-inbox-curation`.
- **Confidential project/area matched:** file without that relation and flag the skip.
- **`Source URL` on tasks.google.com:** still process it - `references/google-tasks-source-pattern.md`.

## See Also

- `references/notion-conventions-check.md` - where the conventions live now
- `references/google-tasks-source-pattern.md` - clippings whose source is a Google Task
- `references/duplicate-detection-by-source-url.md` - duplicate detection
- `references/long-clipping-condensation.md` - condensing a long clipping
- `references/clipping-to-project-notes-pattern.md` - filing under a project/area

## Integration with Other Skills

- **notion-second-brain:** the contract - data sources, properties, markdown dialect, rate limit.
- **second-brain-inbox-curation:** the general inbox sweep; don't process the same Inbox row twice.
- **second-brain-action-items:** extracting tasks out of clippings.
- **second-brain-cross-linker:** keeps the new Notes rows connected.
- **second-brain-weekly-review:** weekly recap over what the processor filed.

## Anti-Patterns

- Don't process Inbox rows without a `Source URL`
- Don't skip linking - a related project/area must be set as a relation
- Don't create a topic-tag soup - only `status/*` and `type/*` tags
- Don't create a second row for a source URL you already have
- Don't forget to fix cross-references to the retired Inbox row
- Don't invent properties or select options - check `notion-second-brain`; don't delete the Inbox row - set `Status` and log it
- Don't assume conventions - read `references/notion-conventions-check.md` first
