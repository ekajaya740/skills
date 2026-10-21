# Duplicate Detection by Source URL

## Problem

The same article or video is often clipped twice under different titles. Title-based duplicate
checks miss it because the Inbox row keeps the original page title while the filed row keeps a
shortened title, and the same URL can arrive with different wording each time.

## Solution

Before writing a Notes row, check the existing Notes rows for a matching `Source URL`.

```bash
# One query, then compare
nb POST "/v1/data_sources/$NOTES_DS/query" '{"page_size":100}' > /tmp/notes.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/notes.json"))
urls = {}
for r in d["results"]:
    p = r["properties"]
    u = p.get("Source URL", {}).get("url")
    if u:
        urls[u] = p["Name"]["title"][0]["text"]["content"]
json.dump(urls, open("/tmp/source_urls.json", "w"), indent=2)
print("known source urls:", len(urls))
PY
```

Then, for each clipping, look its `Source URL` up in the map:

- found -> **skip** the clipping, log it in the report as a duplicate
- not found -> proceed with the write

The Inbox row of a duplicate is retired with `Status` = `Dropped` - it is not deleted.

## Example

In the 2026-06-28 run:

- `Strengthening THIS Makes EVERYTHING Easier` (source:
  `https://www.youtube.com/watch?v=lHoCygBVqj4`) -> already existed as the Notes row
  "grip strength finger training calisthenics" with the same Source URL
- `Why MOST People NEVER Pass Beginner Calisthenics` (source:
  `https://www.youtube.com/watch?v=OHtSJjXxHGM`) -> already existed as the Notes row
  "calisthenics common mistakes progression" with the same Source URL

Both were correctly skipped as duplicates.

## Efficiency tip

For cron runs with many clippings, batch the source-URL check: query the Notes data source **once**
and build a URL -> title map, then check every clipping against that map. Do not query per
clipping - the rate limit is 3 requests/second.

## Note on the old filename check

Filename slugs (`04-Resources/grip-strength-....md`) no longer exist. The URL is the only stable
identity a clipping has, so it is the only thing worth matching on.
