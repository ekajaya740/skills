---
name: second-brain-weekly-review
description: "Generate a weekly review from the migrated Notion second brain. Use when the user wants a summary of the current or past week's activities, projects, decisions, and tasks. Triggers on: 'weekly review', 'review this week', 'weekly recap', 'what did I do this week', 'summarize this week', 'weekly summary', 'my week in review'. NOT for: single-entity summaries (use second-brain-summary skill), cross-note synthesis (use second-brain-synthesis skill), or extracting action items from pasted notes (use second-brain-action-items skill)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Weekly-Review, API]
    related_skills: [notion-second-brain, second-brain-summary, second-brain-synthesis, second-brain-action-items, second-brain-inbox-curation, second-brain-daily-note-curation]
---

# Second-Brain Weekly Review

Generate a structured weekly review from the second brain. Pull together daily notes, project
updates, decisions and tasks into a comprehensive week-in-review.

The second brain lives in **Notion**. The review is saved as a **Daily Notes** row named
`<MONDAY>-<SUNDAY>-weekly-review`.

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
DAILY_DS=$(ds "Daily Notes"); NOTES_DS=$(ds Notes); PROJECTS_DS=$(ds Projects)
AREAS_DS=$(ds Areas); DECISIONS_DS=$(ds Decisions); TASKS_DS=$(ds Tasks)
```

3 requests/second - space calls ~350 ms.

## When to Use This Skill

Use when the user says "weekly review", "review this week", "what did I do this week?", "weekly
recap", "summarize this week", or pastes additional notes alongside the request. Do NOT use for:
single-entity summaries (`second-brain-summary`); cross-note synthesis with gap analysis
(`second-brain-synthesis`); extracting action items from pasted notes
(`second-brain-action-items`).

## Workflow

### Phase 1: Determine the Week

1. Default: the current week (Monday -> Sunday)
2. If the user specifies a date or range, use that
3. Calculate the range (note: on a Sunday, `date -d "monday"` returns NEXT Monday):
   ```bash
   date -d "last monday" +%Y-%m-%d 2>/dev/null || date -d "monday - 7 days" +%Y-%m-%d
   date -d "next sunday" +%Y-%m-%d 2>/dev/null || date -d "sunday" +%Y-%m-%d
   ```
   or in Python: `today - timedelta(days=today.weekday())` .. `+ timedelta(days=6)`

### Phase 2: Gather Weekly Content

#### 2a-2e. Gather in five queries

```bash
# (a) daily notes - the narrative backbone
nb POST "/v1/data_sources/$DAILY_DS/query" '{"filter":{"property":"Date","date":{
  "on_or_after":"<monday>","on_or_before":"<sunday>"}},
  "sorts":[{"property":"Date","direction":"ascending"}],"page_size":50}'

# (b) project notes - swap "Project" for "Area" for area notes
nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"and":[
  {"property":"Date","date":{"on_or_after":"<monday>","on_or_before":"<sunday>"}},
  {"property":"Project","relation":{"is_not_empty":true}}]},
  "sorts":[{"property":"Date","direction":"descending"}],"page_size":50}'

# (c) decisions made
nb POST "/v1/data_sources/$DECISIONS_DS/query" '{"filter":{"property":"Date","date":{
  "on_or_after":"<monday>","on_or_before":"<sunday>"}},
  "sorts":[{"property":"Date","direction":"descending"}]}'

# (d) active tasks
nb POST "/v1/data_sources/$TASKS_DS/query" '{"filter":{"and":[
  {"property":"Status","select":{"does_not_equal":"Done"}},
  {"property":"Due","date":{"on_or_before":"<sunday>"}}]},
  "sorts":[{"property":"Due","direction":"ascending"}],"page_size":50}'

# (e) recently edited rows (supplementary)
nb POST /v1/search '{"sort":{"timestamp":"last_edited_time","direction":"descending"},"page_size":30}'
```

Read each row body with `nb GET /v1/pages/{id}/markdown`. Skip daily-note rows named
`<MONDAY>-<SUNDAY>-weekly-review` (a review, not a daily note) and read only the 3-5 most
relevant project/area notes. Notion does not search body text - a note with no Date property
needs a direct row query plus a body read.

**⚠️ Confidential Project Guard (Check BEFORE Including Confidential Content)** - confidential rows
carry the **Confidential** checkbox. Only whitelisted models - **Anthropic Claude** (all models)
and **Ollama Cloud** (all models) - may read or write confidential content; any other provider
(OpenAI, OpenRouter, xAI, etc.) is forbidden. Before reading a project/area note, check the owning
Projects/Areas row's `Confidential` property (read the property - never grep for the word). If it
is true AND the session is on a non-whitelisted model -> **skip that content** and exclude it from
the review. Note the exclusion in the report ("Confidential project X skipped - run on a
whitelisted model to include").

#### 2f. User-pasted notes

Include them as supplementary context. They are **not** saved to the second brain - they are
ephemeral input for this review only.

### Phase 3: Synthesize

Using ALL gathered content, produce the weekly review following the Output Format below.

**Synthesis rules:** prioritise daily notes as the narrative backbone; pull project/area updates
as structured data; extract decisions explicitly; identify patterns and themes; surface
open/blocked tasks; be honest about gaps (if only 3 days have notes, say so); don't fabricate - if
nothing was recorded for a section, say "No data".

## Output Format

**Every weekly review MUST include these 6 sections.**

**⚠️ TABLE RULES:** use `-` (hyphen) for empty cells, not an em dash (they break table
alignment); keep cell content to ~60 chars (Telegram rendering); no backticks inside cells; a blank
line before and after every table; the header separator row must use exactly `|---|`.

```markdown
# 📅 Weekly Review: <Week Range>

**Period:** <Monday YYYY-MM-DD> → <Sunday YYYY-MM-DD> · **Days with notes:** <N>/7
**Sources:** <N> daily notes, <N> project notes, <N> decisions, <N> area notes

## 1. Week Summary
<3-5 sentence paragraph summarizing the week.>

**Daily Breakdown:**
| Day | Focus | Status |
|-----|-------|--------|
| Monday | <main focus> | - |
| ... | ... | - |
| Sunday | <main focus> | - |
*Status: ✅ = activity, ⚠️ = partial, - = no data*

## 2. Active Projects
<For each project that had activity this week:>

### <Project Name>
- **Status:** <on-track / at-risk / blocked / completed> · **This week:** <what was done>
- **Blockers:** <any blockers, or "none"> · **Next steps:** <what's coming>

## 3. Key Decisions
| # | Date | Decision | Rationale |
|---|------|----------|-----------|
| 1 | YYYY-MM-DD | <decision> | <brief why> |
*No decisions recorded this week.* (if none)

## 4. Key Insights
<2-4 insights from the week.>
- **<Insight 1>:** <explanation> — <mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>
- **<Insight 2>:** <explanation>

## 5. Open Action Items
| # | Task | Source | Project/Area | Deadline |
|---|------|--------|--------------|----------|
| 1 | <task> | <note title> | <project/area> | <date> |
*Pulled from the Tasks data source and the daily notes.*

## 6. Next Week Focus
1. **<Focus 1>:** <brief description>
2. **<Focus 2>:** <brief description>
3. **<Focus 3>:** <brief description>

*Generated from second-brain content on <date>. Week had notes on <N> of 7 days.*
```

The old `#type/task` prefix is gone - open items are Task rows, listed here by name. Project names
and note references are page titles, linked with `<mention-page>` where a reader should be able to
open them.

### Phase 4: Save the Review

Search first (`nb POST /v1/search '{"query":"<monday> weekly review","filter":{"value":"page"}}'`),
then create the **Daily Notes** row named `<MONDAY>-<SUNDAY>-weekly-review`:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$DAILY_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"2026-10-19-2026-10-25-weekly-review"}}]},
    "Date": {"date":{"start":"2026-10-19"}},
    "Week": {"rich_text":[{"text":{"content":"2026-W43"}}]}
  },
  "markdown": "# 📅 Weekly Review: 2026-10-19 → 2026-10-25\n\n..."
}'
```

If the row already exists, update it instead:
`nb PATCH /v1/pages/<existing_page_id>/markdown '{"type":"replace_content","replace_content":{"new_str":"<full review markdown>"}}'`

**No git commit** - the vault is not a git repo any more; Notion holds the content.

## Edge Cases

- **No daily notes for the week:** say so upfront; base the review on project/area activity only.
- **Only 1-2 days of notes:** produce the review, be clear about the limited data, fill the daily
  breakdown with `-` for missing days.
- **No activity in a section:** state it explicitly ("No decisions recorded this week").
- **Week just started:** produce the review with the available data, note "Week [N]M/[N] days
  elapsed".
- **User specifies a past week:** same workflow with the given range.
- **User pastes notes with no second-brain content:** use the pasted notes as the primary source
  and say so.
- **Very busy week:** cap at the most significant items; don't list every task.

## Integration with Other Skills

- **notion-second-brain:** the contract - data sources, properties, markdown dialect, rate limit.
- **second-brain-summary:** single-entity summaries. This skill is for temporal/weekly synthesis.
- **second-brain-synthesis:** cross-note synthesis with gap analysis.
- **second-brain-action-items:** extracting tasks from pasted notes.
- **second-brain-inbox-curation:** inbox processing; this skill works on curated content.
- **second-brain-daily-note-curation:** curates the daily notes this review reads.
- **references:** `cron-job-config.md` (cron job id + prompt), `bulk-type-task-migration.md`
  (task status migration), `tasks-dashboard.md` (saved views).

## Anti-Patterns

- Don't fabricate daily activities - only report what's in the notes
- Don't skip any of the 6 required sections
- Don't make up decisions that aren't recorded
- Don't list every single task - focus on the most important open items
- Don't ignore gaps - be transparent about which days have no notes
- Don't write the Week Summary as bullet points - it must be a narrative paragraph
- Don't forget the Daily Breakdown table
- Don't use `date -d "monday"` on a Sunday without adjusting - it returns the next Monday
- **Don't change the output row without updating the cron job prompt.** The cron job
  `weekly-review-sunday` (id: `dbcdcd3626eb`) hardcodes the save target in its prompt. Update it
  via `cronjob(action='update', job_id='dbcdcd3626eb', prompt='...')` - see
  `references/cron-job-config.md`.
