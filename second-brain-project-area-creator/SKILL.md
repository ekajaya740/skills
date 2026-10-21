---
name: second-brain-project-area-creator
description: "Create new projects and areas in the migrated Notion second brain with the right structure, properties, template bodies and Google Tasks integration. Use when the user says 'create a new project', 'new area', 'start a project called X', 'add a new area for Y'. NOT for: creating notes within an existing project/area (use second-brain-inbox-curation or second-brain-clipping-processor), or curating inbox content (use second-brain-inbox-curation)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Projects, Areas, API]
    related_skills: [notion-second-brain, second-brain-inbox-curation, second-brain-action-items, second-brain-decision-manager]
---

# Second-Brain Project & Area Creator

Create new projects and areas with the correct structure, properties, template bodies and Google
Tasks integration.

The second brain lives in **Notion**. A project is a row in the **Projects** data source, an area
is a row in the **Areas** data source. The old sub-folder scheme becomes related Notes rows; the
old `overview.md` becomes the row's body.

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
PROJECTS_DS=$(ds Projects); AREAS_DS=$(ds Areas); NOTES_DS=$(ds Notes); TASKS_DS=$(ds Tasks)
```

3 requests/second - space calls ~350 ms.

## Prerequisites

1. **Check for duplicates** - list the existing projects and areas first:
   ```bash
   nb POST "/v1/data_sources/$PROJECTS_DS/query" '{"page_size":100}'
   nb POST "/v1/data_sources/$AREAS_DS/query" '{"page_size":100}'
   ```
2. **Never invent a new name when one already exists** - if a matching project/area exists, use it
3. **Read the template** before creating: the *Project* / *Area* pages under **Templates** in
   Notion (or the body structure in Step 2 below)

## Creating a New Project

### Step 1: Plan the sub-topics

There are no folders any more. A sub-folder becomes a **related Notes row** and a line in the
project body's `## Sub-topics` section.

Common project sub-topics: Tests, Research, Docs, Design, Finance, Resources, Planning, Decisions,
Issues. General notes that fit no category are plain Notes rows related to the project.

**Rule:** if a sub-topic will hold 5+ rows sharing a theme, give it its own Notes row with a
recognisable title prefix and list it under `## Sub-topics`.

### Step 2: Create the Projects row

The row body holds the **durable facts** - strategy, architecture decisions, key contacts,
status. Properties:

```json
{
  "Name": {"title":[{"text":{"content":"<Project Name>"}}]},
  "Status": {"select":{"name":"Active"}},
  "Area": {"relation":[{"id":"<area_page_id>"}]},
  "Priority": {"select":{"name":"P2"}},
  "Health": {"select":{"name":"On track"}},
  "Start": {"date":{"start":"2026-10-21"}},
  "Target": {"date":{"start":"2026-12-31"}},
  "Tags": {"multi_select":[{"name":"type/project"},{"name":"status/active"}]}
}
```

- `Status` = `Active` (options: Idea, Active, Paused, Blocked, Done, Archived)
- `Priority` = P0-P3, `Health` = On track / At risk / Off track
- `Created` and `Updated` are automatic on the Projects data source
- `Tags` = `type/project` + `status/active`; the vault's `type/project` tag has no Notion
  select option, so it stays a tag
- `Area` relation = the owning area, when there is one

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$PROJECTS_DS"'"},
  "properties": { ...as above... },
  "markdown": "# <Project Name>\n\n## Purpose\n<What outcome does this project deliver?>\n\n## Strategy\n...\n\n## Key facts\n...\n\n## Sub-topics\n- Tests\n- Research\n\n## Related\n- <mention-page url=\"https://www.notion.so/<area_id>\">Area name</mention-page>"
}'
```

### Step 3: Create the task rows

The old `tasks.md` becomes **Task rows** related to the project:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$TASKS_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"First deliverable"}}]},
    "Status": {"select":{"name":"Todo"}},
    "Priority": {"select":{"name":"P2"}},
    "Project": {"relation":[{"id":"'"$PROJECT_PAGE_ID"'"}]},
    "Tags": {"multi_select":[{"name":"type/task"}]}
  }
}'
```

The old `## Active / ## Ideas / ## Done` sections are now the `Status` property
(Todo / In progress / Blocked / Done). `Ideas` items stay out of the task list - create them only
when the user asks.

### Step 4: Add to Google Tasks

Create a matching Google Tasks list named `[P] <Project Name>` (unless on the exclusion list).

**Exclusion list** (second brain only, no Google Tasks): `dotfiles` (Project)

```bash
gws-core tasks tasklists insert --json '{"title": "[P] Project Name"}'
```

### Step 5: Update Cross-Links

- Relate the new project to the owning area (`Area` relation, one side only)
- Mention related notes and areas in the project body:
  `<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>`
- If the project belongs to an existing area, add a mention of the project in the **area** row's
  body - do not hand-write a backlink, relations mirror automatically

## Creating a New Area

### Step 1: Plan the sub-topics

Area sub-topics: Tests, Materials, Milestones, Vocabulary, Grammar, Routines, Logs, Progress,
References, Research, Strategies, Docs. Each becomes a **Notes row** related to the area, listed
under `## Sub-topics` in the area body. Same rule: 5+ rows sharing a theme -> its own row.

### Step 2: Create the Areas row

```json
{
  "Name": {"title":[{"text":{"content":"<Area Name>"}}]},
  "Status": {"select":{"name":"Active"}},
  "Focus": {"select":{"name":"<focus>"}},
  "Tags": {"multi_select":[{"name":"type/area"},{"name":"status/active"}]}
}
```

- `Status` = Active (options: Active, Ongoing, Dormant, Archived)
- `Focus` is a select on the Areas data source - check the existing options before writing
- Body = the durable facts about the area, same shape as a project body

### Step 3: Task rows - OPTIONAL

**Do NOT auto-create task rows for areas.** Only create them if the user explicitly asks for task
tracking in this area. When you do, set the `Area` relation on each task row.

### Step 4: Google Tasks - Conditional

Only create a Google Tasks list if task rows were created AND the area is not on the exclusion
list.

**Exclusion list** (second brain only, no Google Tasks): `PT-SUM-Digital-Konsultan` (Area),
`Joki` (Area), `ADHD` (Area)

```bash
gws-core tasks tasklists insert --json '{"title": "[A] Area Name"}'
```

### Step 5: Update Cross-Links

- Relate the new area to the owning project(s) where it applies
- Mention related projects and notes in the area body
- If the area relates to an existing project, add a mention of the area in the **project** row's
  body

## Google Tasks Naming Convention

| Type | Prefix | Example |
|------|--------|---------|
| Project | `[P]` | `[P] Mitsukoshi Isetan` |
| Area | `[A]` | `[A] Fitness` |
| Default | - | `Inbox` (catch-all) |

## Templates Reference

The 13 template pages under the **Templates** parent page in Notion: Project, Area, Project Note,
Meeting, Learning Note, Decision, Reference, Atomic Note, Daily Note and the rest of the vault
set. Read the relevant one before creating a row - e.g. the *Project* template for a project body
and the *Decision* template for a decision (see `second-brain-decision-manager`).

## Anti-Patterns

- Don't create a new project/area when one with the same name already exists
- Don't auto-create task rows for areas unless asked
- Don't dump every note into one row - create purpose-specific sub-topic rows when 5+ rows share
  a theme
- Don't skip cross-linking - every new project/area should connect to existing content
- Don't create Google Tasks lists for excluded items
- Don't write a `[[wikilink]]` - use relations and `<mention-page>`
- Don't delete an existing row to "replace" it - update it
