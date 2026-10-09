---
name: japan-transit
description: "Use for Japanese train schedule lookups (jadwal kereta)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Japan, transit, train, schedule, Yahoo, JR]
---

# Japan Transit — Train Schedule Lookups

Find Japanese train schedules (departure/arrival times, duration, fare) with
plain `curl` — no API key, no browser. Yahoo Transit serves full HTML to a
plain curl request with a browser UA.

## When to Use

- "Jam berapa ada kereta X ke Y" / "what time is the train from X to Y"
- Any Japanese station-to-station schedule question (JR, private lines, subways)
- Trip planning around festivals/events (e.g. Tohoku Bon Odori)

## Method

### 1. Build the Yahoo Transit URL

```
https://transit.yahoo.co.jp/search/result?from=<STATION1>&to=<STATION2>&y=YYYY&m=MM&d=DD&hh=HH&m1=0&m2=0&type=depart&t=1&exp=1&q=
```

- `from`/`to` = URL-encoded Japanese station names (e.g. 秋田 = `%E7%A7%8B%E7%94%B0`, 横手 = `%E6%A8%AA%E6%89%8B`)
- `hh` = departure hour (0-23); `type=depart` = search by departure time
- `t=1` = sort by departure time; `exp=1` = include express options
- Query 3 windows (morning ~06, noon ~12, evening ~18) to cover the full day

```bash
curl -sL "https://transit.yahoo.co.jp/search/result?from=%E7%A7%8B%E7%94%B0&to=%E6%A8%AA%E6%89%8B&y=2026&m=8&d=16&hh=18&m1=0&m2=0&type=depart&t=1&exp=1&q=" \
  -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
  -o /tmp/yahoo_transit.html
```

### 2. Parse the results

Use `scripts/parse_yahoo_transit.py` (in this skill) — it extracts each route's
departure/arrival times, stations, and line names from the saved HTML:

```bash
python3 ~/.hermes/skills/travel/japan-transit/scripts/parse_yahoo_transit.py /tmp/yahoo_transit.html
```

Output format: `Route N: HH:MM -> HH:MM | StationA -> StationB` plus line names.

### 3. Report

Answer in the user's language (Indonesian user → Indonesian). Give the full
day's departures grouped by time of day (pagi/siang/sore-malam), with arrival
times. Note the travel duration (~1h20m for Akita→Yokote) and offer to check
connecting lines (e.g. Yokote → Nishimonai Onsen via Yuri Kogen Line).

## Pitfalls

- **Jorudan (jorudan.co.jp) redirects** to a UUID interstitial
  (`jid.jorudan.co.jp/jrd_uuid/`) — curl can't follow it to results. Don't use it.
- **Google/Bing search engines return junk for JP queries** — "Akita to Yokote
  train" surfaces the Akita dog breed, not trains. Go straight to Yahoo Transit.
- **Browser tools may be unavailable** on this VPS (Chrome fallback fails) —
  curl + parse is the reliable path.
- **Station names must be Japanese, URL-encoded.** English names won't match.
  Use the kanji (秋田, 横手, 東京, etc.).
- **The wrapper Gmail/other API skills don't help here** — this is pure web
  scraping, no auth needed.

## Verification

- Response contains `routeDetail` blocks → parse succeeded.
- If the page contains `error` or no `routeDetail`, the station names are wrong
  or the date is invalid — re-check the kanji encoding.
