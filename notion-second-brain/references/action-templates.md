# Action Templates

Practical step-by-step templates for common Notion second brain operations using the Notion CLI (`ntn`).

## Table of Contents

1. [Add New Entry](#template-1-add-new-entry)
2. [Link Entries](#template-2-link-entries)
3. [Find Related Entries](#template-3-find-related-entries)
4. [Update Entry Status](#template-4-update-entry-status)

---

## Template 1: Add New Entry

**Trigger:** User says "add a new [project/task/note] about X" or "create entry for X"

**Purpose:** Create a new page in an existing database with proper properties and links

### Steps

1. **Extract database ID from URL** (if provided) or search for the database
2. **Query the database** to get its schema and data_source_id
3. **Check for duplicates** - search for existing entries with the same name
4. **Prepare properties**:
   - Map values to schema properties
   - **Status**: If database has Status and user didn't specify, set to "Inbox"
   - **Topics/Tags**: Always use kebab-case (e.g., `my-topic`)
5. **Create the page** with `ntn api v1/pages`
6. **Link to related entries** bidirectionally

### CLI Commands

```bash
# Search for existing entry
ntn api v1/search -d '{"query": "Entry Name"}'

# Get database schema (use database_id from URL)
ntn api v1/databases/DATABASE_ID -X GET

# Query to get data_source_id
ntn api v1/data_sources/DATA_SOURCE_ID/query -d '{"page_size": 1}'

# Create page (use data_source_id in parent)
ntn api v1/pages -d '{
  "parent": {"database_id": "NOTES_DATABASE_ID"},
  "properties": {
    "Name": {"title": [{"text": {"content": "Entry Title"}}]},
    "Status": {"status": {"name": "Inbox"}}
  }
}'

# Add bidirectional relations
ntn api v1/pages/PAGE_ID -X PATCH -d '{
  "properties": {
    "Topics": {"relation": [{"id": "TOPIC_ID"}]}
  }
}'
```

### Example: Add Anime to Watchlist

```bash
# 1. Search if entry exists
ntn api v1/search -d '{"query": "Nano Machine"}'

# 2. Create topic if needed
ntn api v1/pages -d '{
  "parent": {"database_id": "TOPICS_DB_ID"},
  "properties": {"Name": {"title": [{"text": {"content": "nano-machine"}}]}}
}'

# 3. Create note in Notes database
ntn api v1/pages -d '{
  "parent": {"database_id": "NOTES_DB_ID"},
  "properties": {
    "Name": {"title": [{"text": {"content": "Nano Machine"}}]},
    "Areas": {"relation": [{"id": "ANIME_AREA_ID"}]},
    "Topics": {"relation": [{"id": "TOPIC_ID"}]}
  }
}'

# 4. Bidirectional links
ntn api v1/pages/AREA_ID -X PATCH -d '{
  "properties": {
    "Notes": {"relation": [{"id": "NOTE_ID"}]}
  }
}'
```

---

## Template 2: Link Entries

**Trigger:** User says "link [entry A] to [entry B]" or "connect X with Y"

**Purpose:** Create bidirectional links between existing entries

### Steps

1. **Find both entries** using search
2. **Determine relation method**:
   - Both are database entries → use relation property
   - One is standalone page → use inline page link in content
3. **Update both sides** of the relation

### CLI Commands

```bash
# Find entry A
ntn api v1/search -d '{"query": "Entry A Name"}'

# Update relation property (use PATCH method)
ntn api v1/pages/PAGE_A_ID -X PATCH -d '{
  "properties": {
    "PropertyName": {"relation": [{"id": "PAGE_B_ID"}]}
  }
}'

# Add inline page link to content
ntn api v1/blocks/PAGE_A_ID/children -X PATCH -d '{
  "children": [{
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{
        "type": "mention",
        "mention": {"type": "page", "page": {"id": "PAGE_B_ID"}}
      }]
    }
  }]
}'
```

---

## Template 3: Find Related Entries

**Trigger:** User says "find all entries related to X" or "show me connections to X"

### CLI Commands

```bash
# Search for related entries
ntn api v1/search -d '{"query": "search terms"}'

# Query database for entries with specific relation
ntn api v1/data_sources/DATA_SOURCE_ID/query -d '{"page_size": 100}'

# Get page content
ntn api v1/blocks/PAGE_ID/children
```

### Output Format

```
Found N related entries:

1. **Entry Name** 
   URL: https://notion.so/Entry-ID
   Type: Note/Area/Topic/Project
   Relations: Areas → Anime, Topics → nano-machine

2. ...
```

---

## Template 4: Update Entry Status

**Trigger:** User says "update the status of X to Y" or "mark X as done"

### CLI Commands

```bash
# Find the entry first
ntn api v1/search -d '{"query": "Entry Name"}'

# Update properties (NOTE: requires PATCH method, not POST)
ntn api v1/pages/PAGE_ID -X PATCH -d '{
  "properties": {
    "Status": {"status": {"name": "Done"}}
  }
}'

# Verify update
ntn api v1/pages/PAGE_ID -X GET
```

---

## Quick Reference

| Action | CLI Command |
|--------|-------------|
| Search | `ntn api v1/search -d '{"query": "terms"}'` |
| Get database schema | `ntn api v1/databases/<id> -X GET` |
| Query database | `ntn api v1/data_sources/<id>/query -d '{}'` |
| Create page | `ntn api v1/pages -d '{...}'` |
| Update page | `ntn api v1/pages/<id> -X PATCH -d '{...}'` |
| Append blocks | `ntn api v1/blocks/<id>/children -X PATCH -d '{...}'` |

## Common Mistakes

1. **Using POST instead of PATCH** for updates → Use `-X PATCH`
2. **Forgetting bidirectional links** → Always update both sides
3. **Wrong ID type** → Use `data_source_id` for queries, `database_id` for creation
4. **Status handling** → Default to "Inbox" if user doesn't specify

## Related Guides

- [structure-discovery.md](structure-discovery.md) - Discover existing workspace structure
- [database-patterns.md](database-patterns.md) - Schema design patterns
- [linking-strategy.md](linking-strategy.md) - Relations vs inline links
