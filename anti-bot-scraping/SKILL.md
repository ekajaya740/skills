---
name: anti-bot-scraping
description: "Bypass Cloudflare WAF with cloudscraper. Token-efficient."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [web-scraping, cloudflare, anti-bot, waf-bypass, scraping]
    related_skills: [spa-data-extraction]
---

# Anti-Bot Scraping

Use this skill when a target website is protected by Cloudflare WAF, Cloudflare Challenge (5秒盾), or similar anti-bot protections that block plain `curl` or `requests`.

## Tool ranking (token efficiency)

| Tool | Approach | Token Cost | Best For |
|------|----------|-----------|----------|
| **cloudscraper** / **ai-cloudscraper** | Python requests wrapper — mimics TLS fingerprint + solves JS challenge | 1 call, minimal output | REST API scraping, SSR pages |
| **curl-impersonate** | curl with real browser TLS fingerprint | 1 call, minimal output | API calls without JS challenge |
| **FlareSolverr** | Proxy service — solves challenge, returns cookies | 2 calls (solve → reuse cookies) | Integration with existing scrapers |
| **undetected-chromedriver** | Selenium patch — bypasses bot detection | 3+ calls, heavy output | SPA / JS-heavy pages |
| **Playwright + stealth** | Browser automation, more stealth than Selenium | 3+ calls, heaviest output | Sites with aggressive anti-bot |

**Always try cloudscraper first** — it's the most token-efficient option.

## Installation

```bash
# Standard cloudscraper
pip3 install cloudscraper

# ai-cloudscraper (zinzied fork — more aggressive bypass, handles more sites)
pip3 install git+https://github.com/zinzied/ai-cloudscraper.git
```

## Basic usage

```python
import cloudscraper

scraper = cloudscraper.create_scraper()
resp = scraper.get('https://target-site.com/page', timeout=30)

if resp.status_code == 200 and 'cloudflare' not in resp.text.lower()[:2000]:
    print('Bypassed successfully')
else:
    print('Still blocked — try ai-cloudscraper or browser approach')
```

## When cloudscraper isn't enough

Cloudscraper handles **JS challenge** (the 5-second wait) and **TLS fingerprinting**. It does NOT handle:
- CAPTCHA challenges (reCAPTCHA, hCaptcha)
- Browser fingerprinting (WebGL, canvas, fonts)
- Rate limiting (add `time.sleep()` between requests)
- Login-gated content

For those, escalate to:
- **undetected-chromedriver** for Selenium-based sites
- **Playwright + playwright-stealth** for modern anti-bot
- **Browser tools** (Hermes browser_navigate) for one-off interactive scraping

## Post-bypass: extracting data from SSR frameworks

Once cloudscraper gets the HTML, the page may use an SSR framework that embeds data. See the `spa-data-extraction` skill for standard patterns (Inertia.js `data-page`, Next.js `__NEXT_DATA__`, Nuxt `__NUXT__`).

### Nuxt compressed IIFE format

Some Nuxt sites (e.g. IDX.co.id) encode `__NUXT__` data as a **compressed IIFE function** rather than plain JSON:

```html
<script>window.__NUXT__=(function(a,b,c,...){...})("value1",1,"value2",...);</script>
```

The data is passed as positional arguments to the function. To extract it:

```python
import re, json

# Extract the argument list (everything between the last } and the final );)
script = raw  # the full script content
last_brace = script.rfind('}')
after_brace = script[last_brace+1:].strip()

if after_brace.startswith('('):
    # Find matching closing paren
    depth = 0
    for i, c in enumerate(after_brace):
        if c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                args = after_brace[1:i]
                break
    
    # Parse as JSON array (handle unicode escapes)
    json_str = '[' + args + ']'
    json_str = json_str.replace('\\u002F', '/')
    json_str = json_str.replace('\\u0026', '&')
    
    # Manual split on top-level commas (values may contain nested objects)
    values = []
    depth = 0
    in_str = False
    current = ''
    for c in args:
        if c == '"' and (not current or current[-1] != '\\'):
            in_str = not in_str
            current += c
        elif not in_str:
            if c in '({[': depth += 1; current += c
            elif c in ')}]': depth -= 1; current += c
            elif c == ',' and depth == 0:
                values.append(current.strip())
                current = ''
            else: current += c
        else: current += c
    if current.strip(): values.append(current.strip())
```

## Pitfalls

- **Dependency conflicts** — `ai-cloudscraper` may upgrade `cryptography` past what Hermes expects. This is usually harmless for scraping but may produce pip warnings.
- **Login walls** — cloudscraper doesn't handle auth. If the page redirects to login, you need session cookies first.
- **Rate limiting** — IDX and many Indonesian sites are aggressive. Add `time.sleep(1)` between requests.
- **Nuxt IIFE vs JSON** — always check if `__NUXT__` is plain JSON or a function call. The function call format requires manual parsing (see above).
- **Unicode escapes** — Nuxt IIFE args use `\\u002F` for `/` and `\\u0026` for `&`. Replace before parsing.
