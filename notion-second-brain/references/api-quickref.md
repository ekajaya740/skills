# Notion Second Brain — API quick reference

Cheat sheet for the migrated second brain. API version **2026-03-11**, base **https://api.notion.com**.
Contract: `notion-second-brain` (the full skill). Every request carries:

```bash
-H "Authorization: Bearer $NOTION_API_TOKEN"
-H "Notion-Version: 2026-03-11"
-H "Content-Type: application/json"
```

Token: `$WORKSPACE/.env` → `NOTION_API_KEY`, or exported. Ledger: `$WORKSPACE/migration/ledger/notion_db_ids.json`.

## Endpoints

| Purpose | Method + path |
|---|---|
| Create a page | `POST /v1/pages` |
| Read page properties | `GET /v1/pages/{page_id}` |
| Update page properties | `PATCH /v1/pages/{page_id}` |
| Read page body (markdown) | `GET /v1/pages/{page_id}/markdown` |
| Update page body (markdown) | `PATCH /v1/pages/{page_id}/markdown` |
| Query a data source | `POST /v1/data_sources/{data_source_id}/query` |
| Create a data source | `POST /v1/data_sources` (parent: `{"type":"database_id","database_id":"…"}`) |
| Create a database | `POST /v1/databases` (parent: page or workspace) |
| Update a data source | `PATCH /v1/data_sources/{data_source_id}` |
| Search pages / data sources | `POST /v1/search` |
| Create a view | `POST /v1/views` |
| Blocks (fallback) | `GET /v1/blocks/{block_id}/children`, `PATCH /v1/blocks/{block_id}/children` |

## Page creation body

```json
{
  "parent": {"type": "data_source_id", "data_source_id": "<DS_ID>"},
  "properties": {
    "Name": {"title": [{"text": {"content": "Title"}}]},
    "Type": {"select": {"name": "Reference"}},
    "Tags": {"multi_select": [{"name": "type/reference"}]},
    "Date": {"date": {"start": "2026-10-21"}},
    "Source URL": {"url": "https://example.com"},
    "Related": {"relation": [{"id": "<PAGE_ID>"}]},
    "Confidential": {"checkbox": false}
  },
  "markdown": "# Title\n\nBody as enhanced markdown.",
  "markdown_version": "v1"
}
```

## Property value shapes

| Type | Value |
|---|---|
| title | `{"title":[{"text":{"content":"…"}}]}` |
| rich_text | `{"rich_text":[{"text":{"content":"…"}}]}` |
| select | `{"select":{"name":"Active"}}` |
| multi_select | `{"multi_select":[{"name":"a"},{"name":"b"}]}` |
| status | `{"status":{"name":"Todo"}}` (not used by this brain — the schemas use select) |
| date | `{"date":{"start":"2026-10-21"}}` — `{"date":{"start":…,"end":…}}` for a range, `{"date":null}` to clear |
| checkbox | `{"checkbox":true}` |
| url | `{"url":"https://…"}` |
| number | `{"number":3}` |
| relation | `{"relation":[{"id":"<PAGE_ID>"}]}` |
| files | `{"files":[{"name":"a.pdf","external":{"url":"https://…"}}]}` — Notion-hosted file URLs expire, re-upload instead |
| created_time / last_edited_time | read-only, set by Notion |

## Query shape

```json
{
  "filter": {"and": [
    {"property": "Status", "select": {"equals": "Active"}},
    {"property": "Date", "date": {"on_or_after": "2026-10-01"}},
    {"property": "Confidential", "checkbox": {"equals": false}},
    {"property": "Related", "relation": {"contains": "<PAGE_ID>"}},
    {"property": "Related", "relation": {"is_empty": true}}
  ]},
  "sorts": [{"property": "Date", "direction": "descending"}],
  "page_size": 100
}
```

Filter operators by type: select/multi-select `equals` `does_not_equal` `contains` `does_not_contain`
`is_empty` `is_not_empty`; date `equals` `before` `after` `on_or_before` `on_or_after`
`this_week` `past_week` `past_month`; checkbox `equals`; relation `contains` `does_not_contain`
`is_empty`.

## Markdown dialect

| Construct | Syntax |
|---|---|
| Headings | `#` … `####` |
| To-do | `- [ ]` / `- [x]` |
| Table | GFM pipe table; blank line before and after |
| Callout | `<callout icon="emoji" color="blue_bg">` … children indented with a TAB … `</callout>` |
| Code fence | ```` (four backticks) when the content contains three-backtick runs |
| Block colour | `{color="Red"}` on the block's first line |
| Inline colour | `<span color="Red">text</span>` |
| Divider | `---` |
| Blockquote | `> text` |

**Escaping.** Outside code blocks, prefix these characters with a backslash:

```text
\  *  ~  `  $  [  ]  <  >  {  }  |  ^
```

Inside a table cell a literal pipe is written \\|.

## Mentions and links

| Thing | Form |
|---|---|
| Inline page mention | `<mention-page url="https://www.notion.so/<PAGE_ID>">Page title</mention-page>` |
| Ordinary link | `[label](https://…)` |
| Relation (the link graph) | the `Related`/`Project`/`Area`/`Sources`/`Supersedes`/`Source` property |
| Notion page URL | `https://www.notion.so/<PAGE_ID>` |

No `notion://` scheme. No `[[wikilink]]`. A mention uses the **page** id, never the data-source id.

## View creation

```json
{
  "data_source_id": "<DS_ID>",
  "name": "Now",
  "type": "table",
  "configuration": {
    "type": "table",
    "group_by": {"type": "select", "property": "Status"},
    "properties": [{"property_id": "Name", "visible": true}]
  },
  "filter": {"property": "Status", "select": {"does_not_equal": "Done"}},
  "sorts": [{"property": "Due", "direction": "ascending"}]
}
```

`type` ∈ table | board | list | calendar | timeline | gallery | form | chart | map | dashboard.
`group_by.type` ∈ select | status | person | relation | date | text | number | checkbox | formula.

## Limits

| Limit | Value |
|---|---|
| Requests | 3/second per connection — space ~350 ms, back off on 429, honour `Retry-After` |
| Markdown payload | < 5000 blocks per request |
| Page read-back | pages over ~20,000 blocks come back truncated — check `truncated` |
| Rich-text value | 2,000 characters |
| Multi-select / relation array | 100 elements |
| File URLs | pre-signed, **expire** — re-upload, do not re-link |

## Nine data sources and their ids

Ids live in `$WORKSPACE/migration/ledger/notion_db_ids.json`:

```json
{
  "Inbox": "<id>",
  "Projects": "<id>",
  "Tasks": "<id>",
  "Notes": "<id>",
  "Areas": "<id>",
  "Decisions": "<id>",
  "Daily Notes": "<id>",
  "Archive": "<id>",
  "Templates": "<id>",
  "root_page_id": "3f04c3376067800f8d03c40b25d6fa0c"
}
```

Lookup when a name is missing: `POST /v1/search` with
`{"filter":{"property":"object","value":"data_source"}}` and match the title.
