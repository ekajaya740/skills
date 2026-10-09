---
name: spa-data-extraction
description: "Extract structured data from modern JS-heavy SPAs (Inertia.js, Next.js, Nuxt) by discovering hidden API endpoints in server-rendered HTML state, then paginating and enriching from detail pages."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [web-scraping, data-extraction, spa, inertia, nextjs, nuxt, api-discovery, pagination, enrichment]
    related_skills: [gws-calendar]
---

# SPA Data Extraction

Use this skill when a target website loads its content dynamically (JS framework SPA) but serves its initial HTML via SSR — and you need to extract structured data rather than render/interact with the page in a browser.

## Core insight

Modern SSR frameworks (Inertia.js + Vue, Next.js, Nuxt) embed **API route definitions and raw data** inside the initial HTML payload as a JSON attribute or global variable. You can extract this, call the APIs directly via curl, and get structured JSON — no browser rendering needed.

## Framework signatures

| Framework | Where data lives | How to find |
|-----------|-----------------|-------------|
| **Inertia.js** (Laravel + Vue) | `data-page` attribute on `#app` div | `grep -oP 'data-page="[^"]*"'` then JSON decode |
| **Next.js** | `__NEXT_DATA__` script tag | `grep -oP '__NEXT_DATA__\s*=\s*({[^<]+})'` |
| **Nuxt** | `window.__NUXT__` | `grep -oP '__NUXT__\s*=\s*({[^<]+})'` |
| **Gatsby** | `window.__GATSBY` | Similar pattern |
| **Remix** | `window.__remixContext` | Similar pattern |

## Workflow

### Step 1: Find the embedded state

Fetch the page with curl (browser is overkill for this):

```bash
curl -s 'https://target-site.com/page' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  -H 'Accept: text/html,application/xhtml+xml' \
  -o /tmp/page.html
```

For **Inertia.js**, search for the `data-page` attribute:

```bash
grep -oP 'data-page="[^"]*"' /tmp/page.html | head -1 | sed 's/data-page="//;s/"$//' | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(json.dumps(d,indent=2))" 2>/dev/null | head -100
```

If the JSON is HTML-entity-encoded (`&quot;`), handle it:

```bash
python3 -c "
import html, json, re
raw = open('/tmp/page.html').read()
m = re.search(r'data-page=\"([^\"]+)\"', raw)
d = json.loads(html.unescape(m.group(1)))
print(json.dumps(d, indent=2)[:5000])
"
```

### Step 2: Find the API endpoint

Inside the embedded state, look for:
- **Route definitions** — the app's route list often includes API URLs (Inertia shares routes as `ziggy` config)
- **Direct data** — sometimes the page's actual data is embedded here too (pagination links, initial data set)
- **Prefetched/graphql queries** — look for query names that match the page content

Key things to grep for in the decoded JSON:
- `"api/"` — API route prefixes
- `"url":"` — pagination URL patterns
- `"links"` — pagination link objects
- `"next"` — next page link
- `"path"` — current API path

### Step 3: Call the API directly

```bash
curl -s 'https://api.target-site.com/api/endpoint?page=N&param=value' \
  -H 'User-Agent: Mozilla/5.0' \
  -H 'Accept: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Referer: https://target-site.com/original-page'
```

**Important headers:**
- `Accept: application/json` — tells the server to return JSON, not HTML
- `X-Requested-With: XMLHttpRequest` — some Laravel/Inertia apps gate on this
- `Referer: <original page>` — API may check origin

### Step 4: Paginate

From the first API response, read:
- `meta.last_page` or `meta.total` — how many pages
- `links.next` — next page URL (sometimes absolute, sometimes relative)
- `links.first` / `links.last` — boundary URLs

Loop through pages:

```bash
for page in $(seq 1 23); do
  curl -s "https://api.target-site.com/api/articles?page=$page&prefecture=5" \
    -H 'Accept: application/json' \
    -o "/tmp/data_page_$page.json"
done
```

Filter for the data type you need (e.g., events vs. articles vs. guides):

```bash
python3 -c "
import json
for p in range(1, 24):
    d = json.load(open(f'/tmp/data_page_{p}.json'))
    events = [it for it in d['data'] if it['type'] == 'event']
    print(f'Page {p}: {len(events)} events')
    for ev in events:
        ed = ev.get('event_date', {})
        print(f'  {ev[\"title\"]} | {ed.get(\"start\",\"?\")} - {ed.get(\"end\",\"?\")}')
"
```

### Step 5: Enrich from detail pages

The list API often returns **truncated** data — no venue, no address, no full description, and **descriptions are clipped to ~150 characters (card-grid preview length)**. Get the full data from each item's individual page (which is also SSR'd):

**Why list descriptions are truncated:** List endpoints are designed for card-grid rendering. They return just enough text for a preview snippet. The full `content` (all paragraphs, often 500–2000 chars) and `directions` (access info) only exist on the detail page's `data-page` JSON under `article.content` and `article.directions`.

**Scaling enrichment across many items:** If you have 9–50 detail pages to enrich, batch them in parallel with `delegate_task` (passing URLs as context) or use Python's `concurrent.futures.ThreadPoolExecutor` with `urllib.request` in a single script with `timeout=15` per request. Sequential HTTP for 20+ pages blocks the session unnecessarily.

```bash
curl -s 'https://target-site.com/akita/event-slug/12345' \
  -H 'User-Agent: Mozilla/5.0' | python3 -c "
import html, json, re, sys
raw = sys.stdin.read()
m = re.search(r'data-page=\"([^\"]+)\"', raw)
d = json.loads(html.unescape(m.group(1)))
article = d.get('article', d.get('props', {}).get('article', {}))
print(f'Venue: {article.get(\"event_venue\",\"\")}')
print(f'Address: {article.get(\"address_en\",\"\")}')
print(f'Name (JA): {article.get(\"event_name_ja\",\"\")}')
print(f'Website: {article.get(\"website\",\"\")}')
print(f'Location: {article.get(\"location\",{})}')
print(f'Directions: {article.get(\"directions\",\"\")[:200]}')
"
```

### Step 6: Filter by date criteria

Use `start_date[:4]` to filter by year, compare dates with the current date, etc.:

```python
from datetime import date
today = date(2026, 6, 16)
if start and start[:4] == '2026':
    start_date = date.fromisoformat(start[:10])
    if start_date >= today:
        # Include this item
```

## Pitfalls

- **HTML entity encoding** — Inertia pages encode JSON as `&quot;` instead of `"`. Always use `html.unescape()` before `json.loads()`.
- **Route-based pagination** — some APIs use page-based (`?page=N`), others use cursor-based. Check `links` object.
- **Rate limiting** — add `sleep(0.5)` between pages if the server is aggressive.
- **URL encoding** — the embedded `data-page` JSON may have `\\/` escaped slashes. `json.loads` handles this, but `grep`-based extraction may break.
- **Incomplete data in list views** — list endpoints often omit venue/address/price fields. Always enrich from detail pages.
- **Non-English duplicates** — The same event may appear in multiple languages (en, fr, de, it, ko, th, vi, ru, es, pt, id, ar). Each language variant has a different `id` and `url` but represents the same real-world event. Filter by `item.lang == "en"` or deduplicate by checking `translations` / `alternate` hreflang tags on the detail page. Some pages contain 15+ language alternates.
- **List API lat/lng is prefecture centroid, not event-specific** — The `prefecture.location` field in list responses points to the prefecture's administrative center, not the event venue. Always enrich from the detail page's `article.location` for precise coordinates.
- **Past/future events mixed** — filter by date, not just event type. Some events in the API may have already passed for the current year.
- **Price field** — `event_free: true` means free; `event_general_price: 0` doesn't always mean free (check both).
- **Time info** — `unknown_start_time: true` / `unknown_end_time: true` flags events where the exact time is not known — treat as all-day in calendar inserts.

## Output format for calendar insertion

After extracting and enriching, events can be inserted into Google Calendar using the REST API directly (bypass gws CLI when token cache is stale):

```python
headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
for ev in events:
    requests.post(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        headers=headers,
        json=ev  # full event object with summary, description, location, start, end
    )
```

See the `gws-calendar` skill for the full Google Calendar event schema.