---
name: second-brain-inbox-curation
description: "Inbox curation for the migrated Notion second brain - scan the Inbox data source, classify each note into its best home (Projects, Areas, Notes, Decisions, Archive), and send a Telegram notification after each run. Triggers on: 'curate inbox', 'inbox curation', 'process my inbox', 'triage the inbox'. NOT for: web clippings only (use second-brain-clipping-processor), task extraction (use second-brain-action-items), or weekly recaps (use second-brain-weekly-review)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Inbox, PARA, Curation, API]
    related_skills: [notion-second-brain, second-brain-clipping-processor, second-brain-action-items, second-brain-weekly-review, second-brain-project-area-creator]
---

# Second Brain Inbox Curation

Inbox curation. The inbox is a **mixed bag** - web clippings, random notes, reference material.
Scan the **Inbox** data source and route each row to its best home based on content: Projects,
Areas, Notes, Decisions, or Archive - wherever the content is relevant. Not everything goes to
archive; some become project notes, decisions or references.

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
INBOX_DS=$(ds Inbox); NOTES_DS=$(ds Notes); DECISIONS_DS=$(ds Decisions)
ARCHIVE_DS=$(ds Archive); PROJECTS_DS=$(ds Projects); AREAS_DS=$(ds Areas)
```

3 requests/second - space calls ~350 ms. See `references/cron-mode-workflow.md`.

## Telegram Notification

After every curation run, send a summary to the user via Telegram. **Cron job delivery:** in a
cron job the final response IS the notification - the system delivers it automatically. Do NOT
call `send_message` or any Telegram tool; just produce the summary as your final response
output. Format:

```
📥 Inbox Curated (YYYY-MM-DD HH:MM)

Processed: X notes
• <note title> → <destination>
...
```

If the inbox is empty:
```
✅ Inbox empty - nothing to curate (YYYY-MM-DD HH:MM)
```

## What This Skill Does

1. **Scan** the Inbox data source (`Status` = `Untriaged`)
2. **Classify** each row into its best PARA home
3. **Route** it: create the destination row, retire the Inbox row
4. **Notify** the user

## Linked References (in `references/`)

`cron-mode-workflow.md` (cron constraints) · `tag-audit-script.md` (Tags cleanup) ·
`curation-pattern-clippings.md` · `clipping-to-project-notes.md` ·
`duplicate-resolution.md` · `decision-archive-rule.md` · `cross-reference-update.md` ·
`resource-organization.md` / `reorganize-resources-by-project.md` ·
`area-payment-index.md` / `payment-tracking-in-tasks.md` ·
`saving-images-to-project-notes.md` · `google-tasks-integration.md`

## Decision & Relation Handling

When curating an inbox row, also check whether it:

1. **Is a decision** -> create a row in the **Decisions** data source (Status `Proposed`,
   `Rationale`, `Source` relation to the inbox row); flip it to `Accepted` when the human
   decides. The decision log is a saved view - see `references/decision-archive-rule.md`.
2. **Relates to an existing decision** -> append it as linked context (a `Source` relation on the
   decision row, or a mention in the decision body). Don't create a duplicate decision.
3. **Relates to an existing project/area** -> create a **Notes** row with a `Project` or `Area`
   relation, and a `Source` relation back to the inbox row.

Inbox rows are diverse - clippings, random thoughts, reference material. Unclassifiable rows stay
in the Inbox (`Status` = `Untriaged`) and are flagged in the report.

## Tagging Rules - Status & Category Only

Tags answer exactly **two questions**: **Status?** (`status/active`, `status/seed`,
`status/archived`, `status/evergreen`) and **Category?** (`type/project`, `type/area`,
`type/task`, `type/meeting`, `type/decision`, `type/learning`, `type/atomic`,
`type/reference`, `type/research`, `type/notebook`, `type/notebook-notes`,
`type/sticky-notes`, `type/overview`, `type/project-note`, `type/personal-review`,
`type/status-report`, `type/ai-doc`, `type/code-review`), plus the flexible categories
`confidential`, `fitness`, `wedding`, `daily`, `tasks`, `testing`.

**Do NOT create tags for:** project names (use the `Project` relation instead), topics, tools,
muscles, body parts - they belong in the body or in relations.

## PARA Classification Rules

### ⚠️ Confidential Project Guard (Check BEFORE Classification)

Confidential rows carry the **Confidential** checkbox. Only whitelisted models - **Anthropic
Claude** (all models) and **Ollama Cloud** (all models) - may read or write confidential content;
any other provider (OpenAI, OpenRouter, xAI, etc.) is forbidden. Read the target Projects/Areas
row's `Confidential` property before classifying. If it is true AND the session is on a
non-whitelisted model -> **do not create a row related to it**; you may still archive the inbox row
and process non-confidential matches. Note the skip in the run report.

### Projects - active work with a deadline or defined outcome

Signals: a specific deliverable, milestone or sprint; references a project that already exists in
the **Projects** data source; has action items, tasks or a timeline; words "build", "launch",
"deploy", "implement", "fix", "PR", "feature", "release"; **has a clear end condition**.

Destination: a **Notes** row with a `Project` relation.
- **ALWAYS list existing projects and areas first** (query `$PROJECTS_DS` and `$AREAS_DS`)
- if a match exists, use that name - **never invent a new project name when one already exists**
- create the project row only if no match exists (see `second-brain-project-area-creator`)

### Areas - ongoing responsibility or interest area

Signals: a life domain (health, fitness, career, learning, finance, relationships); references an
area that already exists in the **Areas** data source; no specific deadline - a continuous
practice; words "routine", "habit", "journal", "diary", "tracking", "weekly", "daily practice".

Destination: a **Notes** row with an `Area` relation.

**⚠️ Pitfall - module/component notes belong under the project, not a work area:** a note about a
module, component or subsystem of a known project (e.g. `portal-batch` is a module of the MIPS
project) belongs to that **project**, not to a general work area like Work-Of-Ekajaya. Decision
test: *"If I were working on this project, would I want this note in the project folder?"* If yes, it
is a project note. Use a work area only for notes about general professional practice that do not
tie to a specific deliverable.

### Notes (standalone) - reference material, topic of interest

Signals: an article, tutorial, guide or reference; about a specific technology, concept or tool;
words "how to", "guide", "tutorial", "explained", "overview", "cheatsheet". Destination: a **Notes**
row (Type=Reference) with no Project/Area relation.

### Duplicate Detection - Delete, Don't Archive

Before classifying, check for a duplicate: compare `Source URL` values (same URL = duplicate),
then titles (near-identical), then content (first 200 characters substantially the same). Keep the
first/best version, then delete the duplicate row - the one exception to "never delete a page". See
`references/duplicate-resolution.md`.

### Decisions - active decisions with rationale

Signals: asks "should I", compares options, or documents a choice with reasoning; references an
existing decision. Destination: a **Decisions** row; the decision log is a saved view.

### Archive - inactive, completed, or no longer relevant

Signals: the content is outdated or superseded, or already processed elsewhere. **Duplicates are
NOT archived - they are deleted.**

### Ambiguous - Leave in Inbox + Flag

Leave `Status` = `Untriaged` and note it in your response for the user to review.

## Decision Archive Rule (Overwrite -> Archive, Never Delete)

When a decision is revisited and the conclusion changes: create the new **Decisions** row with
`Supersedes` -> the old row, set the old row's `Status` = `Superseded`, record the forward link
in its body, and **never delete a decision - only supersede**.

## Step-by-Step Execution

1. **List the inbox rows:**
   ```bash
   nb POST "/v1/data_sources/$INBOX_DS/query" '{"filter":{"property":"Status","select":{"equals":"Untriaged"}},
     "sorts":[{"property":"Captured","direction":"ascending"}],"page_size":50}'
   ```
2. **For each row:**
   a. read the full content (`nb GET /v1/pages/{id}/markdown`, `nb GET /v1/pages/{id}`)
   b. apply the PARA classification rules + decision/relation handling
   c. if ambiguous -> skip, report it in the Telegram notification
   d. if classified: create the destination row - a condensed **Notes** row (Type=Reference)
      for reference material, a **Notes** row with a Project/Area relation for project/area content,
      a **Decisions** row for a decision, an **Archive** row for outdated content. A confirmed
      duplicate is the only row that gets deleted.
   e. retire the inbox row - Notion has no move endpoint, so set `Status`:
      `nb PATCH /v1/pages/<inbox_page_id> '{"properties":{"Status":{"select":{"name":"Filed"}}}}'`
      (`Dropped` for a deliberate skip, `Processing` while it is in flight)
   f. fix cross-references - relations that still point at the old row, and inline mentions of the
      old page id (see `references/cross-reference-update.md`)
   g. log the action

   **⚠️ User explicitly names a new area/project:** when the user says "it's an X area" or "this
   is a Y project", create the Projects/Areas row immediately as part of the same task - do not
   defer setup to a separate step.

3. **Notify the user via Telegram** with a summary of what was curated.

4. **No git commit** - the vault is not a git repo any more; Notion holds the content.

### Google Tasks Exclusion List

These Areas/Projects have **no** Google Tasks list (second brain only): `PT-SUM-Digital-Konsultan`
(Area), `Joki` (Area), `ADHD` (Area), `dotfiles` (Project).

## Google Tasks Inbox Curation

Parallel to the second-brain inbox curation - the Google Tasks "Inbox" list is also a mixed bag
that needs routing. Google Tasks is **not** Notion; use the `gws` CLI.

**This step needs Google Tasks OAuth scope.** The stored credential at
`~/.config/gws/credentials.json` has no `tasks` scope, so every Google Tasks call returns
`403 Request had insufficient authentication scopes`. Re-consent with the `tasks` scope first, or
skip this section and leave Google Tasks alone - the Notion side of the curation still works.

1. **List:** `gws-core tasks tasklists list --format json`, then
   `gws-core tasks tasks list --params '{"tasklist": "INBOX_LIST_ID"}' --format json`
2. **For each task:** belongs to an existing project/area -> move to that list; needs a new
   project/area -> create the list + move; is a quick note -> create an **Inbox** row in Notion and
   complete the task; is done -> mark complete
3. **Move** (no native move - copy + delete): `gws-core tasks tasks insert --params '{"tasklist":
   "DEST_LIST_ID"}' --json '{"title": "Task name"}'` then `gws-core tasks tasks delete --params
   '{"tasklist": "SOURCE_LIST_ID", "task": "TASK_ID"}'`
4. **Complete** (use `patch`, not `update`): `gws-core tasks tasks patch --params '{"tasklist": "LIST_ID",
   "task": "TASK_ID"}' --json '{"status": "completed"}'`
5. **Create a list:** `gws-core tasks tasklists insert --json '{"title": "[P] New Project"}'`

The `gws` wrapper on this box points at the removed `~/.hermes` tree; the working binary is
`gws-core` (see `references/google-tasks-integration.md` for the env vars and the scope gap).

## Schedule

Run daily.

## Anti-Patterns

- Don't process a row twice - set `Status` = `Processing` as soon as you start
- Don't run inbox curation and the clipping processor on the same Inbox row
- Don't invent project or area names when one already exists - list them first
- Don't create topic tags - only `status/*` and `type/*`
- Don't delete decisions - only supersede
- Don't delete anything except a confirmed duplicate
- Don't forget to fix relations and mentions that pointed at the retired row
- Don't write a `[[wikilink]]` - use relations and `<mention-page>`
