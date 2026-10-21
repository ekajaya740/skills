---
name: second-brain-operations
description: "General second brain operation - orchestrates the full PARA workflow in Notion: daily inbox curation, clipping processing, daily note curation, weekly review, on-demand summary/synthesis/action-items. Use when the user asks about how the second brain works, what the system does, what skills are available, or wants to run a full cycle. Triggers on: 'how does the second brain work', 'run second brain', 'second brain operations', 'what skills do you have for my second brain', 'explain the system', 'full cycle'. NOT for: running a specific single skill (use that skill directly), or content questions (use second-brain-synthesis or second-brain-summary)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Operations, PARA, API]
    related_skills: [notion-second-brain, second-brain-inbox-curation, second-brain-clipping-processor, second-brain-daily-note-curation, second-brain-weekly-review, second-brain-summary, second-brain-synthesis, second-brain-action-items, second-brain-cross-linker, second-brain-decision-manager, second-brain-project-area-creator]
---

# Second-Brain Operations

Orchestrate the full second-brain workflow. This skill is the **control panel** - it explains how
the system fits together, when each skill runs, and how to operate the second brain day-to-day.

The second brain lives in **Notion**. There is no vault folder tree any more: the structure is nine
data sources plus a Templates page.

**Contract: `notion-second-brain`.** Read it before any call - data-source ids, property names,
select options, markdown dialect, rate limit, token location.

## Environment

```bash
export WORKSPACE="${WORKSPACE:-$HOME/Documents/01-Projects/Notion-Migration}"
[ -f "$WORKSPACE/.env" ] && set -a && . "$WORKSPACE/.env" && set +a
export NOTION_API_VERSION=2026-03-11
export NOTION_API_TOKEN="${NOTION_API_KEY:?NOTION_API_KEY missing - put it in $WORKSPACE/.env}"
```

3 requests/second - space calls ~350 ms.

## Structure

| Data source | Holds |
|---|---|
| **Inbox** | capture - raw notes, clippings, random thoughts (`Status` = Untriaged) |
| **Daily Notes** | journal - daily working logs (ephemeral); weekly reviews live here too |
| **Projects** | active work with deadlines/deliverables |
| **Areas** | ongoing responsibilities & interests |
| **Tasks** | every actionable item, related to a project/area and a source note |
| **Notes** | reference material, tutorials, guides, project/area notes |
| **Decisions** | architectural & life decisions with rationale |
| **Archive** | inactive/completed content (old daily notes, retired notes) |
| **Templates** | plain template pages (13) under the Templates parent page |

Root page: `3f04c3376067800f8d03c40b25d6fa0c` = "Second Brain".

## Available Skills

| Skill | What It Does | When It Runs |
|-------|-------------|-------------|
| **notion-second-brain** | the contract: data sources, properties, markdown, rate limit | always - read it first |
| **second-brain-inbox-curation** | scan the Inbox, classify each row into its PARA home | Cron: daily 09:00 |
| **second-brain-clipping-processor** | process web clippings (Source URL) -> Notes rows | Cron: daily 20:00 |
| **second-brain-daily-note-curation** | extract summaries + decisions from daily notes, archive originals | Cron: Sunday 10:00 |
| **second-brain-weekly-review** | generate the 6-section weekly review | Cron: Sunday 04:00 |
| **second-brain-summary** | quick summary of a single note/project/area/topic | On-demand |
| **second-brain-synthesis** | cross-note synthesis + gap analysis | On-demand |
| **second-brain-action-items** | extract tasks/decisions/info from raw notes | On-demand |
| **second-brain-cross-linker** | find orphaned rows, connect related notes | On-demand |
| **second-brain-decision-manager** | create, supersede and review decisions | On-demand |
| **second-brain-project-area-creator** | create a new project or area | On-demand |
| **second-brain-skills-autofix** | keep these skills consistent with the contract | On-demand |
| **email-to-vault-resource** | pull documents out of email into Drive + a Notes row | On-demand |
| **project-code-review** | review a codebase, write three Notes rows | On-demand |

## Daily Rhythm

### Every Day (09:00) - Inbox Curation
- Cron: `Inbox Curation`
- Queries the Inbox data source for `Status` = Untriaged
- Classifies into Projects, Areas, Notes, Decisions or Archive
- Detects duplicates -> deletes them
- Reports to Telegram

### Every Day (20:00) - Clipping Processing
- Cron: `clipping-processor-daily`
- Queries the Inbox data source for `Kind` = Clipping
- Adds properties, links to related projects/areas, files as Notes rows
- Detects duplicates by Source URL
- Reports to Telegram (even if empty)

### Every Sunday (04:00) - Weekly Review
- Cron: `weekly-review-sunday`
- Gathers all second-brain content from the past week
- Produces the 6-section review: Summary, Projects, Decisions, Insights, Action Items, Next Focus
- Saves it as a Daily Notes row named `<MONDAY>-<SUNDAY>-weekly-review`

### Every Sunday (10:00) - Daily Note Curation
- Cron: `Daily Note Curation`
- Processes the daily notes from the past week
- Extracts relevant content -> Notes rows related to a project/area
- Extracts decisions -> Decisions rows
- Archives the original daily notes (Archive rows)
- Reports to Telegram

## On-Demand Operations

### Summarize Something
```text
"summarize project X"
"summarize my notes on Y"
"recap this week"
```
-> loads the `second-brain-summary` skill

### Synthesize Across Notes
```text
"what do I know about X"
"synthesize my notes on Y"
"am I missing anything about Z"
"meeting prep for X"
```
-> loads the `second-brain-synthesis` skill

### Extract Action Items
```text
"extract action items from these notes"
"turn this into tasks"
```
-> loads the `second-brain-action-items` skill

### Run a Full Cycle
```text
"run second brain"
"full cycle"
```
-> runs inbox curation + clipping processing + daily note curation in sequence

## Tagging Rules

Tags answer exactly **two questions**:
1. **Status?** - `status/active`, `status/seed`, `status/archived`, `status/evergreen`
2. **Category?** - `type/project`, `type/area`, `type/task`, `type/meeting`, `type/decision`,
   `type/learning`, `type/atomic`, `type/reference`, `type/research`, `type/notebook`,
   `type/notebook-notes`, `type/sticky-notes`, `type/overview`, `type/project-note`,
   `type/personal-review`, `type/status-report`, `type/ai-doc`, `type/code-review`

**Additional allowed:** `confidential`, `fitness`, `wedding`, `daily`, `tasks`, `testing`

**Do NOT create tags for:** project names, topics, tools - use the `Project`/`Area` relations
instead.

Vault statuses with no Notion select option (seed, note, seedling, evergreen, investigation,
resolved, processed) survive as `status/<value>` tags.

## Task Convention

A task is a **row in the Tasks data source**, not a checkbox in a note:
- `Status` = Todo / In progress / Blocked / Done
- `Priority` = P0-P3, `Due` = a date, `Context` = Computer / Home / Errands / Calls / Anywhere
- `Project` / `Area` relations, and `Source` back to the note it came from

The old `#type/task` prefix and the Obsidian Tasks plugin are gone. Inside a note body, use
markdown checkboxes (`- [ ]` / `- [x]`) for readability only - the row is the source of truth.

## Tasks Dashboard

The old `Tasks.md` with live `tasks` query blocks is replaced by **saved views** over the Tasks
data source, created with `POST /v1/views`:
- **Due Today** / **Due Tomorrow** / **Due This Week** - filter on `Due`
- **By Project** / **By Area** - group by the `Project` / `Area` relation
- **All Open Tasks** - filter `Status` != Done, sorted by `Due`

The default views already created with the workspace: Inbox (table, Untriaged, Captured desc),
Projects (board, grouped by Status), Now (tasks due in the next 7 days), All Tasks (grouped by
Area), Orphans (Notes with empty `Related`), Stale (Notes with `Stale After` < today).

## Git Workflow

There is **no vault git repo** any more - Notion holds the content, so there is nothing to commit
or push for second-brain content. The *skills* repo (this repo) is still versioned:

```bash
cd ~/Documents/01-Projects/Work-Of-Ekajaya/skills
git add -A
git commit -m "description: YYYY-MM-DD action"
git push

# ⚠️ Do NOT pull --rebase with unstaged changes - commit first
```

## Search

QMD is gone and there is no index to maintain. Search with the API:

```bash
nb POST /v1/search '{"query":"<query>","page_size":30}'
nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"or":[
  {"property":"Name","title":{"contains":"<query>"}},
  {"property":"Tags","multi_select":{"contains":"<query>"}}]}}'
```

Follow the `Related` relations from hub/Overview rows for conceptual navigation. Notion does not
search body text - query the candidate rows and read their markdown. No reindex step exists.

## Cron Job Summary

| Job | Schedule | Skill | What It Does |
|-----|----------|-------|-------------|
| `Inbox Curation` | Daily 09:00 | second-brain-inbox-curation | Classify inbox rows -> PARA |
| `clipping-processor-daily` | Daily 20:00 | second-brain-clipping-processor | Process web clippings |
| `weekly-review-sunday` | Sunday 04:00 | second-brain-weekly-review | Generate the weekly review |
| `Daily Note Curation` | Sunday 10:00 | second-brain-daily-note-curation | Extract + archive daily notes |
| `github-backup-am` | Daily 10:00 | - | Git backup of the skills repo |
| `github-backup-pm` | Daily 18:00 | - | Git backup of the skills repo |

## Anti-Patterns

- Don't run inbox curation and the clipping processor on the same Inbox row - clippings have
  `Kind` = Clipping, other inbox rows don't
- Don't archive daily notes before extracting - create the summaries and decisions first
- Don't `git pull --rebase` with unstaged changes - commit first
- Don't create topic tags - use the relations
- Don't delete decisions - only supersede
- Don't delete pages in general - archive and log them
- Don't write a `[[wikilink]]` or a `notion://` URI - use relations and `<mention-page>`
