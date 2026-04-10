---
name: notion-second-brain
description: "Use when user wants to interact with their Notion second brain for: (1) Adding new entries (projects, tasks, notes, knowledge), (2) Linking entries together, (3) Searching/retrieving information, (4) Updating existing entries, (5) Creating new databases. Uses Notion CLI (ntn) to interact with the user's Notion workspace."
---

# Notion Second Brain

## Overview

This skill enables Claude to interact with a user's Notion workspace as a second brain using the Notion CLI (`ntn`). It provides structured workflows for discovering the user's existing structure, adding new entries, linking related content, and retrieving information.

**IMPORTANT**: This skill ALWAYS writes to Notion. Never create local files when this skill is invoked.

## Critical Discovery Phase

**ALWAYS discover the user's actual Notion structure BEFORE creating any entries.** The user's structure may differ from assumptions. Use the database IDs from URLs to query actual schemas.

### User's Known Database IDs

When user provides URLs, extract the database ID from the URL path:
- URL: `https://www.notion.so/ekajaya740/{DATABASE_ID}?v=...`
- Extract: The 32-character ID between workspace name and `?v=`

### Standard Database Schema (Verified)

Based on discovery, the user's databases have these schemas:

**Notes Database** (`4de4c337606782d4b9e381a96e9d5384`):
- Name (title), Status, Topics (relation), Areas (relation), Projects (relation), Tasks (relation), Notebook (relation), Archive (checkbox), Favorite (checkbox)

**Areas Database** (`1cc4c337606782b5930601142c3241ad`):
- Name (title), Type (select: Personal/Business), Notes (relation), Projects (relation), Resources (relation), Archive (checkbox)

**Topics Database** (`af74c3376067830f8e4401fbf30ac3ce`):
- Name (title), Notes (relation), Resources (relation)

**Projects Database** (`c314c33760678294827a81d57f5cae42`):
- Name (title), Status, Areas (relation), Start Date, End Date, Progress (rollup), Notes (relation), Tasks (relation), Resources (relation), Archive (checkbox)

**Tasks Database** (`10f4c3376067827a974a819e394aa4e8`):
- Name (title), Description (rich_text), Date, Complete (checkbox), Projects (relation), Notes (relation), Resources (relation), URL

**Resources Database** (`0904c3376067838695a481b8512f6778`):
- Name (title), Type (select: Video/Book/etc), Status, URL, Favorite (checkbox), Areas (relation), Projects (relation), Topics (relation), Archive (checkbox), Description (rich_text)

**Notebook Database** (`0c24c3376067820498b1017cec7c8714`):
- Name (title), Notes (relation), Archive (checkbox)

## Prerequisite Check

Before using this skill, verify the Notion CLI is available:

1. Check if `ntn` command is available
2. Verify `NOTION_API_TOKEN` environment variable is set
3. If not available, inform the user they need to:
   - Install: `npm i -g ntn@latest`
   - Set token: `export NOTION_API_TOKEN="secret_xxx"`

## Discovery Workflow

**MANDATORY** - Always discover structure first:

1. **Extract database IDs from URLs** provided by user
2. **Query each database** to get actual schema with properties
3. **Identify relations** between databases (dual-property relations are synced)
4. **Query existing entries** to understand current content

```bash
# Get database schema (use data_source_id from results)
ntn api v1/databases/<database-id> -X GET

# Query database entries (use data_source_id, NOT database_id)
ntn api v1/data_sources/<data_source_id>/query -d '{"page_size": 5}'

# Search across workspace
ntn api v1/search -d '{"query": "search terms"}'
```

## Data Source vs Database ID

**CRITICAL**: Notion API uses two different IDs:
- `database_id`: The database itself (from URL)
- `data_source_id`: The underlying data source (found in query results)

When creating/querying pages, use `data_source_id` from the database query results.

## Action Execution

### Creating a Note Entry (Readlist/Watchlist)

For anime, comics, books, or any media entries:

1. **Create Note** in Notes database with Area relation and icon
2. **Update Area** bidirectionally (Area → Note)

**Topics are only added if the user explicitly mentions them.**

```bash
# Step 1: Create note with Area relation and icon (from Notes Template)
ntn api v1/pages -d '{
  "parent": {"database_id": "NOTES_DATABASE_ID"},
  "icon": {"type": "icon", "icon": {"color": "gray", "name": "document"}},
  "properties": {
    "Name": {"title": [{"text": {"content": "Entry Title"}}]},
    "Areas": {"relation": [{"id": "AREA_ID"}]}
  }
}'

# Step 2: Update area to link back (bidirectional)
ntn api v1/pages/AREA_ID -X PATCH -d '{
  "properties": {
    "Notes": {"relation": [{"id": "NOTE_ID"}]}
  }
}'
```

**If user explicitly mentions a topic**, also create and link it (see Optional Topic section below).

### Linking Entries

Relations in Notion work bidirectionally - updating one side doesn't always auto-update the other. Always update both sides:

```bash
# Update page to add relation
ntn api v1/pages/PAGE_ID -X PATCH -d '{
  "properties": {
    "RelatedProperty": {"relation": [{"id": "OTHER_PAGE_ID"}]}
  }
}'
```

### Searching and Retrieving

```bash
# Search across workspace
ntn api v1/search -d '{"query": "search terms"}'

# Fetch specific page content
ntn api v1/blocks/PAGE_ID/children

# Query database (use data_source_id from schema)
ntn api v1/data_sources/DATA_SOURCE_ID/query -d '{"page_size": 100}'
```

### Updating Entries

```bash
# Update page properties (requires PATCH method)
ntn api v1/pages/PAGE_ID -X PATCH -d '{
  "properties": {
    "PropertyName": {"select": {"name": "Value"}}
  }
}'

# Append content to a page
ntn api v1/blocks/PAGE_ID/children -X PATCH -d '{
  "children": [{
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{"type": "text", "text": {"content": "Content"}}]
    }
  }]
}'
```

## Icon Reference

All entries should use these icons from the Notion icon set:

| Type | Icon Name | Icon |
|------|-----------|------|
| Notes | `document` | 📄 |
| Areas | `looped-square` | 🔄 |
| Notebooks | `book-closed` | 📗 |
| Topics | `tag` | 🏷️ |
| Projects | `folder` | 📁 |
| Resources | `bookmark` | 🔖 |
| Tasks | `checkmark` | ✅ |

```bash
# Icon format for creating pages
"icon": {"type": "icon", "icon": {"color": "gray", "name": "<icon-name>"}}

# For Tasks (or if emoji preferred), use:
"icon": {"type": "emoji", "emoji": "✅"}
```

## Known Area IDs

| Area Name | Area ID | Content Type | Icon |
|-----------|---------|--------------|------|
| Anime アニメ | `3284c337-6067-8132-a673-c014bf8ddba6` | Anime (TV, OVA, ONA) | 🔄 |
| Comic | `3374c337-6067-81aa-939f-d127aa20bea8` | Manga, Webtoons, Comics | 🔄 |
| Language | `3254c337-6067-8173-a514-d0dad6f110b7` | Language learning | 🔄 |
| Programming | `3254c337-6067-819f-aba6-d0ca073d1dda` | Programming projects | 🔄 |

### Content Type Classification

| Content Type | Use Area | Example |
|--------------|----------|---------|
| Anime (TV, OVA, ONA) | Anime アニメ | Dr. Stone, Attack on Titan |
| Manga/Webtoons/Comics | **Comic** | Nano Machine, One Piece |
| Films/Movies | Resources or appropriate Area | Spirited Away |
| Books | Appropriate Area | Clean Code |
| TV Series | Appropriate Area | Breaking Bad |

## Page Content Template

For media series entries (anime, comics, books), use the structure from 薬屋のひとりごと (The Apothecary Diaries) as the reference template.

### **IMPORTANT: Only Add Season/Volume Headers When User Mentions Them**

- **DEFAULT (no season labels)**: List episodes/chapters directly after the divider, no season header
- **ONLY when user mentions multiple seasons/volumes**: Use Season/Volume headers

### Default Template (No Season Labels - Use This When Not Mentioning Seasons)

```
## [Title] ([Native Title]) — [English Title]

Genre: [Genre1, Genre2, Genre3]

---

- [ ] [Episode/Chapter 1 Title]
- [ ] [Episode/Chapter 2 Title]
- [x] [Episode/Chapter 3 Title] (checked = completed)

---

### Notes

- **Status:** Use checkboxes to mark episodes/chapters as watched
- **Last Updated:** {{date}}

### Resources

- [MyAnimeList](url)
- [Official Website](url)
```

### Multi-Season Template (Only When User Mentions OR Known to Have Multiple)

```
## [Title] ([Native Title]) — [English Title]

Genre: [Genre1, Genre2, Genre3]

---

### Season 1

- [ ] [Episode/Chapter 1 Title]
- [ ] [Episode/Chapter 2 Title]
- [x] [Episode/Chapter 3 Title] (checked = completed)

### Season 2

- [ ] [Episode/Chapter 1 Title]

---

### Notes

- **Status:** Use checkboxes to mark episodes/chapters as watched
- **Last Updated:** {{date}}

### Resources

- [MyAnimeList](url)
- [Official Website](url)
```

See `references/watchlist-templates.md` for detailed templates and examples.

## Common Mistakes to Avoid

1. **Don't assume database structure** - Always query to verify
2. **Don't create new databases** unless user explicitly asks - Use EXISTING databases
3. **Don't forget bidirectional relations** - Update both sides
4. **Use correct IDs** - data_source_id for queries, database_id for creation
5. **Use PATCH for updates** - POST creates, PATCH modifies

## Quick Reference

| Action | Notion CLI Command |
|--------|-------------------|
| Get database schema | `ntn api v1/databases/<id> -X GET` |
| Query entries | `ntn api v1/data_sources/<id>/query -d '{}'` |
| Search | `ntn api v1/search -d '{"query": "terms"}'` |
| Create page | `ntn api v1/pages -d '{...}'` |
| Update page | `ntn api v1/pages/<id> -X PATCH -d '{...}'` |
| Append blocks | `ntn api v1/blocks/<id>/children -X PATCH -d '{...}'` |

## Tips

- **Always discover first** - User's structure may differ from assumptions
- **Use existing databases** - Don't create new ones unless asked
- **Bidirectional relations** - Update both sides of any relation
- **Topics/Tags formatting** - Always use kebab-case (e.g., `nano-machine`)
- **Media entries** → Notes database with Area/Topic relations
- Use `ntn api <path> --help` for quick reference

## Self-Documentation

```bash
ntn api ls                    # List all endpoints
ntn api v1/pages --help       # Help for pages endpoint
ntn api v1/pages --docs       # Full official docs
ntn <command> --help          # General command help
```
