---
name: second-brain-action-items
description: "Convert raw notes into a structured list of action items and file them in Notion. Use when the user pastes notes and wants to extract tasks, decisions, and information. Triggers on: 'extract action items', 'what are the action items', 'turn these notes into tasks', 'parse tasks from', 'action items from these notes', 'buat action items', 'ambil task dari catatan'. NOT for: summarizing content (use second-brain-summary skill), cross-note synthesis (use second-brain-synthesis skill), or inbox curation (use second-brain-inbox-curation skill)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Tasks, Action-Items, API]
    related_skills: [notion-second-brain, second-brain-summary, second-brain-synthesis, second-brain-inbox-curation, second-brain-weekly-review]
---

# Second-Brain Action Items

Convert raw notes into a clear, structured list of action items. Separate information, decisions, and
tasks. Make every task specific and actionable.

The second brain lives in **Notion**. A task is a **row in the Tasks data source**, not a checkbox
inside a note, and there is no Obsidian Tasks plugin to query. The old `#type/task` prefix is gone:
task state now lives in the `Status` and `Priority` properties of a Task row.

**Contract: `notion-second-brain`.** Read it before any call — it owns the data-source ids, the
property names, the markdown dialect, the rate limit and the token location. Never invent a
property or a select option.

## Environment

```bash
export WORKSPACE="${WORKSPACE:-$HOME/Documents/01-Projects/Notion-Migration}"
[ -f "$WORKSPACE/.env" ] && set -a && . "$WORKSPACE/.env" && set +a
export NOTION_API_VERSION=2026-03-11
export NOTION_API_TOKEN="$NOTION_API_KEY:?NOTION_API_KEY missing - put it in $WORKSPACE/.env}"

nb() {  # nb METHOD PATH [json-body]
  curl -sS -X "$1" "https://api.notion.com$2"     -H "Authorization: Bearer $NOTION_API_TOKEN"     -H "Notion-Version: $NOTION_API_VERSION"     -H "Content-Type: application/json"     $3:+-d "$3"
}

LEDGER="$WORKSPACE/migration/ledger/notion_db_ids.json"
TASKS_DS=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['Tasks'])" "$LEDGER")
NOTES_DS=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['Notes'])" "$LEDGER")
```

3 requests/second — space calls ~350 ms. Token lives in `$WORKSPACE/.env` (or an exported env var);
`~/.hermes` no longer exists.

## When to Use This Skill

Use when the user:
- Pastes raw notes and wants action items extracted
- Says "extract action items from these notes"
- Says "turn this into tasks" or "what needs to be done?"
- Has meeting notes, brainstorm output, or journal entries that contain tasks

Do NOT use for:
- Summarizing content → use `second-brain-summary`
- Cross-note synthesis → use `second-brain-synthesis`
- Inbox curation → use `second-brain-inbox-curation`

## Extraction Rules

### 1. Separate Three Categories

| Category | Description | Example |
|---|---|---|
| **Information** | Facts, context, background — not actionable | "The server is running Ubuntu 22.04" |
| **Decisions** | Choices that were made — record for reference | "We decided to use PostgreSQL over MySQL" |
| **Tasks** | Specific actions that someone needs to do | "Set up PostgreSQL database on the server" |

Decisions are filed in the **Decisions** data source (Status `Proposed`, `Rationale` rich text),
information is filed in **Notes**, tasks in **Tasks**.

### 2. Task Quality Rules

Every task MUST be:
- **Specific** — "Set up PostgreSQL" not "Handle database stuff"
- **Actionable** — starts with a verb (create, update, review, contact, deploy, etc.)
- **Assignable** — clear who does it (or marked "not specified")
- **Dated** — has a deadline or marked "not specified"

### 3. Task Parsing Heuristics

Look for these signals in the notes:
- Bullet points or numbered lists
- Phrases: "need to", "should", "must", "TODO", "action item", "follow up", "will do", "going to"
- Verbs at the start of lines: "Create...", "Update...", "Review...", "Contact..."
- Lines with @mentions or names followed by actions
- Lines with dates or deadlines

### 4. Handling Ambiguity

- If something sounds like a task but is vague → still extract it, but rephrase to be more specific
- If a task has no clear owner → assign "not specified"
- If a task has no deadline → mark "not specified" (leave `Due` empty on the Task row)
- If you're unsure whether it is a task or information → put it in Information with a note

## Output Format

**Every extraction MUST produce this structure:**

```
## 📋 Action Items

**Source:** <brief description of the note content>
**Extracted:** <N> tasks, <N> decisions, <N> information items

---

### ✅ Tasks

| # | Task | Owner | Deadline | Priority |
|---|------|-------|----------|----------|
| 1 | <specific action> | <name or "not specified"> | <date or "not specified"> | <high / medium / low> |
| 2 | <specific action> | <name or "not specified"> | <date or "not specified"> | <high / medium / low> |

---

### 📌 Decisions Made

- **<Decision>:** <brief context>

---

### ℹ️ Information / Context

- <Fact or context item 1>
- <Fact or context item 2>

---

### 📝 Notes

<Any observations, ambiguities, or follow-up questions about the extracted items>
```

The `#type/task` prefix is gone from the table — task state is carried by the Task row's `Status`
and `Priority` properties, and the `type/task` tag survives as a Tags value on the note.

### Priority Guidelines

| Priority | Signals | Notion `Priority` |
|---|---|---|
| **High** | "urgent", "ASAP", "critical", "blocker", "today", "immediately", explicit near deadline | `P0` |
| **Medium** | "this week", "soon", "important", no deadline but clearly needed | `P2` |
| **Low** | "when possible", "nice to have", "eventually", "backlog", no urgency indicated | `P3` |

If no priority signal is detected, default to **Medium** (P2). Use `P1` only when the notes say
"important" *and* name a deadline inside the week.

## Writing the result to Notion

When the user wants the extraction filed (or the notes come from the second brain), persist it:

1. One **Notes** row holding the markdown above — `Type` = Note, `Status` = Active, `Date` = today,
   `Tags` = `type/task` (plus any `status/` tag that has no Notion select option).
2. One **Tasks** row per task, related to that note:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$TASKS_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"Set up PostgreSQL database on the server"}}]},
    "Status": {"select":{"name":"Todo"}},
    "Priority": {"select":{"name":"P2"}},
    "Due": {"date":{"start":"2026-10-28"}},
    "Source": {"relation":[{"id":"'"$NOTE_ID"'"}]}
  }
}'
```

- `Source` is a relation to the Notes row the task came from — one side only, Notion relations are
  bidirectional.
- `Project` / `Area` relations are set when the user named one.
- `Due` is omitted (not null-filled) when the deadline is "not specified".
- `Confidential` is checked only when the notes are private.

3. Decisions go to the **Decisions** data source:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$DECISIONS_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"Use PostgreSQL over MySQL"}}]},
    "Date": {"date":{"start":"2026-10-21"}},
    "Status": {"select":{"name":"Accepted"}},
    "Rationale": {"rich_text":[{"text":{"content":"Operational team already knows Postgres."}}]},
    "Source": {"relation":[{"id":"'"$NOTE_ID"'"}]}
  },
  "markdown": "# Use PostgreSQL over MySQL\n\n**Status:** Accepted\n**Date:** 2026-10-21\n\n## Context\n..."
}'
```

4. If the user only asked to *read* the notes ("what are the action items?"), return the four
   sections in chat and do **not** create anything.

Read the note body back to confirm: `GET /v1/pages/{"<id>"}/markdown`.
Long bodies: keep a single markdown payload under 5000 blocks; split long tables into several
Notes rows rather than truncating.

## Edge Cases

- **No tasks found:** Say so explicitly. "No actionable tasks found in these notes. Here's the
  information and decisions extracted:" then show those sections.
- **Very long notes:** Extract all tasks but cap the output at ~20 tasks. If there are more, note
  "Showing first 20 tasks — N more items detected."
- **All information, no tasks:** Still produce the output format but show "0 tasks" and populate
  Information and Decisions.
- **Unclear ownership:** Use "not specified" — don't guess.
- **Conflicting deadlines:** Use the one that appears most certain. Note the conflict in the Notes
  section.
- **Tasks embedded in prose:** Parse them out into the table format. Don't leave them as paragraphs.
- **Duplicate task:** Query the Tasks data source for an existing row with the same `Name` and
  `Project`/`Area` before creating — update it instead of creating a second row.

## Integration with Other Skills

- **notion-second-brain:** the contract — data sources, properties, markdown dialect, rate limit.
- **second-brain-summary:** Use when the user wants a summary of content. This skill is for
  extracting actionable tasks.
- **second-brain-synthesis:** Use for cross-note synthesis. This skill works on a single paste of
  raw notes.
- **second-brain-inbox-curation:** Use for inbox processing. This skill is for ad-hoc note parsing.
- **second-brain-weekly-review:** Use for weekly recaps. This skill is for extracting tasks from a
  single paste.

## Anti-Patterns

- Don't leave the Tasks table empty without explanation
- Don't make up deadlines or owners — use "not specified" and leave `Due` empty
- Don't produce vague tasks like "Handle the thing" — rephrase to be specific
- Don't skip the Decisions and Information sections even if the user only asked for tasks
- Don't mix information and tasks — keep them in separate sections
- Don't forget to assign priority to each task
- Don't create Task rows for information items, and don't file a task only in the note body — a task
  is a row in the Tasks data source
- Don't delete an existing Task row to "replace" it; update it
