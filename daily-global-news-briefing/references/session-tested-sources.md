# Session-Tested RSS Sources

Verified working during session 2026-05-14. These feeds returned clean XML with CDATA-wrapped titles via direct Python `requests` fetch.

## Working Feeds (High Reliability)

| Feed | URL | Category | Notes |
|---|---|---|---|
| BBC World | `https://feeds.bbci.co.uk/news/world/rss.xml` | Geopolitics | Returns ~5-8 top world stories. CDATA titles need stripping. |
| BBC Business | `https://feeds.bbci.co.uk/news/business/rss.xml` | Economy | Good for market-moving stories, corporate news, and policy. |
| BBC Technology | `https://feeds.bbci.co.uk/news/technology/rss.xml` | Tech / Science | Mix of product news, regulation, and AI/security. |
| BBC US/Canada | `https://feeds.bbci.co.uk/news/us_and_canada/rss.xml` | US Policy | Returns US-focused political/economic stories. |

## Feeds That Failed / Are Rate-Limited

| Feed | URL | Failure Mode |
|---|---|---|
| Reuters | Various | `r.jina.ai` returned `SecurityCompromiseError: Anonymous access blocked... DDoS attack suspected`. Direct RSS fetch also unreliable due to anti-bot. |
| AP News | `https://apnews.com` | Same `r.jina.ai` block. |
| TechCrunch | `https://techcrunch.com` | Same `r.jina.ai` block. |
| The Guardian | `https://www.theguardian.com/world` | `r.jina.ai` timeout. |

## Verified Fetch Code

```python
import requests, xml.etree.ElementTree as ET

feeds = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
]

for name, url in feeds:
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        root = ET.fromstring(resp.text)
        items = root.iter('item')
        for item in items:
            title = item.find('title')
            desc = item.find('description')
            t = title.text if title is not None else ""
            if t.startswith('<![CDATA['):
                t = t[9:-3]
            print(f"  - {t}")
    except Exception as e:
        print(f"  FEED ERROR: {e}")
```

## Regional Fallback: Jina AI Reader for Paywalled Sites

**Tested: 2026-05-17**

The Jina AI Reader (`r.jina.ai/http://URL`) extracts clean markdown from paywalled/complex sites that don't expose RSS or block direct scraping. International news giants (Reuters, AP, TechCrunch, The Guardian) are **blocked** by Jina AI due to rate-limiting. However, **Australian regional news sites work reliably** and return clean article text.

### Australian Sites — VERIFIED Working via `r.jina.ai`

| Site | Category | Extraction Quality | Sample URL Pattern |
|------|----------|-------------------|-------------------|
| **SMH Technology** | Tech / Business | Excellent — clean markdown with headlines, author, summary | `r.jina.ai/http://www.smh.com.au/technology` |
| **ABC News** | General / Tech | Excellent — article cards with images, headlines, summaries | `r.jina.ai/http://www.abc.net.au/news/topic/technology` |
| **AFR Technology** | Business / Tech | Good — structured article list, paywall-resistant | `r.jina.ai/http://www.afr.com/technology` |
| **ZDNet Australia** | Tech | Good — trending lists, product reviews | `r.jina.ai/http://www.zdnet.com/au/` |
| **The Conversation AU** | Science / Analysis | Excellent — academic-quality articles | `r.jina.ai/http://theconversation.com/au/topics/technology-13` |

### How to Use

```python
import requests
url = "https://r.jina.ai/http://www.smh.com.au/technology"
resp = requests.get(url, timeout=30)
# resp.text is clean markdown with ![] images, ## headings, bullet lists
```

### Limitations
- Returns section/homepage text, not full article body (need per-article URL for full text)
- Rate-limit: ~5 requests/minute — pace requests with `time.sleep(3)` between calls
- If blocked, wait 60s or switch to direct RSS

### Comparison: Direct RSS vs `r.jina.ai` vs Browser

| Situation | Best Approach |
|-----------|--------------|
| BBC / Reuters | Direct RSS with Python `requests` + `xml.etree` |
| SMH / AFR / ABC News (no RSS) | `r.jina.ai` fallback |
| Complex multi-page, JavaScript-heavy | Browser automation (if available) |
| Known paywall | `r.jina.ai` (sometimes bypasses) |


