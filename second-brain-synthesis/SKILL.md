---
name: second-brain-synthesis
description: "Synthesis and gap analysis layer over the migrated second brain in Notion. Use when the user asks a question that requires pulling together information from multiple notes, wants a cited summary, or wants to know what's missing from their knowledge. Triggers on: 'what do I know about X', 'synthesize my notes on', 'what have I written about', 'am I missing anything about', 'gap analysis', 'meeting prep', 'what is the state of', 'summarize my thinking on'. NOT for: reading a single known page (use second-brain-summary skill), inbox curation (use second-brain-inbox-curation skill), or internet research (use web search)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Synthesis, Gap-Analysis, API]
    related_skills: [notion-second-brain, second-brain-summary, second-brain-action-items, second-brain-weekly-review, second-brain-cross-linker]
---

# Second-Brain Synthesis

Answer questions by synthesizing across the entire second brain. Produce cited, well-structured
answers - not raw query results. End every answer with a gap analysis section.

The second brain lives in **Notion**: nine data sources, no local files, no QMD, no index, no
reindex step. Retrieval is a data-source query, a Notion search, and a page-body read.

**Contract: `notion-second-brain`.** Read it before any call - data-source ids, property names,
select options, markdown dialect, rate limit, token location.

Inspired by [GBrain](https://github.com/garrytan/gbrain)'s query pipeline: 3-layer search, synthesize,
cite, gap analysis.

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
NOTES_DS=$(ds Notes); PROJECTS_DS=$(ds Projects); DECISIONS_DS=$(ds Decisions)
```

3 requests/second - space calls ~350 ms.

## Prerequisites

No search index, no reindex step. Retrieval = property queries + `POST /v1/search`; page bodies
come from `GET /v1/pages/{id}/markdown`.

## When to Use This Skill

Use when the user wants a **synthesized answer** drawn from multiple notes, **meeting prep**, a
**gap analysis**, a **state summary** of a project, or a **theme synthesis** across notes. Do NOT
use for: reading a single known page or one entity (`second-brain-summary`), extracting action
items from raw notes (`second-brain-action-items`), inbox curation
(`second-brain-inbox-curation`), internet research (web search).

## Workflow

### Phase 1: Retrieve (3-Layer Search)

Cast a wide net. Use multiple retrieval strategies.

#### Layer 1: Property + title query

```bash
nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"or":[
  {"property":"Name","title":{"contains":"<query>"}},
  {"property":"Tags","multi_select":{"contains":"<query>"}}]},
  "sorts":[{"property":"Date","direction":"descending"}],"page_size":20}'
```

Returns rows + their properties. Note the top 5-10. Notion does not index body text - a term that
only appears in a body will not match here.

#### Layer 2: Global search + data-source routing

```bash
nb POST /v1/search '{"query":"<query>","page_size":30}'
```

This spans every data source at once (Notes, Projects, Areas, Decisions, Daily Notes). Then check
the data source the query type needs (see Query Routing below) - a project-status question also
needs the Projects row and its open Task rows.

#### Layer 3: Full content of the top results

```bash
nb GET /v1/pages/<page_id>/markdown      # -> {"markdown": "...", "truncated": false}
```

Read the 3-5 most relevant pages. `truncated: true` means a very large page - read what you got
and say so.

**Token budget:** read snippets (properties, first lines) first, then only load full bodies for
the top 3-5 most relevant results. Don't try to read everything.

**⚠️ Confidential Guard (Check BEFORE Reading Confidential Content)** - confidential rows carry the
**Confidential** checkbox. Only whitelisted models - **Anthropic Claude** (all models) and
**Ollama Cloud** (all models) - may read or write confidential content; any other provider
(OpenAI, OpenRouter, xAI, etc.) is forbidden. Before reading the body of a row belonging to a
project/area: check the `Confidential` property on the row and on the owning Project/Area row
(read the property - never grep for the word "confidential", it produced false positives before).
If it is true AND the session is on a non-whitelisted model -> **skip reading that body** and
exclude it from synthesis. Note the exclusion in the output ("Confidential project X excluded - run
on a whitelisted model to include") so the human can re-run if capture is desired.

### Phase 2: Synthesize

Using the retrieved content, compose a structured answer following these rules.

#### Answer Format

```
## <Topic> — Synthesis

<2-3 paragraph synthesized answer. Write naturally, connect ideas across notes.
Don't just list facts — explain relationships and context.>

### Key Points
- **<Point>**: <explanation> — <mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>

### Sources
- <mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page> — <what it covers>
```

The `[[wikilink]]` is gone: a citation is an inline **mention** of the page
(`<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>`). There is no
`notion://` scheme. Every cited page must appear in the Sources list with its id, so the reader
can open it in Notion.

#### Citation Rules (from GBrain's quality convention)

- Every factual claim must have a page source - cite it inline as a mention
- If a claim draws from multiple pages, cite all of them
- If you're inferring something not explicitly stated, say so
- **Source precedence:** user's statements > Overview/synthesis notes > daily notes > external
- **Quality:** connect dots across pages rather than listing facts; resolve contradictions by
  surfacing both sides with sources; prioritise recency; be specific (numbers, dates, details)

### Phase 3: Gap Analysis

End every synthesis with a gap analysis. This is the most valuable part.

#### What to Look For

1. **Missing expected content**: "You have detailed notes on X but nothing about Y."
2. **Stale information**: "The last note about X is from 3 weeks ago - may be outdated." (Check the
   `Date` and `Stale After` properties.)
3. **Contradictions**: "Note A says X, Note B says Y."
4. **Unresolved open questions**: "Your overview mentions 'need to research X' but no follow-up."
5. **Missing connections**: notes on X and Y with nothing linking them (query Notes for rows with
   an empty `Related` relation).

#### Gap Analysis Format

```
### 🔍 Gap Analysis

**What's missing:**
- <specific gap 1>
- <specific gap 2>

**Potentially stale:**
- <note> is from <date> — <why it might be outdated>

**Open questions from your notes:**
- "<exact quote>" — <mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>

**Suggested next capture:**
- <suggestion for what to write next>
```

## Query Routing

Different query types need different retrieval emphasis:

### "What do I know about X?" (General Knowledge)
- Broad retrieval across all data sources
- Emphasis on standalone Notes and Area rows
- Include any Daily Notes that mention X

### "What's the status of project X?" (Project Status)
- Read the Projects row body (the durable facts) and its `Status`, `Health`, `Target` properties
- Check the open Task rows where `Project` relation contains the project page id
- Note the `Date` of the last linked note

### "Meeting prep for X" (Meeting Preparation)
- Find every page mentioning X (person, company, topic) across Notes, Daily Notes, Decisions
- Read the most recent pages first
- Extract: last contact date, open commitments, unresolved items
- Gap analysis: "No notes since <date> - X may have replied through channels the brain doesn't see"

### "Am I missing anything about X?" (Gap-Focused)
- Retrieve everything about X
- The gap analysis section should be the primary output
- Be thorough - check every data source, not only Notes

### "Summarize my thinking on X" (Theme Synthesis)
- Broad retrieval, then cluster findings by sub-topic
- Show evolution of thinking if the pages span time (sort by `Date`)
- Highlight where your thinking has changed

## Edge Cases

- **No results found**: Say so honestly. Suggest broadening the query (shorter keyword, or drop the
  `Tags` clause). Don't fabricate.
- **Only 1-2 relevant pages**: synthesize from what's there, but be explicit about the limited base.
- **Query too broad** ("summarize everything"): ask the user to narrow the scope.
- **Conflicting information**: present both sides with sources.
- **Very long pages**: `GET /v1/pages/{id}/markdown` may return `truncated: true` - read what came
  back and say it was truncated.
- **Search returns nothing but the body surely contains it**: Notion does not search body text -
  query the candidate rows and read their markdown instead.

## Performance Notes

- Property queries and `POST /v1/search` are the primary retrieval methods; for conceptual gaps
  traverse `Related` relations from hub/Overview rows
- The LLM synthesis is the main token cost - keep retrieved content focused (top 5-10 results)
- Space API calls ~350 ms apart (3 requests/second limit)

## Integration with Other Skills

- **notion-second-brain:** the contract - data sources, properties, markdown dialect, rate limit.
- **second-brain-summary:** quick single-entity summaries. This skill adds cross-page synthesis and
  gap analysis.
- **second-brain-action-items:** extracting structured tasks from raw notes, not cross-page
  synthesis.
- **second-brain-weekly-review:** weekly recaps, not deep cross-note synthesis.
- **second-brain-clipping-processor:** processing web clippings, not synthesis.
- **second-brain-inbox-curation:** inbox processing; this skill queries already-curated content.
- **second-brain-cross-linker:** finds orphaned or weakly connected pages - the gap analysis
  often surfaces exactly those.

## Anti-Patterns

- Answering from general knowledge when the second brain has relevant content
- Hallucinating facts not present in the pages you read
- Silently picking one source when sources conflict
- Loading full pages when snippets suffice; skipping the gap analysis section
- Citing sources that don't actually contain the claimed information
- Writing a `[[wikilink]]` - cite pages as `<mention-page ...>` mentions
