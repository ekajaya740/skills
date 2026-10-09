# RSS Feed Configuration

Default and fallback RSS feeds used by the daily briefing skill.

## Default Feeds (High Reliability)

| Source | URL | Category | Fallback |
|---|---|---|---|
| BBC World | `https://feeds.bbci.co.uk/news/world/rss.xml` | Geopolitics | Direct homepage scrape |
| BBC Business | `https://feeds.bbci.co.uk/news/business/rss.xml` | Markets | Direct homepage scrape |
| BBC Technology | `https://feeds.bbci.co.uk/news/technology/rss.xml` | Tech/Science | Direct homepage scrape |
| BBC US & Canada | `https://feeds.bbci.co.uk/news/us_and_canada/rss.xml` | US Policy | Direct homepage scrape |

## Alternative / Fallback Feeds (Rate-Limited)

| Source | URL | Category | Notes |
|---|---|---|---|
| Reuters World | `https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best` | Markets | Frequently rate-limited via jina.ai; prefer direct fetch |
| CNBC World | `https://www.cnbc.com/id/100727362/device/rss/rss.html` | Business | Large feed, slower |

## Feed Reliability Troubleshooting

### BBC Feeds Blocked
If `requests.get()` receives `403 Forbidden` or `SecurityCompromiseError`:
- The BBC CDNs may block datacenter IPs.
- **Fix:** Add a realistic `User-Agent` header: `"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"`
- **Fix:** If direct RSS fails, fall back to `r.jina.ai/http://feeds.bbci.co.uk/news/world/rss.xml`

### Reuters / AP / TechCrunch Blocked
These sources aggressively block `r.jina.ai` after ~5 requests/minute.
- **Fix:** Always use direct RSS/Atom feed URLs first.
- **Fix:** If you must scrape, rotate across multiple sources and never hit the same domain more than 3 times per minute.

### General Rate-Limit Handling
```python
import time, requests

def safe_fetch(url, headers=None, retries=2, backoff=30):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers or {"User-Agent": "Mozilla/5.0"}, timeout=20)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 403, 451):
                if attempt < retries:
                    time.sleep(backoff * (attempt + 1))
                    continue
        except Exception:
            if attempt < retries:
                time.sleep(backoff)
                continue
    return None
```

### jina.ai Fallback (Use Sparingly)
When direct RSS is unavailable, `r.jina.ai/http://URL` returns plain text extraction:
```python
url = "https://r.jina.ai/http://www.bbc.com/news"
resp = requests.get(url, timeout=30)
```
⚠️ Limit to ≤5 requests per minute. If rate-limited, wait 60s before retry.

## Adding a Custom Source

1. Find the website's RSS/Atom feed (via `/feed`, `/rss.xml`, or browser dev tools)
2. Test with `curl -s "URL" | head -n 20`
3. If well-formed XML with `<item>` tags, add to the `FEEDS` dict in `scripts/fetch_briefing.py`
4. Map the feed to a category in `cat_map`
5. Validate output by running `python scripts/fetch_briefing.py`
