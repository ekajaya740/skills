---
name: second-brain-summary
description: "Summarize content from the migrated second brain in Notion. Use when the user wants a summary of a specific note, project, area, topic, or date range. Triggers on: 'summarize', 'give me a summary of', 'recap', 'what's in my notes about', 'summarize my project', 'summarize my area', 'summarize today', 'summarize this week', 'what did I write about'. NOT for: cross-note synthesis with gap analysis (use second-brain-synthesis skill), inbox curation (use second-brain-inbox-curation skill), or internet research (use web search)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Summary, API]
    related_skills: [notion-second-brain, second-brain-synthesis, second-brain-inbox-curation, second-brain-action-items, second-brain-weekly-review]
---

# Second-Brain Summary

Summarize content from the second brain. The second brain lives in **Notion**: notes are rows in
the Notes data source, projects in Projects, areas in Areas, daily notes in Daily Notes. There is
no local vault, no QMD, no index, no reindex step — every retrieval is a data-source query or a
Notion search.

**Contract: `notion-second-brain`.** Read it before any call. It owns the data-source ids, the
property names, the select options, the markdown dialect, the rate limit and the token location.

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
ds() { python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$LEDGER" "$1"; }
NOTES_DS=$(ds Notes); DAILY_DS=$(ds "Daily Notes")
```

3 requests/second — space calls ~350 ms.

## Prerequisites

1. **Resolve the ids** from the ledger (above). If a name is missing, refresh it with
   `nb POST /v1/search '{"query":"Notes","filter":{"property":"object","value":"data_source"}}'`
   and update the ledger — never hand-edit ids.
2. **Search with the API, not with grep:** `POST /v1/data_sources/{id}/query` for property
   filters, `POST /v1/search` for titles. Notion search covers titles and properties, not
   arbitrary body text — for body content, query the data source and read the page bodies.

## When to Use This Skill

Use when the user wants:
- A **quick summary** of a single note, project, area, or topic
- A **daily/weekly recap** — "what did I write today this week?"
- A **project status recap** — "summarize where project X stands"
- A **topic overview** — "what do I have on topic X?"

Do NOT use for:
- Cross-note synthesis with gap analysis → use `second-brain-synthesis`
- Inbox curation → use `second-brain-inbox-curation`
- Internet research → use web search

## Summary Types & Retrieval Strategies

### Type 1: Summarize a Single Note

**Trigger:** "summarize [note name]" or "summarize the note about X"

1. Find the note — title search across pages:
   ```bash
   nb POST /v1/search '{"query":"<keyword>","filter":{"value":"page"},"page_size":20}'
   ```
   Or, when you already know the data source:
   ```bash
   nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"property":"Name","title":{"contains":"<keyword>"}}}'
   ```
2. Read the body: `GET /v1/pages/{id}/markdown` → `{"markdown":"...","truncated":false}`
3. Produce a structured summary following the Output Format below

### Type 2: Summarize a Project

**Trigger:** "summarize project X" or "recap my X project"

**⚠️ Confidential Guard (Check BEFORE Reading Project Content)**

Confidential rows carry the **Confidential** checkbox. Per the second-brain rule, only whitelisted
models — **Anthropic Claude** (all models) and **Ollama Cloud** (all models) — may read or write
confidential content. Any other provider (OpenAI, OpenRouter, xAI, etc.) is forbidden.

**Before reading project content:**
1. Find the project row and read its properties: filter `{"property":"Name","title":{"equals":"<name>"}}`
   and read the `Confidential` property. The relation properties of that row (Notes, Tasks) tell
   you which rows belong to it.
2. If `Confidential` is true AND the session is on a non-whitelisted model/provider → **do not
   read the linked notes or the project body**. Produce a summary noting the exclusion (e.g.
   "Project X is confidential and excluded — run on a whitelisted model to include").
3. Note the skip in the report so the human can re-run on a whitelisted model.

1. Read the project row's body (the durable facts, previously `overview.md`):
   `GET /v1/pages/{project_page_id}/markdown`
2. List the open tasks: query Tasks with `Project` relation contains the project page id
   and `Status != Done`, sorted by `Due` ascending.
3. List recent notes: query Notes with
   `{"property":"Project","relation":{"contains":"$PROJECT_PAGE_ID"}}` sorted by `Date` desc, `page_size` 5.
4. Read the 2-3 most relevant notes (`GET /v1/pages/{id}/markdown`)
5. Produce a structured summary (see Output Format below)

### Type 3: Summarize an Area

**Trigger:** "summarize area X" or "recap my X area"

**⚠️ Confidential Guard** — same check as Type 2, on the Areas row's `Confidential` property.

1. Read the area row's body (previously `03-Areas/<Name>/overview.md`)
2. List open tasks where `Area` contains the area page id
3. List recent notes where `Area` contains the area page id (sort `Date` desc, take 5)
4. Read the 2-3 most relevant notes
5. Produce a structured summary

### Type 4: Summarize a Topic

**Trigger:** "summarize what I have on X" or "what do I know about X"

1. Query the Notes data source for the topic across title and tags:
   ```bash
   nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"or":[
     {"property":"Name","title":{"contains":"<keyword>"}},
     {"property":"Tags","multi_select":{"contains":"<keyword>"}}]},
     "page_size":20}'
   ```
2. Also search page titles globally with `POST /v1/search` (it covers Projects, Areas, Notes,
   Decisions and Daily Notes in one call).
3. Read the top 3-5 most relevant results (`GET /v1/pages/{id}/markdown`)
4. Summarize findings grouped by source (project, area, standalone note)

Notion does not search body text — if a topic lives only in bodies, query the candidate rows and
read their markdown. Say how many rows you actually read.

### Type 5: Summarize by Date Range

**Trigger:** "summarize today", "summarize this week", "what did I write on [date]"

1. Daily notes for the date: query Daily Notes with
   `{"property":"Date","date":{"on_or_after":"<start>","on_or_before":"<end>"}}` sorted by `Date` ascending.
2. Notes across the period: query Notes with the same `Date` range, `page_size` 100.
3. Recently edited rows: `POST /v1/search` with
   `{"sort":{"timestamp":"last_edited_time","direction":"descending"},"page_size":20}`
4. Read and summarize the most relevant rows

## Output Format

**Every summary — regardless of type — MUST include these 4 sections:**

1. **Summary** — 3-5 sentences summarizing the main content. Written as a coherent paragraph, not
   bullet points.
2. **Key Points** — 3-5 bullet points of the most important takeaways from the content.
3. **Key Insights** — 1-3 insights, patterns, or observations that emerge from the content. Can be
   trends, contradictions, or implicit conclusions.
4. **Action Items** — List of actionable tasks (if any). If none, write "No action items."

### Output Template

```
## 📋 Summary: <Project/Area/Topic/Note Name>

**Type:** <Project / Area / Topic / Note / Date Range>
**Sources:** <N> row(s) from <data source(s)>

### Summary
<3-5 sentence paragraph summarizing the main content. Explain context, what's happening, and current state.>

### Key Points
- **<Point 1>:** <brief explanation>
- **<Point 2>:** <brief explanation>
- **<Point 3>:** <brief explanation>

### Key Insights
- **<Insight 1>:** <explanation — can be a trend, pattern, contradiction, or implicit conclusion>
- **<Insight 2>:** <explanation>

### Action Items
- [ ] <Task 1>
- [ ] <Task 2>

*No action items.* (if there are none)
```

The `#type/task` prefix is gone — a task is a row in the Tasks data source, not a checkbox
prefix. Render the action items as plain checkboxes here, and create the Task rows (```POST
/v1/pages` with parent `data_source_id`, `Status` = Todo, `Due`, `Priority`, `Project`/`Area`
relations and a `Source` relation back to the note) when the user asks for them to be tracked.
Name the source note in the `**Sources:**` line so the reader can open it, and mention pages in
the answer as `<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>` so
the links are clickable in Notion.

### Guidance Per Type

**Project/Area** — Summary explains the project/area status, what's being worked on, and current
state. Key Points cover milestones, decisions, and progress. Insights can be productivity trends,
recurring blockers, or priority shifts. Action Items come from the open Task rows related to the
project/area.

**Topic** — Summary explains what's known about the topic overall. Key Points grouped by source
(project, area, standalone note). Insights can be knowledge gaps, consistency across notes, or
evolution of understanding. Action Items if any tasks relate to the topic.

**Single Note** — Summary paraphrases the note content. Key Points capture core ideas. Insights
are observations about the note. Action Items if the note contains tasks.

**Date Range** — Summary explains what was written during the period. Key Points per day or per
theme. Insights are daily/weekly patterns, dominant themes. Action Items from notes in that period.

## Edge Cases

- **Note/project/area not found:** Say so honestly. Suggest similar names from the query results.
- **Empty project/area (no notes yet):** Report "No notes yet — only the overview and tasks exist."
- **Very long notes:** `GET /v1/pages/{id}/markdown` returns `truncated: true` for very large
  pages — summarize what you got and say it was truncated.
- **Ambiguous name matches:** List the matches (title + data source) and ask the user to clarify.
- **No results for topic search:** Say so. Suggest broadening the query (drop the Tags clause, or
  search a shorter keyword).
- **Relation filters return nothing:** a row may relate through `Related`/`Sources` instead of
  `Project`/`Area` — query both before declaring it empty.

## Integration with Other Skills

- **notion-second-brain:** the contract — data sources, properties, markdown dialect, rate limit.
- **second-brain-synthesis:** Use when the user needs cross-note synthesis with gap analysis. This
  skill is for simpler, single-entity summaries.
- **second-brain-inbox-curation:** Use for inbox processing. This skill is for reading/summarizing
  already-curated content.
- **second-brain-action-items:** Use for extracting structured tasks from raw notes. This skill is
  for summarizing, not task extraction.
- **second-brain-weekly-review:** Use for weekly recaps. This skill is for ad-hoc single-entity
  summaries.

## Anti-Patterns

- Don't skip any of the 4 required sections (Summary, Key Points, Key Insights, Action Items)
- Don't produce a wall of text — keep summaries scannable with bullets and headers
- Don't list every note — pick the most relevant/recent ones
- Don't fabricate content — only summarize what the API returned
- Don't confuse this with synthesis — no gap analysis, no contradiction resolution here
- Don't write Summary as bullet points — it must be a coherent paragraph (3-5 sentences)
- Don't leave Action Items empty without explicitly stating "No action items"
- Don't read a confidential row on a non-whitelisted model, and don't hide the skip
- Don't summarize from search snippets alone — read the page body before asserting what it says
