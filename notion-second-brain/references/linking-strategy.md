# Linking Strategy

This guide covers the reuse-first linking strategy for connecting Notion entries, ensuring the workspace remains denormalized and avoids duplicate content.

## Table of Contents

1. [Overview](#overview)
2. [Reuse-First Principle](#reuse-first-principle)
3. [Search-Before-Create Pattern](#search-before-create-pattern)
4. [When to Suggest Reuse](#when-to-suggest-reuse)
5. [Notion Relation Properties](#notion-relation-properties)
6. [Linking Patterns](#linking-patterns)
7. [Decision Flowchart](#decision-flowchart)
8. [Examples](#examples)

---

## Overview

Linking in Notion is not just about connection, it is about building a coherent knowledge graph where each piece of information exists once and is referenced by many related entries. Before creating a new page or database entry, always search for existing entries that could serve the same purpose.

---

## Reuse-First Principle

The core principle: **Always prefer linking to existing entries over creating new ones.**

### Why Reuse?

- **Reduces duplication** - One source of truth for each concept
- **Maintains consistency** - Updates propagate automatically through relations
- **Improves searchability** - Fewer entries mean cleaner search results
- **Preserves context** - Existing entries already have their own connections and history

### When to Create Instead of Reuse

Create a new entry only when:

- No existing entry covers the concept or entity
- The new entry represents a genuinely new topic or project
- The user explicitly requests a new entry

---

## Search-Before-Create Pattern

Before creating any new entry, execute a search to find existing alternatives.

### Search Process

1. **User requests new entry** - User mentions adding something (project, note, contact, etc.)
2. **Extract key terms** - Identify the likely name, tags, or topic
3. **Search workspace** - Use `notion_notion-search` with relevant query
4. **Evaluate results** - Check if any existing entry covers the same ground
5. **Decide** - Proceed with reuse or creation based on findings

### Search Query Examples

```json
{
  "query": "<item-name>",
  "query_type": "internal",
  "page_size": 10
}
```

```json
{
  "query": "<topic-keyword>",
  "query_type": "internal",
  "page_size": 10
}
```

```json
{
  "query": "<tag-name>",
  "query_type": "internal",
  "page_size": 10
}
```

### What to Search For

| Entry Type | Search Terms |
|------------|--------------|
| Project | Project name, client name, project codename |
| Person | Full name, email, company |
| Topic | Subject area, category name |
| Document | Document title, doc type (meeting notes, spec, etc.) |
| Tag | Tag name, category label |

---

## When to Suggest Reuse

### Strong Reuse Signals

Suggest reuse when:

1. **Similar title** - Existing entry has same or very similar name
2. **Related content** - Existing entry discusses the same topic or project
3. **Same tags** - Existing entry shares relevant multi-select tags
4. **Same area** - Existing entry lives in the same parent page or database
5. **Semantic match** - Search returns high-relevance result for the query

### Reuse Suggestion Format

When you find a potential reuse candidate:

```
Found existing entry that may cover this:

**[Entry Name](page-url)**
- Type: <database/page>
- Status: <relevant property>
- Tags: <tags if applicable>

Should I link to this entry instead of creating a new one?
```

### Accepting Reuse

If user confirms reuse:

1. Retrieve the existing entry ID
2. Create new entry that links to the existing one via relation or inline link
3. Set appropriate properties pointing to the reused entry
4. Add the new entry as a related item, not a duplicate

### Rejecting Reuse

If user rejects reuse (wants a new separate entry):

1. Proceed with creating the new entry
2. Still consider linking the new entry to the similar existing entry if they are related
3. Document the distinction between the two entries

---

## Notion Relation Properties

Notion `relation` properties create explicit database-level links between entries.

### How Relations Work

- A relation property in Database A points to entries in Database B
- The linked entries show a reverse relation back to Database A (if dual relations are set)
- Relations are queryable and can be used for filtering and rollups

### Creating Relations

When creating a database with relations:

```
CREATE TABLE "Tasks" (
  "Name" TITLE,
  "Status" SELECT('To Do', 'In Progress', 'Done'),
  "Related Project" RELATION('<projects-database-id>'),
  "Tags" MULTI_SELECT('urgent', 'review', 'planning')
)
```

### Adding Relations via Page Creation

When creating a page that should link to an existing entry:

1. Set the relation property to the existing entry ID
2. The relation property type must match the target database

Example page creation with relation:

```json
{
  "pages": [
    {
      "properties": {
        "Name": "New Task",
        "Related Project": "<existing-project-id>"
      }
    }
  ],
  "parent": {
    "database_id": "<tasks-database-id>"
  }
}
```

### Relation vs Inline Link

| Aspect | Relation | Inline Page Link |
|--------|----------|------------------|
| Schema | Defined at database level | Embedded in page content |
| Queryable | Yes - can filter by relation | No - just visual connection |
| Bidirectional | Optional (dual relation) | No reverse link |
| Use for | Structured data, filtering | Contextual references, notes |

---

## Linking Patterns

### Bidirectional Links

Bidirectional links create mutual references that help navigate both directions.

**Setup with Dual Relations:**

```
CREATE TABLE "Projects" (
  "Name" TITLE,
  "Tasks" RELATION('<tasks-database-id>', DUAL 'Related Project')
)

CREATE TABLE "Tasks" (
  "Name" TITLE,
  "Related Project" RELATION('<projects-database-id>', DUAL 'Tasks')
)
```

**Effect:**
- Each task shows its linked project
- Each project shows all its tasks automatically

### Hub Pages

A hub page aggregates related entries without duplicating content.

**Structure:**

```
Hub Page: "Engineering Team"
  - Links to individual engineer pages
  - Contains team-level context and overview
  - Relations to projects the team owns
```

**Hub Page Properties:**

- Title: Team/area name
- Relation: Team members (people)
- Relation: Projects (if hub owns projects)
- Content: Overview, responsibilities, links to resources

### Inline Page Links

Inline links embed references within page content for contextual linking.

**Usage in Page Content:**

```
For the Q4 planning initiative, see [[Project Alpha]] and [[Q4 Strategy Doc]].

Related team members: [[Alice Smith]], [[Bob Johnson]]
```

**When to Use Inline Links:**

- References within explanatory text
- Connecting ideas across different contexts
- Creating a narrative that references related entries
- Quick links to supporting documents

### Tag-Based Linking

Use multi-select properties to create implicit networks.

**Tag Structure:**

```
Entry has: Tags = ['frontend', 'react', 'urgent']
```

**Finding Related Entries:**

1. Filter by shared tags
2. Browse entries with matching multi-select values
3. Use tags to discover indirect connections

---

## Decision Flowchart

```
User requests new entry
         |
         v
Search for existing entry
         |
         v
   Similar found? ---No---> Create new entry
         |                         |
        Yes                        v
         |                   Add relations to
         v                   related existing entries
Suggest reuse                       |
         |                          v
         v                    Done
User confirms?
    |       |
   Yes      No
    |        |
    v        v
Link to   Create new entry
existing  (still consider
entry     linking if related)
    |
    v
Done
```

---

## Examples

### Example 1: Adding a Task to Existing Project

**User Request:** "Add a task for the website redesign"

**Search:** `notion_notion-search` for "website redesign project"

**Result:** Found Project "Website Redesign" (ID: `proj-123`)

**Action:** Create task with `Related Project` relation set to `proj-123`

```json
{
  "pages": [
    {
      "properties": {
        "Name": "Redesign homepage mockup",
        "Status": "To Do",
        "Related Project": "proj-123"
      }
    }
  ],
  "parent": {
    "database_id": "tasks-db"
  }
}
```

### Example 2: Suggesting Reuse for Similar Topic

**User Request:** "Add notes on machine learning"

**Search:** `notion_notion-search` for "machine learning"

**Result:** Found page "ML Fundamentals" (ID: `ml-456`)

**Suggestion:**

```
Found existing entry that may cover this:

**ML Fundamentals**
- Type: Page
- Tags: ai, machine-learning, fundamentals

Should I link to this page instead of creating a new one?
```

### Example 3: Linking with Inline References

**Scenario:** Creating meeting notes that reference existing projects and people

**Page Content:**

```
# Meeting Notes: Q4 Planning

Attendees: [[Alice Smith]], [[Bob Johnson]]

Discussed [[Project Alpha]] timeline and resource allocation.

Related: [[Q4 OKRs]] and [[Team Roadmap]]
```

### Example 4: Creating a Hub Page with Dual Relations

**Setup:** Team Hub with dual relations to member pages and project pages

**Team Hub Page:**

```
Title: Platform Team
Relations:
  - Members: Alice, Bob, Carol (people relation)
  - Projects: Platform v2, API Gateway (dual relation to Projects)
Content: Team overview, responsibilities, key metrics
```

**Effect:** The Platform Team page shows all members and all projects. Each member page shows their team. Each project shows its owning team.

### Example 5: Tag-Based Discovery and Linking

**Scenario:** User wants to link all frontend-related entries

**Search:** `notion_notion-search` for "frontend"

**Results:** Multiple entries tagged with `frontend`

**Action:** Link these entries to a central "Frontend" hub page, or ensure they share consistent tagging for easy filtering and discovery.

---

## Related Files

- [Structure Discovery](structure-discovery.md) - How to map existing workspace structure
- [Database Patterns](database-patterns.md) - Database schema design and creation
- [Action Templates](action-templates.md) - Ready-to-use action sequences
