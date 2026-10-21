# Curation Pattern: Clippings -> Notes Rows

For inbox rows that are web clippings/articles (tutorials, guides, explainers), the workflow is:

1. **Create a NEW condensed Notes row** (Type=Reference, or Type=Note related to a project/area)
2. **Retire the original** by setting the Inbox row's Status to `Filed`

## Why not move?

The original clipping content often has messy titles and extraneous content (ads, thread metadata,
comments). A clean summary row gives:
- proper properties (Type, Status, Date, Tags, Source URL)
- relations to related notes
- condensed, LLM-digested content
- a consistent, searchable title

## Property template for a reference row

```json
{
  "Name": {"title":[{"text":{"content":"<short descriptive title>"}}]},
  "Type": {"select":{"name":"Reference"}},
  "Status": {"select":{"name":"Active"}},
  "Date": {"date":{"start":"2026-10-21"}},
  "Tags": {"multi_select":[{"name":"status/seed"},{"name":"type/reference"}]},
  "Source URL": {"url":"<original URL>"}
}
```

## Body template

```markdown
# <Title>

<2-3 sentence summary of the key insight>

## Key Points

- Bullet 1
- Bullet 2
- Bullet 3

## Related

- <mention-page url="https://www.notion.so/<PAGE_ID>">Other note</mention-page>
```

## The original

Retire the inbox row (`Status` = `Filed`), and if the original text is worth keeping, put it in
an **Archive** row with `Original Path` = the inbox page id, or link it from the summary body.
