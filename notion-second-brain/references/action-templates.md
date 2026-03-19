# Action Templates

Practical step-by-step templates for common Notion second brain operations. Each template provides trigger conditions, exact steps, and working examples.

## Table of Contents

1. [Add New Entry](#template-1-add-new-entry)
2. [Link Entries](#template-2-link-entries)
3. [Find Related Entries](#template-3-find-related-entries)
4. [Update Entry Status](#template-4-update-entry-status)
5. [Create New Database](#template-5-create-new-database)

---

## Template 1: Add New Entry

**Trigger:** User says "add a new [project/task/note] about X" or "create entry for X"

**Purpose:** Create a new page in an existing database with proper properties and links

### Steps

1. **Identify the target database**
   - Search for the database to confirm it exists
   - If database does not exist, use [Template 5](#template-5-create-new-database) first

2. **Search for duplicates**
   - Use `notion_notion-search` to check if entry already exists
   - Query with the proposed entry name or key terms

3. **Fetch the database schema**
   - Use `notion_notion-fetch` with the database ID
   - Identify required properties and their types

4. **Prepare properties**
   - Map user-provided values to schema properties
   - Set default values for optional properties if not provided

5. **Create the page**
   - Use `notion_notion-create-pages` with parent set to database ID
   - Include all required properties

6. **Link to related entries**
   - After creation, use [Template 2](#template-2-link-entries) to connect to related pages
   - Link to parent pages, related projects, tags, and team members

7. **Confirm and report**
   - Return the created page URL and summary of properties set

### Example

**User prompt:**
> Add a new task about finishing the Q4 report, set status to In Progress, due Friday, and link it to the Marketing project.

**Tool calls:**

```json
{
  "tool": "notion_notion-search",
  "args": {
    "query": "Q4 report task",
    "query_type": "internal",
    "page_size": 5
  }
}
```

```json
{
  "tool": "notion_notion-fetch",
  "args": {
    "id": "database-id-for-tasks"
  }
}
```

```json
{
  "tool": "notion_notion-create-pages",
  "args": {
    "parent": {
      "database_id": "database-id-for-tasks"
    },
    "pages": [
      {
        "properties": {
          "Name": "Finish Q4 Report",
          "Status": "In Progress",
          "date:Due Date:start": "2024-12-20",
          "date:Due Date:is_datetime": 0
        }
      }
    ]
  }
}
```

**Response:** Page created at `https://notion.so/workspace/task-q4-report-abc123`

**Next step:** Use Template 2 to link to the Marketing project.

---

## Template 2: Link Entries

**Trigger:** User says "link [entry A] to [entry B]" or "connect X with Y" or "add relation between X and Y"

**Purpose:** Create bidirectional links between existing entries using relations or inline page links

### Steps

1. **Locate entry A**
   - Use `notion_notion-search` to find the first entry
   - Record its ID and determine if it belongs to a database

2. **Locate entry B**
   - Use `notion_notion-search` to find the second entry
   - Record its ID and type (database entry or standalone page)

3. **Determine link method**

   | Entry A Type | Entry B Type | Recommended Method |
   |--------------|--------------|--------------------|
   | Database page | Database page | Relation property (see [linking-strategy.md](linking-strategy.md)) |
   | Any | Standalone page | Inline page link in content |
   | Database page | Standalone page | Relation property or inline link |

4. **For relation property method**
   - Fetch entry A schema to check for existing relation properties
   - If valid relation exists, use `notion_notion-update-page` to set the relation
   - If no relation exists, add inline page link to entry A content instead

5. **For inline link method**
   - Fetch entry A to get current content
   - Add page reference using Notion markdown: `<page url="notion-page-id">`
   - Use `notion_notion-update-page` with `replace_content` command

6. **Verify link created**
   - Fetch both entries to confirm link appears correctly

### Example

**User prompt:**
> Link the "Q4 Report" task to the "Marketing" project page.

**Tool calls:**

```json
{
  "tool": "notion_notion-search",
  "args": {
    "query": "Q4 Report",
    "query_type": "internal",
    "page_size": 5
  }
}
```

```json
{
  "tool": "notion_notion-search",
  "args": {
    "query": "Marketing project",
    "query_type": "internal",
    "page_size": 5
  }
}
```

```json
{
  "tool": "notion_notion-fetch",
  "args": {
    "id": "task-q4-report-id"
  }
}
```

Check if a relation property exists for Projects. If yes:

```json
{
  "tool": "notion_notion-update-page",
  "args": {
    "page_id": "task-q4-report-id",
    "command": "update_properties",
    "properties": {
      "relation:Projects": "marketing-project-id"
    }
  }
}
```

If no relation property exists, add inline link:

```json
{
  "tool": "notion_notion-update-page",
  "args": {
    "page_id": "task-q4-report-id",
    "command": "update_content",
    "content_updates": [
      {
        "old_str": "# Q4 Report\n",
        "new_str": "# Q4 Report\n\nRelated to [[Marketing]] project.\n"
      }
    ]
  }
}
```

**Response:** Entries now linked. Verify by fetching both entries.

---

## Template 3: Find Related Entries

**Trigger:** User says "find all entries related to X", "show me X and its connections", or "what entries link to X"

**Purpose:** Search and retrieve entries with semantic matching, filter by properties, return organized results

### Steps

1. **Perform semantic search**
   - Use `notion_notion-search` with `query_type: "internal"`
   - Query with the topic, project name, or concept
   - Set `page_size` appropriately (default 10, max 25)

2. **For targeted search by property**
   - First discover database schema using [structure-discovery.md](structure-discovery.md)
   - Search for entries matching specific property values

3. **Organize results**
   - Group by database or parent page
   - Note the type of each entry (page, database entry)
   - List relevant properties for each result

4. **Check for related entries**
   - For each strong match, fetch to identify linked entries
   - Use relation properties and inline links to map connections

5. **Return organized results**
   - Present as a list with entry name, type, URL, and key properties
   - Include a summary of how entries relate to the search topic

### Example

**User prompt:**
> Find all entries related to the Q4 marketing campaign.

**Tool calls:**

```json
{
  "tool": "notion_notion-search",
  "args": {
    "query": "Q4 marketing campaign",
    "query_type": "internal",
    "page_size": 10
  }
}
```

**Response example:**

```
Found 4 related entries:

1. **Q4 Marketing Campaign** (Database)
   URL: https://notion.so/workspace/q4-campaign-db-123
   Type: Database with 3 properties

2. **Campaign Strategy** (Page)
   URL: https://notion.so/workspace/campaign-strategy-456
   Type: Child page under Q4 Marketing
   Links to: Campaign Tasks database

3. **Launch Checklist** (Database entry)
   URL: https://notion.so/workspace/launch-checklist-789
   Type: Entry in Campaign Tasks database
   Status: In Progress
   Related Project: Q4 Marketing Campaign

4. **Budget Tracker** (Page)
   URL: https://notion.so/workspace/budget-tracker-abc
   Type: Standalone page
   References: Q4 Marketing via inline link
```

---

## Template 4: Update Entry Status

**Trigger:** User says "update the status of X to Y", "change X's property to Y", or "mark X as done"

**Purpose:** Modify an existing entry's properties to reflect new state

### Steps

1. **Find the entry**
   - Use `notion_notion-search` to locate entry by name
   - Verify you have the correct entry before proceeding

2. **Fetch current state**
   - Use `notion_notion-fetch` to get current properties
   - Confirm the property you need to update exists

3. **Determine property type and valid values**
   - Select properties: use exact option names
   - Checkbox: use `__YES__` or `__NO__`
   - Date: use ISO format `YYYY-MM-DD`
   - Text: use plain string value

4. **Update the property**
   - Use `notion_notion-update-page` with `update_properties` command
   - Include only the properties being changed

5. **Verify update**
   - Fetch the entry again to confirm changes applied

### Example

**User prompt:**
> Mark the Q4 Report task as done.

**Tool calls:**

```json
{
  "tool": "notion_notion-search",
  "args": {
    "query": "Q4 Report",
    "query_type": "internal",
    "page_size": 5
  }
}
```

```json
{
  "tool": "notion_notion-fetch",
  "args": {
    "id": "task-q4-report-id"
  }
}
```

**Current state:** Status is "In Progress", needs to change to "Done"

```json
{
  "tool": "notion_notion-update-page",
  "args": {
    "page_id": "task-q4-report-id",
    "command": "update_properties",
    "properties": {
      "Status": "Done"
    }
  }
}
```

**Response:** Status updated to "Done". Verify by fetching the entry.

---

## Template 5: Create New Database

**Trigger:** User says "create a new database for X" or "set up a new [project/task/contact] tracker"

**Purpose:** Create a new database with appropriate schema, properties, and initial views

### Steps

1. **Design the schema**
   - Identify the entity type (tasks, projects, contacts, etc.)
   - List required properties (name, status, dates, etc.)
   - Determine relation needs (link to existing databases)
   - See [database-patterns.md](database-patterns.md) for schema patterns

2. **Create the database**
   - Use `notion_notion-create-database` with SQL DDL syntax
   - Include title property and essential properties
   - Set appropriate property types (select, date, relation, etc.)

3. **Create initial views**
   - Use `notion_notion-create-view` for each needed view type
   - Common views: table (default), board (for status), calendar (for dates), gallery (for visual)
   - Configure filters and sorts for each view

4. **Create template entry (optional)**
   - Add one sample entry to demonstrate structure
   - Include placeholder values in all required fields

5. **Link to parent structure**
   - Identify where this database fits in the page hierarchy
   - Create a parent page if needed, or link from existing hub page
   - Use [structure-discovery.md](structure-discovery.md) to find appropriate parent

6. **Document in project memory**
   - Add new database to cached structure
   - Update link targets for future relations

### Example

**User prompt:**
> Create a new database for tracking client feedback with status, priority, and client name.

**Tool calls:**

```json
{
  "tool": "notion_notion-create-database",
  "args": {
    "parent": {
      "page_id": "parent-page-id"
    },
    "title": "Client Feedback",
    "schema": "CREATE TABLE (\"Name\" TITLE, \"Status\" SELECT('Open':default, 'In Review':yellow, 'Resolved':green), \"Priority\" SELECT('Low':gray, 'Medium':yellow, 'High':red), \"Client Name\" RICH_TEXT, \"Due Date\" DATE)"
  }
}
```

**Response:** Database created with ID `feedback-db-xyz`

**Create views:**

```json
{
  "tool": "notion_notion-create-view",
  "args": {
    "database_id": "feedback-db-xyz",
    "data_source_id": "feedback-db-xyz",
    "name": "All Feedback",
    "type": "table"
  }
}
```

```json
{
  "tool": "notion_notion-create-view",
  "args": {
    "database_id": "feedback-db-xyz",
    "data_source_id": "feedback-db-xyz",
    "name": "By Status",
    "type": "board",
    "configure": "GROUP BY \"Status\""
  }
}
```

```json
{
  "tool": "notion_notion-create-view",
  "args": {
    "database_id": "feedback-db-xyz",
    "data_source_id": "feedback-db-xyz",
    "name": "High Priority",
    "type": "table",
    "configure": "FILTER \"Priority\" = \"High\""
  }
}
```

**Result:**
- Database "Client Feedback" created
- 3 views configured: table, board grouped by status, filtered table
- Ready for entries to be added

---

## Quick Reference

| Action | Primary Tool | Key Parameter |
|--------|--------------|---------------|
| Add entry | `notion_notion-create-pages` | `parent.database_id` |
| Link entries | `notion_notion-update-page` | `update_properties` with relation or `update_content` |
| Find entries | `notion_notion-search` | `query`, `query_type: "internal"` |
| Update entry | `notion_notion-update-page` | `update_properties` |
| Create database | `notion_notion-create-database` | `schema` (SQL DDL) |

## Related Guides

- [structure-discovery.md](structure-discovery.md) - Discover existing workspace structure before making changes
- [database-patterns.md](database-patterns.md) - Schema design patterns and property type recommendations
- [linking-strategy.md](linking-strategy.md) - When to use relations vs inline links
