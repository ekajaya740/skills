---
name: notion-second-brain
description: "Use when user wants to interact with their Notion second brain for: (1) Adding new entries (projects, tasks, notes, knowledge), (2) Linking entries together, (3) Searching/retrieving information, (4) Updating existing entries, (5) Creating new databases. Requires Notion MCP configured with access to user's workspace."
---

# Notion Second Brain

## Overview

This skill enables Claude to interact with a user's Notion workspace as a second brain. It provides structured workflows for discovering the user's existing structure, adding new entries, linking related content, and retrieving information using Notion MCP tools.

## Prerequisite Check

Before using this skill, verify Notion MCP is configured:

1. Check if Notion tools are available in the current session
2. If Notion tools are not available, inform the user that Notion MCP must be configured first

## Discovery Workflow

Map the user's Notion structure before performing any actions:

1. **Identify top-level pages** - Search for the user's main hub pages (e.g., "Second Brain", "Dashboard", "Projects")
2. **Map databases** - Find all database structures (tables, boards, calendars) and their schemas
3. **Identify linking patterns** - Understand how entries are connected (relations, linked pages, tags)
4. **Document the structure** - Create a mental model of the workspace layout for context-aware actions

For detailed discovery techniques, see [references/structure-discovery.md](references/structure-discovery.md).

## Action Execution

After discovery, execute actions based on the user's request:

### Adding New Entries

- Create pages in existing databases or as standalone pages
- Set appropriate properties (status, dates, tags, etc.)
- Link new entries to related existing content

For creation patterns, see [references/database-patterns.md](references/database-patterns.md) and [references/action-templates.md](references/action-templates.md).

### Linking Entries

- Use Notion relations or inline page links to connect related entries
- Create hub pages that aggregate related content
- Maintain bidirectional links where appropriate

For linking strategies, see [references/linking-strategy.md](references/linking-strategy.md).

### Searching and Retrieving

- Use `notion_notion-search` for semantic search across the workspace
- Use `notion_notion-fetch` to retrieve full page/database contents
- Navigate relations to find related information

### Updating Entries

- Modify page content using `notion_notion-update-page`
- Update database properties (status changes, due dates, etc.)
- Add or remove relations as context evolves

### Creating New Databases

- Design database schema based on the user's needs
- Create appropriate views (table, board, calendar, etc.)
- Set up initial properties and relations

For database creation patterns, see [references/database-patterns.md](references/database-patterns.md).

## Quick Reference

| Action | Notion MCP Tools |
|--------|-----------------|
| Search | `notion_notion-search` |
| Fetch page/db | `notion_notion-fetch` |
| Create page | `notion_notion-create-pages` |
| Update page | `notion_notion-update-page` |
| Create database | `notion_notion-create-database` |
| Add comment | `notion_notion-create-comment` |

## Tips

- Always discover the workspace structure first before making changes
- Use the user's existing terminology and conventions
- Create entries in the appropriate parent page or database
- Link new entries to related content immediately after creation