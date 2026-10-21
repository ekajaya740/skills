# Duplicate Resolution - Comparing an Inbox Row With an Existing Version

When a duplicate is detected (same Source URL, near-identical title, or substantially the same
content), decide which version to keep and whether to merge.

## Step 1: Compare versions

| Aspect | Check |
|---|---|
| **Properties** | Does the existing row have proper Type/Status/Tags/Source URL? If not, the inbox version may be better. |
| **Content quality** | Is the existing version a condensed summary (clean) or a raw clipping (full of HTML, video tags, social media metadata)? |
| **Completeness** | Does the inbox version have substantive text the existing one lacks, or is it just noise? |

## Step 2: Decide the action

| Scenario | Action |
|---|---|
| Existing is a **condensed summary** and the inbox row is a **raw clipping** | Delete the inbox duplicate. The existing version is better. |
| Existing is **missing properties** or has **stale content** | Merge the inbox content into the existing row, then delete the inbox row. |
| Inbox version has **substantive new content** | Merge it into the existing row (add sections, update the summary), then delete the inbox row. |
| Both are raw clippings, same source | Delete the inbox duplicate; keep the one with better properties. |

## Step 3: Merge

1. Read the existing row (`nb GET /v1/pages/{id}/markdown`)
2. Identify what is missing
3. Write the merged body:
   ```bash
   nb PATCH /v1/pages/<existing_page_id>/markdown '{"type":"replace_content",
     "replace_content":{"new_str":"<merged body>"}}'
   ```
   (or `update_content` with `content_updates` for a targeted change)
4. Copy the missing properties across with `nb PATCH /v1/pages/{id}`

## Step 4: Delete the duplicate

Duplicates are deleted, not archived - the one exception to "never delete a page":

```bash
nb DELETE /v1/pages/<inbox_page_id>
```

Safe because the canonical copy lives in Notes, Projects or Areas.

## Common patterns

**Raw clipping vs. condensed summary (most common):** the inbox row is a full thread with
`<video>`, `<img>` and social boilerplate; the existing row is clean markdown with properties
and key points. Action: delete the inbox row, keep the summary.

**Same source, missing properties:** the inbox row has the Source URL and tags, the existing row
has none. Action: merge the properties into the existing row, then delete the inbox row.
