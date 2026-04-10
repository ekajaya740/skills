# Structure Discovery

This guide provides a systematic process for discovering and mapping an existing Notion workspace structure using the Notion CLI (`ntn`).

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Search for Existing Databases](#step-1-search-for-existing-databases)
3. [Step 2: Fetch Database Schemas](#step-2-fetch-database-schemas)
4. [Step 3: Map Page Hierarchy](#step-3-map-page-hierarchy)
5. [Step 4: Identify Linking Targets](#step-4-identify-linking-targets)
6. [Step 5: Cache Structure to Project Memory](#step-5-cache-structure-to-project-memory)
7. [Complete Example Workflow](#complete-example-workflow)

---

## Overview

Before performing any Notion operations, you must understand the workspace structure. This discovery process:

- Identifies databases and their schemas
- Maps parent-child page relationships
- Finds existing entries that can serve as link targets
- Caches the structure for future sessions

Run each step in order. Do not skip steps.

---

## Step 1: Search for Existing Databases

Use `ntn api v1/search` to discover databases and pages in the workspace.

### Core Search Queries

Execute these searches to find primary structure elements:

```json
{
  "query": "second brain",
  "query_type": "internal",
  "page_size": 10
}
```

```json
{
  "query": "projects",
  "query_type": "internal",
  "page_size": 10
}
```

```json
{
  "query": "tasks",
  "query_type": "internal",
  "page_size": 10
}
```

```json
{
  "query": "notes",
  "query_type": "internal",
  "page_size": 10
}
```

```json
{
  "query": "knowledge",
  "query_type": "internal",
  "page_size": 10
}
```

### Additional Contextual Searches

For deeper discovery, search for domain-specific terms relevant to the workspace:

```json
{
  "query": "<domain-term>",
  "query_type": "internal",
  "page_size": 10
}
```

Replace `<domain-term>` with terms like: "clients", "contacts", "finance", "inventory", "content", "documentation", "meeting notes", "goals", "OKRs".

### Expected Output

The search returns results with `url` fields for each page or database. Extract the IDs:

- Database URLs: `https://notion.so/<workspace>/<database-id>`
- Page URLs: `https://notion.so/<workspace>/<page-id>`

Store all discovered IDs for Step 2.

---

## Step 2: Fetch Database Schemas

For each discovered database ID, use `ntn api v1/databases/<id> -X GET` to get the schema.

### Fetch a Database

```json
{
  "id": "<database-id>"
}
```

### What to Extract

From the response, record:

1. **Database title** - The `title` field
2. **Properties** - Each column with its type:
   - `title` - Primary name field
   - `select` - Single choice dropdown
   - `multi_select` - Multiple choice tags
   - `date` - Date or date-time
   - `number` - Numeric values
   - `checkbox` - Yes/No flags
   - `relation` - Links to other databases
   - `rollup` - Calculated values
   - `people` - User references
   - `files` - File attachments
   - `url` - Web links
   - `email` / `phone_number` - Contact fields
   - `rich_text` - Text content

3. **Description** - Database purpose if present
4. **Template IDs** - Any applied templates

### Schema Recording Format

```markdown
## Database: <Name>

**ID:** <database-id>
**Description:** <purpose>

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Name | title | Primary identifier |
| Status | select | Options: To Do, In Progress, Done |
| Tags | multi_select | |
| Due Date | date | |
| Related Project | relation | Links to Projects database |
```

---

## Step 3: Map Page Hierarchy

Identify top-level pages and their children using `ntn api v1/search`.

### Find Top-Level Pages

Top-level pages have no parent or are children of the workspace root. Search for pages that likely serve as root containers:

```json
{
  "query": "home",
  "query_type": "internal",
  "page_size": 5
}
```

```json
{
  "query": "dashboard",
  "query_type": "internal",
  "page_size": 5
}
```

```json
{
  "query": "index",
  "query_type": "internal",
  "page_size": 5
}
```

### Map Parent-Child Relationships

For each top-level page found, fetch it to identify its child pages:

```json
{
  "id": "<page-id>",
  "include_discussions": true
}
```

### Identifying Hierarchy Patterns

Look for these common patterns:

| Pattern | Description | Discovery Method |
|---------|-------------|------------------|
| Hub and Spoke | Central page with linked child pages | Fetch page, look for child page references |
| Nested Hierarchy | Pages within pages | Indentation in page structure |
| Database Pages | Database entries with parent pages | Relation properties pointing to parent |
| Tag-Based | Pages grouped by multi-select tags | Multi-select property with tag values |

### Hierarchy Recording Format

```markdown
## Page Hierarchy

### Level 0: Root Pages
- **Dashboard** (`page-id-1`) - Entry point with overview
- **Projects Hub** (`page-id-2`) - Project index

### Level 1: Children of Dashboard
- **Weekly Review** (`page-id-3`) - Recurring review page
- **Quick Notes** (`page-id-4`) - Capture location

### Level 2: Children of Projects Hub
- **Project Alpha** (`database-id-1`) - Database of alpha tasks
- **Project Beta** (`database-id-2`) - Database of beta tasks
```

---

## Step 4: Identify Linking Targets

Find specific entries that can serve as targets for relations or page links using `ntn api v1/search`.

### Find Linkable Entries

Search for specific item names that appear frequently:

```json
{
  "query": "<specific-item-name>",
  "query_type": "internal",
  "page_size": 5
}
```

### Identify Relation Targets

For databases with `relation` properties, list valid targets:

1. Fetch the related database schema (Step 2)
2. Search for sample entries in that database
3. Record the IDs and titles of valid link targets

### Linking Targets Format

```markdown
## Linkable Entries

### Projects
| ID | Name |
|----|------|
| `abc123` | Project Alpha |
| `def456` | Project Beta |

### Tags
| ID | Name | Color |
|----|------|-------|
| `tag1` | urgent | red |
| `tag2` | review | blue |

### Team Members
| ID | Name |
|----|------|
| `user1` | Alice |
| `user2` | Bob |
```

---

## Step 5: Cache Structure to Project Memory

Store all discovered structure in project memory for future sessions.

### Write to Project Memory

Use `project_memory_write` to cache the complete structure:

```json
{
  "memory": {
    "notionWorkspace": {
      "discoveredAt": "<ISO-8601-timestamp>",
      "databases": {
        "<database-id>": {
          "name": "<name>",
          "schema": { ... }
        }
      },
      "pages": {
        "<page-id>": {
          "name": "<name>",
          "parentId": "<parent-id>",
          "children": ["<child-id>"]
        }
      },
      "linkTargets": {
        "projects": [ ... ],
        "tags": [ ... ],
        "teamMembers": [ ... ]
      }
    }
  },
  "merge": false
}
```

### Directive for Future Sessions

Add a directive to ensure future sessions load this structure:

```markdown
## Directives

- **Priority**: high
- **Content**: "When working with notion-second-brain, first read project_memory section 'notionWorkspace' to load cached structure before making any changes"
```

### When to Refresh

Refresh the cached structure when:
- New databases are created
- Page hierarchy changes significantly
- New relation targets are added
- You encounter errors indicating stale IDs

---

## Complete Example Workflow

### Step 1: Initial Search

```
ntn api v1/search: {"query": "second brain", "query_type": "internal", "page_size": 10}
```

Returns:
- Dashboard page: `https://notion.so/workspace/dashboard-123`
- Projects database: `https://notion.so/workspace/projects-db-456`

### Step 2: Fetch Database Schema

```
ntn api v1/databases/projects-db-456 -X GET
```

Response includes:
```json
{
  "title": "Projects",
  "properties": {
    "Name": {"type": "title"},
    "Status": {"type": "select", "options": ["Active", "Completed", "On Hold"]},
    "Owner": {"type": "people"},
    "Due Date": {"type": "date"}
  }
}
```

### Step 3: Map Page Hierarchy

```
ntn api v1/pages/dashboard-123 -X GET
```

Response shows child pages and databases linked from the dashboard.

### Step 4: Identify Link Targets

```
ntn api v1/search: {"query": "Project Alpha", "query_type": "internal", "page_size": 5}
```

Returns the Project Alpha entry with ID `proj-alpha-789`.

### Step 5: Cache Structure

```
project_memory_write: {"memory": {"notionWorkspace": { ... }}, "merge": false}
```

### Result

The cached structure enables future sessions to:
- Know all available databases and their schemas
- Understand page hierarchy before making changes
- Use correct relation IDs when creating linked entries
- Avoid duplicate creation of existing structures
