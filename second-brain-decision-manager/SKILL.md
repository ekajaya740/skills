---
name: second-brain-decision-manager
description: "Manage decisions in the migrated Notion second brain - create, supersede, and review decisions with full rationale. Use when the user is deliberating ('should I', 'help me decide', 'I'm torn between'), wants to record a decision, or review past decisions. NOT for: general note-taking (use second-brain-inbox-curation), or extracting decisions from raw notes (use second-brain-action-items)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Decisions, API]
    related_skills: [notion-second-brain, second-brain-action-items, second-brain-daily-note-curation, second-brain-synthesis, second-brain-weekly-review]
---

# Second-Brain Decision Manager

Manage decisions in the second brain. Every decision gets its own row with context, options,
rationale and consequences. Decisions are never deleted - only superseded.

The second brain lives in **Notion**. A decision is a row in the **Decisions** data source:
`Name`, `Date`, `Status` (Proposed, Accepted, Superseded, Overturned, Rejected), `Area`,
`Project`, `Supersedes` (relation to Decisions), `Rationale` (rich text), `Source` (relation to
Notes), `Confidential`. There is no `05-Decisions/` folder and no index file to append to.

**Contract: `notion-second-brain`.** Read it before any call - data-source ids, property names,
select options, markdown dialect, rate limit, token location.

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
DECISIONS_DS=$(ds Decisions); NOTES_DS=$(ds Notes); PROJECTS_DS=$(ds Projects); AREAS_DS=$(ds Areas)
```

3 requests/second - space calls ~350 ms.

## Prerequisites

1. **Search the second brain** for related notes, past decisions and principles before creating a
   new decision:
   ```bash
   nb POST /v1/search '{"query":"<topic>","page_size":30}'
   nb POST "/v1/data_sources/$DECISIONS_DS/query" '{"filter":{"property":"Name","title":{"contains":"<topic>"}}}'
   ```
2. **Read the decision template** - the *Decision* page under **Templates** in Notion, or the body
   structure in Step 3 below.

## Decision Trigger

When the user is deliberating - phrases like:
- "should I", "I'm thinking about", "which is better"
- "help me decide", "I'm torn between", "what do you think"
- "pros and cons", "weigh the options"

The agent MUST:
1. Search the second brain for related notes, past decisions and principles
2. Present structured options with pros/cons weighted by principles
3. Create a decision row in the **Decisions** data source
4. Make it visible in the decision log (a saved view - see Step 4)
5. Let the human make the final call - the agent advises, it does not decide

## Creating a New Decision

### Step 1: Determine the Title and Date

`Name` = a short, durable title (`2026-06-16 - Migration strategy`), `Date` = today. There is
no filename; the `Name` property is the label.

### Step 2: Build the Properties

```json
{
  "Name": {"title":[{"text":{"content":"Migration strategy"}}]},
  "Date": {"date":{"start":"2026-06-16"}},
  "Status": {"select":{"name":"Proposed"}},
  "Tags": {"multi_select":[{"name":"type/decision"},{"name":"status/active"}]},
  "Source": {"relation":[{"id":"<daily_note_or_source_page_id>"}]},
  "Project": {"relation":[{"id":"<project_page_id>"}]},
  "Rationale": {"rich_text":[{"text":{"content":"<one-line reason>"}]}]}
```

- `Status` = `Proposed` while it is still open; flip it to `Accepted` when the human decides.
- `Source` relation points back at the daily note or conversation note the decision came from.
- `Project` / `Area` relations link it to the owning row.
- `Rationale` is a rich-text property (2000-char cap) - the full reasoning goes in the body.
- The Decisions data source has no `Tags` property in the scaffold spec - if `Tags` is not
  present on the row, drop it rather than inventing a property.

### Step 3: Use the Decision Template Structure

Write the body as enhanced markdown in the page's `markdown` param:

```markdown
# <Decision Title>

**Status:** Proposed
**Date:** YYYY-MM-DD

## Context
<What prompted this decision? Background and situation.>

## Options Considered

### Option A: <Title>
- **Pros:** <list>
- **Cons:** <list>
- **Trade-offs:** <what you give up>

### Option B: <Title>
- **Pros:** <list>
- **Cons:** <list>
- **Trade-offs:** <what you give up>

## Decision
<The chosen option and why.>

## Rationale
<Full reasoning - principles that guided the choice, constraints, priorities.>

## Consequences
<Expected outcomes, both positive and negative. What changes as a result?>

## Related
- <mention-page url="https://www.notion.so/<PAGE_ID>">Related Note</mention-page>
- <mention-page url="https://www.notion.so/<PAGE_ID>">Principles</mention-page>
```

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$DECISIONS_DS"'"},
  "properties": { ...as built in Step 2... },
  "markdown": "# <Decision Title>\n\n**Status:** Proposed\n\n## Context\n..."
}'
```

### Step 4: Make It Visible in the Decision Log

The old `00-Inbox/Decision.md` checkbox index is now a **saved view** over the Decisions data
source. Create it once (it stays current by itself):

```bash
nb POST /v1/views '{
  "data_source_id": "'"$DECISIONS_DS"'",
  "name": "Decision Log",
  "type": "table",
  "configuration": {"type":"table","group_by":{"type":"select","property":"Status"}},
  "filter": {"property":"Status","select":{"does_not_equal":"Rejected"}},
  "sorts": [{"property":"Date","direction":"descending"}]
}'
```

No index file to append to, and no checkbox to tick - the view is the log.

## Superseding a Decision (Changing Your Mind)

When a decision is revisited and the conclusion changes:

### Step 1: Create the New Decision

Create the new row with the current date, and set `Supersedes` to the old row's page id:

```json
"Supersedes": {"relation":[{"id":"<old_decision_page_id>"}]}
```

### Step 2: Mark the Old Decision Superseded

```bash
nb PATCH /v1/pages/<old_decision_page_id> '{"properties":{
  "Status": {"select":{"name":"Superseded"}}}}'
```

There is no `superseded_by` property on the Decisions data source. Record the forward link in
the old row's body instead:

```bash
nb PATCH /v1/pages/<old_decision_page_id>/markdown '{"type":"update_content","update_content":{
  "content_updates":[{"old_str":"## Related",
    "new_str":"## Related\n- Superseded by <mention-page url=\"https://www.notion.so/<new_decision_page_id>\">New decision title</mention-page>"}]}}'
```

### Step 3: The Decision Log updates itself

The view filters and sorts live - the old row now shows `Status` = Superseded and the new row
appears. No index edit is needed.

### Step 4: Cross-Link

- New row: `Supersedes` relation -> the old row
- Old row: a mention of the new decision in its `## Related` section

**Never delete a decision - only supersede.**

## Decision Review

Periodically (weekly via cron or on-demand):

1. Query the Decisions data source for rows still open:
   ```bash
   nb POST "/v1/data_sources/$DECISIONS_DS/query" '{"filter":{"property":"Status","select":{"equals":"Proposed"}},
     "sorts":[{"property":"Date","direction":"ascending"}]}'
   ```
2. Check for decisions past their review date
3. Surface them for human follow-up
4. Update statuses as needed (`Accepted`, `Overturned`, `Rejected`)

## Naming

| Type | Pattern | Example |
|------|---------|---------|
| Active decision | `<YYYY-MM-DD> - <title>` in the Name property | `2026-06-16 - Migration strategy` |
| Superseded decision | same row, `Status` = Superseded, never deleted | |

## Integration

- **notion-second-brain:** the contract - data sources, properties, relations, views, rate limit.
- **second-brain-action-items:** extracting decisions from raw notes. This skill is for creating
  and managing decisions deliberately.
- **second-brain-daily-note-curation:** extracts decisions from daily notes automatically. This
  skill is for standalone decision management.
- **second-brain-synthesis:** gap analysis on a topic. This skill is for the decision lifecycle.
- **second-brain-weekly-review:** surfaces open decisions in the weekly recap.

## Anti-Patterns

- Don't make the decision for the user - present options, let them choose
- Don't skip the rationale section - "why" is more important than "what"
- Don't delete decisions - only supersede
- Don't forget to set `Status` = Accepted/Rejected when the human decides
- Don't skip cross-linking to the related project/area
- Don't create decisions without searching for existing related decisions first
- Don't invent a `superseded_by` property - write the forward link in the body
