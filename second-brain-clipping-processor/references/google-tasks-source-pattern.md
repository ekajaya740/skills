# Google Tasks Source Pattern

Some Inbox clippings have a `Source URL` pointing at `tasks.google.com` rather than a public web
URL. These are notes that were flagged/synced from the Google Tasks inbox via the daily note
pipeline, not traditional web clippings.

## Characteristics

- `Source URL` is a `https://tasks.google.com/task/...` link
- The content is a meta-note describing a task that was in the Google Tasks inbox, often with
  "Flagged from Google Tasks inbox on YYYY-MM-DD"
- The note may contain "Action Needed" sections asking for clarification
- The title may be tentative, contain question marks, or mix languages (e.g. Indonesian + English)

## How to Handle

Treat them as normal clippings:
1. The source URL is valid - preserve it in the `Source URL` property
2. The title should reflect the actual task content (e.g. "retardmaxxing", "some by me merah")
3. Relate it to the most relevant area/project based on tags and content (e.g. health-related ->
   the Fitness area)
4. Don't skip just because the source isn't a public URL

## Real Examples (2026-06-27)

| Original Inbox title | Filed Notes title | Source URL | Linked to |
|---------------------|-------------------|------------|-----------|
| `2026-06-27-Retardmaxxing.md` | retardmaxxing | tasks.google.com/task/bUyCBmdAZulFL_Cn | Fitness area |
| `2026-06-27-Some-by-me-merah.md` | some-by-me-merah | tasks.google.com/task/_XBjYqGIxcbvnyER | Fitness area |

## Notion specifics

- The `Source URL` property takes the `tasks.google.com` link verbatim.
- The Area/Project relation is what carries the "linked to" meaning - there is no `links:` field.
- If the task became a real Task row, create it in the **Tasks** data source and relate it with
  `Source` back to the Notes row.
