---
name: second-brain-daily-note-curation
description: "Weekly daily note curation in the migrated Notion second brain - extract project/area summaries and decisions from Daily Notes rows, then archive the originals. Dedicated weekly cron. Triggers on: 'curate daily notes', 'process daily notes', 'daily note curation'. NOT for: inbox triage (use second-brain-inbox-curation), clipping processing (use second-brain-clipping-processor), or weekly recap (use second-brain-weekly-review)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Daily-Notes, Curation, API]
    related_skills: [notion-second-brain, second-brain-inbox-curation, second-brain-clipping-processor, second-brain-action-items, second-brain-weekly-review]
---

# Second-Brain Daily Note Curation (Weekly)

Curate daily notes. Daily notes are **ephemeral working logs** - they help you complete
projects/areas and make decisions. Process weekly.

The second brain lives in **Notion**. A daily note is a row in the **Daily Notes** data source
(`Name` = `YYYY-MM-DD`), replaced by **Notes** rows, **Decisions** rows and an **Archive** row.
There is no file to move and no git commit to make.

**Contract: `notion-second-brain`.** Read it first - data-source ids, property names, select
options, markdown dialect, rate limit, token location.

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
DAILY_DS=$(ds "Daily Notes"); NOTES_DS=$(ds Notes); DECISIONS_DS=$(ds Decisions)
ARCHIVE_DS=$(ds Archive); PROJECTS_DS=$(ds Projects); AREAS_DS=$(ds Areas)
```

3 requests/second - space calls ~350 ms.

## What This Skill Does

1. **Scan** the Daily Notes data source - read every row for the period
2. **Create Notes rows** related to the Project/Area the content belongs to
3. **Extract decisions** into the **Decisions** data source
4. **Archive** the original - an Archive row, and the Daily Note marked archived
5. **Notify** the user via Telegram

## Telegram Notification

After every curation run, send a summary to the user via Telegram.

**Cron job delivery:** when running as a cron job, the final response IS the notification - the
system delivers it automatically. Do NOT call `send_message` or any Telegram tool; just produce
the summary as your final response output. The format below still applies.

```
📅 Daily Notes Curated (YYYY-MM-DD HH:MM)

Processed: X daily notes
• <date> → <project/area notes created> | decisions: <count>
• <date> → no matches, archived
...
```

If there is nothing to curate:
```
✅ No daily notes to curate (YYYY-MM-DD HH:MM)
```

## Step-by-Step Execution

### 0. Read the conventions first

The vault `AGENTS.md` is gone. The rules now live in `notion-second-brain` and in
`notion-scaffold-and-beautify.md` (migration workspace). The contract owns the property names,
the select options and the status mapping.

### 1. List daily notes to curate

```bash
nb POST "/v1/data_sources/$DAILY_DS/query" '{"filter":{"and":[
  {"property":"Date","date":{"on_or_after":"<period_start>","on_or_before":"<period_end>"}}]},
  "sorts":[{"property":"Date","direction":"ascending"}],"page_size":100}'
```

A Daily Note that was already curated has an **Archive** row pointing at it (`Original Path`) -
skip those. A weekly review row is named `<MONDAY>-<SUNDAY>-weekly-review`; it is a Daily Notes
row, not a daily note to curate.

### 1b. Check for an existing weekly review

If a weekly review covers the dates you are curating, use it as a reference - it may already
contain synthesized insights, decisions and action items. Do not re-create it; focus on extracting
project/area summaries and decisions.

### 2. For each daily note

**a. Read the full row** - `nb GET /v1/pages/{id}/markdown` plus `nb GET /v1/pages/{id}`
for the properties.

**b. Analyze for related Projects/Areas** - list them first: query `$PROJECTS_DS` and
`$AREAS_DS` with `{"page_size":100}` and read their `Confidential` flags.

**⚠️ Confidential-project guard (check BEFORE creating any summary).** Confidential rows carry
the **Confidential** checkbox. Only whitelisted models - **Anthropic Claude** (all models) and
**Ollama Cloud** (all models) - may read or write confidential content; any other provider
(OpenAI, OpenRouter, xAI, etc.) is forbidden.

When a daily note maps to a confidential project/area:
- On a **non-whitelisted** model/provider → do NOT create a Notes row related to it, and do not
  read that project's rows. You MAY still archive the daily note and create summaries for the
  *non-confidential* matches in the same note.
- Note the skip in the run report so the human can re-run on a whitelisted model.
- If unsure whether a target is confidential, read its `Confidential` property before writing.

**c. Create summary Notes rows** for the related Project/Area:
- `Name` = `<YYYY-MM-DD> - <short title>`; `Type` = Note; `Status` = Active;
  `Date` = the daily note's date
- `Tags` = `status/active` (plus optional flexible categories: fitness, wedding, daily, tasks,
  testing, confidential). No topic tags - topics belong in the body and the relations.
- `Project` or `Area` relation = the owning row; `Source` relation = the daily note row
- Body: a concise summary of the parts relevant to that project/area, as enhanced markdown

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$NOTES_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"2026-10-19 — Concert setup"}}]},
    "Type": {"select":{"name":"Note"}},
    "Status": {"select":{"name":"Active"}},
    "Date": {"date":{"start":"2026-10-19"}},
    "Tags": {"multi_select":[{"name":"status/active"}]},
    "Area": {"relation":[{"id":"'"$AREA_PAGE_ID"'"}]},
    "Source": {"relation":[{"id":"'"$DAILY_NOTE_ID"'"}]}
  },
  "markdown": "# 2026-10-19 — Concert setup\n\n**Source:** <mention-page url=\"https://www.notion.so/'"$DAILY_NOTE_ID"'\">2026-10-19</mention-page>\n\n..."
}'
```

**d. Only create** summaries when the content genuinely relates: a daily note about a relationship
→ no match, skip; a daily note about concert setup → relates to Work-Of-Ekajaya, create the
summary; multiple matches → a summary for each one.

**e. Cross-link** - the `Source` relation points back at the daily note (one side only; Notion
mirrors it). Optionally add an inline mention of the new row in the project's body.

**f. Extract decisions** → create a row in the **Decisions** data source:
- `Name` = the decision title, `Date` = the daily note's date
- `Status` = `Proposed` (the human decides), `Tags` = `type/decision`, `status/active`
- `Source` relation = the daily note row
- `Rationale` rich text = the reasoning captured from the note
- Body follows the decision template (Context, Options Considered, Decision, Rationale,
  Consequences, Related) - see the decision-note template page under **Templates** and
  `second-brain-decision-manager`
- Only extract a decision when the note contains a choice/comparison with reasoning
- The `Decision.md` index is now a **view** of the Decisions data source - create it once with
  `POST /v1/views` (type table, sorted by Date) and it stays current. No index file to update.

### 3. Archive the original

Notion has no move endpoint, so archiving a daily note is two writes:

1. An **Archive** row that points at the original:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$ARCHIVE_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"2026-10-19"}}]},
    "Type": {"select":{"name":"Note"}},
    "Original Path": {"rich_text":[{"text":{"content":"'"$DAILY_NOTE_ID"'"}}]},
    "Archived": {"date":{"start":"2026-10-21"}},
    "Related": {"relation":[{"id":"'"$DAILY_NOTE_ID"'"}]}
  }
}'
```


2. The Daily Note row itself is marked as curated - set its `Tags` to include `archived`.
   **Never delete a page by default** - archive and log it.

**Always archive originals.** Daily notes are ephemeral; they should not stay in the Daily Notes
data source indefinitely.

### 4. No Reindex, No Git Commit

No QMD, no index, no reindex step - nothing to refresh after writing. The vault is not a git repo
any more: Notion holds the content, so there is no commit and no push. Proceed straight to the
notification.

## Rules

**Names** - archived daily notes keep their name (`YYYY-MM-DD`); summary notes are
`<YYYY-MM-DD> - <short title>`; decision notes carry the decision title.

**Properties** - summary notes use the standard Notes property set, decision notes the Decisions
property set, and the `Source` relation points back at the original daily note.

**Google Tasks** - this skill does NOT create Tasks; extract them with
`second-brain-action-items`.

**Decision Archive Rule** - superseded decisions are never deleted: the old row gets `Status` =
`Superseded` and the new row's `Supersedes` relation points at it (see
`second-brain-decision-manager`).

## Integration

- **notion-second-brain:** the contract - data sources, properties, relations, rate limit.
- **second-brain-inbox-curation:** inbox → PARA classification (as needed)
- **second-brain-clipping-processor:** inbox clippings with a Source URL
- **second-brain-action-items:** extract tasks from raw notes (call separately if needed)
- **second-brain-decision-manager:** the decision template and the supersede flow
- **second-brain-weekly-review:** the weekly recap that summarises what this skill curated

## Schedule

Run weekly on Sunday.

## Pitfalls

- **Don't archive before extracting** - create summaries and decisions first, then archive
- **Don't create Tasks** in this skill; that is `second-brain-action-items`' job
- **Archived daily notes keep their name** - no rename
- **Empty daily note (all template, no content)** - still archive it, no summary needed
- **Use the page `markdown` param, not shell heredocs** - build the body in a file and POST it,
  so shell metacharacters (`&`, `<`, `>`) never reach the shell
- **The decision index is a view now** - create it once with `POST /v1/views`, never append to a
  markdown file
- **Subdirectory daily notes** - the old `Weekly Review/` subfolder is now a Daily Notes row
  named `<MONDAY>-<SUNDAY>-weekly-review`; skip it during curation
- **The contract skill is authoritative** - property names, select options and the status mapping
  come from `notion-second-brain`, never from memory
- **Confidential projects need a whitelisted model** - content that maps to a confidential
  project/area (e.g. Mitsukoshi-Isetan) must not be summarized by a non-whitelisted model. Skip
  that match, archive the original, flag it in the report.
- **Weekly review may already exist** - check the Daily Notes rows for a
  `<MONDAY>-<SUNDAY>-weekly-review` row first and use it as a reference
- **Daily notes already archived** - check the Archive data source for an `Original Path` entry
  pointing at the row before processing it again
