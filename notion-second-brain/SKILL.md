---
name: notion-second-brain
description: "Use when user wants to interact with their Notion second brain for: (1) Adding new entries (projects, tasks, notes, knowledge), (2) Linking entries together, (3) Searching/retrieving information, (4) Updating existing entries, (5) Creating new databases. Uses Notion CLI (ntn) to interact with the user's Notion workspace."
---

# Notion Second Brain

## Overview

This skill enables Claude to interact with a user's Notion workspace as a second brain using the Notion CLI (`ntn`). It provides structured workflows for discovering the user's existing structure, adding new entries, linking related content, and retrieving information.

**IMPORTANT**: This skill ALWAYS writes to Notion. Never create local files when this skill is invoked.

## Prerequisite Check

Before using this skill, verify the Notion CLI is available:

1. Check if `ntn` command is available
2. Verify `NOTION_API_TOKEN` environment variable is set
3. If not available, inform the user they need to:
   - Install: `npm i -g ntn@latest`
   - Set token: `export NOTION_API_TOKEN="secret_xxx"`

## Discovery Workflow

Map the user's Notion structure before performing any actions:

1. **Search for existing content**: Use `ntn api v1/search` to find relevant pages/databases
2. **Identify databases**: Find all database structures and their schemas
3. **Map parent pages**: Understand the workspace hierarchy (e.g., "Second Brain", "Projects", "Notes")
4. **Document the structure**: Create a mental model of the workspace layout

Example discovery commands:
```bash
# Search for databases
ntn api v1/search filter="{\"property\":\"object\",\"value\":\"database\"}"

# Search for pages with "Second Brain" in title
ntn api v1/search query="Second Brain"

# Get database schema
ntn api v1/databases/<database-id>
```

## Action Execution

After discovery, execute actions based on the user's request using `ntn api`:

### Adding New Entries

**ALWAYS use Notion** - never create local files:

```bash
# Create a page in a database
ntn api v1/pages -d '{
  "parent": {"database_id": "DATABASE_ID"},
  "properties": {
    "Name": {"title": [{"text": {"content": "Entry Title"}}]},
    "Status": {"select": {"name": "In Progress"}},
    "Tags": {"multi_select": [{"name": "tag-name"}]}
  }
}'

# Create a standalone page
ntn api v1/pages -d '{
  "parent": {"page_id": "PAGE_ID"},
  "properties": {
    "title": {"title": [{"text": {"content": "Page Title"}}]}
  }
}'
```

### Linking Entries

Create relations between entries:

```bash
# Update a page to add a relation
ntn api v1/pages/PAGE_ID -d '{
  "properties": {
    "Related": {"relation": [{"id": "OTHER_PAGE_ID"}]}
  }
}'

# Add a mention in page content
ntn api v1/blocks/PAGE_ID/children -d '{
  "children": [{
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{
        "type": "mention",
        "mention": {"type": "page", "page": {"id": "OTHER_PAGE_ID"}}
      }]
    }
  }]
}'
```

### Searching and Retrieving

```bash
# Search across workspace
ntn api v1/search query="search terms"

# Fetch specific page content
ntn api v1/blocks/PAGE_ID/children

# Query database with filters
ntn api v1/databases/DB_ID/query -d '{
  "filter": {
    "property": "Status",
    "select": {"equals": "Done"}
  }
}'
```

### Updating Entries

```bash
# Update page properties
ntn api v1/pages/PAGE_ID -d '{
  "properties": {
    "Status": {"select": {"name": "Completed"}},
    "Completed Date": {"date": {"start": "2024-01-15"}}
  }
}'

# Append content to a page
ntn api v1/blocks/PAGE_ID/children -d '{
  "children": [{
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{"type": "text", "text": {"content": "Additional content"}}]
    }
  }]
}'
```

### Creating New Databases

```bash
# Create a database as child of a page
ntn api v1/databases -d '{
  "parent": {"page_id": "PAGE_ID"},
  "title": [{"type": "text", "text": {"content": "Database Title"}}],
  "properties": {
    "Name": {"title": {}},
    "Status": {"select": {"options": [{"name": "Todo", "color": "red"}, {"name": "Done", "color": "green"}]}},
    "Tags": {"multi_select": {"options": []}}
  }
}'
```

## Quick Reference

| Action | Notion CLI Command |
|--------|-------------------|
| Search | `ntn api v1/search` |
| Fetch page | `ntn api v1/pages/PAGE_ID` |
| Fetch blocks | `ntn api v1/blocks/PAGE_ID/children` |
| Create page | `ntn api v1/pages` |
| Update page | `ntn api v1/pages/PAGE_ID` |
| Query database | `ntn api v1/databases/DB_ID/query` |
| Create database | `ntn api v1/databases` |
| Add blocks | `ntn api v1/blocks/PAGE_ID/children` |

## Tips

- **Always use Notion**: When this skill is invoked, all data goes to Notion. Never create local files.
- Discover the workspace structure first before making changes
- Use the user's existing terminology and conventions
- Create entries in the appropriate parent page or database
- Link new entries to related content immediately after creation
- **Topics/Tags formatting**: Always use kebab-case for tags and topics (e.g., `my-topic`, `project-alpha`, `urgent-task`)
- Use `ntn api <path> --help` for quick reference on any endpoint

## Self-Documentation

Always prefer checking the CLI help over guessing:

```bash
ntn api ls                    # List all endpoints
ntn api v1/pages --help       # Help for pages endpoint
ntn api v1/pages --docs       # Full official docs
ntn <command> --help          # General command help
```
