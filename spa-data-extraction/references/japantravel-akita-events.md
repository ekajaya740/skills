# JapanTravel Akita Events — Real-world SPA extraction example

**Target:** `https://en.japantravel.com/events/akita`
**Date extracted:** June 16, 2026

## API endpoint discovered

From the Inertia.js SSR state, the route definition was:

```
events.prefecture
  uri: "events/{prefecture}"
  wheres: { prefecture: "hokkaido|aomori|...|akita|..." }
```

Pagination links in the SSR state revealed:

```
https://api.japantravel.com/api/articles?page=1
```

The AJAX endpoint used `prefecture=5` (Akita's numeric ID).

## Query pattern

```bash
curl -s 'https://api.japantravel.com/api/articles?page=N&prefecture=5' \
  -H 'Accept: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Referer: https://en.japantravel.com/events/akita'
```

Total: 23 pages of 20 items each. Filtered by `item.type == "event"` and `item.lang == "en"`.

## Data fields in list API response

Each list item had `type: "event"` with:
- `id`, `title`, `slug`, `url` — identifiers
- `event_date.start`, `event_date.end` — ISO datetime strings
- `event_free`, `event_general_price` — pricing info
- `description` — **truncated** to ~150 chars (card-grid preview length)
- `event_date.unknown_start_time`, `event_date.unknown_end_time` — time awareness
- `city`, `prefecture` — location (list-level lat/lng is prefecture-centroid, not event-specific)

**Missing from list API:** venue name, full address, specific lat/lng, directions, Japanese name, website URL, full content.

## Description truncation — the key trap

The `description` field in the list response is ~150 characters — just enough for a card preview. The full multi-paragraph content (500–2000 chars) plus access directions live only on the detail page's Inertia.js state under:

- `article.content` — full HTML content (strip tags with `re.sub(r'<[^>]+>', '', text)`)
- `article.directions` — HTML directions content (strip tags same way)
- `article.subtitle` — subtitle/headline

## Enrichment from detail pages

Each event's individual URL (from `item.url`) is also SSR'd with Inertia.js. The `data-page` JSON contained:

```python
m = re.search(r'data-page="({.*?})"\s*>', raw, re.DOTALL)
json_str = html.unescape(m.group(1))
data = json.loads(json_str)
article = data.get('props', {}).get('article', {}) or data.get('article', {})
```

Key fields on the detail page:

| Field | Where | Purpose |
|-------|-------|---------|
| `article.event_venue` | detail only | Venue name |
| `article.address_en` | detail only | Full postal address |
| `article.event_name_ja` | detail only | Japanese name |
| `article.location.lat/lng` | detail only | Precise coordinates |
| `article.directions` | detail only | Access instructions (HTML) |
| `article.content` | detail only | Full event description (HTML) |
| `article.subtitle` | detail only | Short headline |
| `article.disclaimer` | detail only | Date-not-confirmed warnings |
| `article.website` | detail only | Official event URL |

## Downstream: Google Calendar insertion with reminders

After extracting and enriching all events, insert into Google Calendar. The `gws` CLI often fails with stale token cache (keyring decryption issues). Direct REST API workflow:

```python
# 1. Refresh token via OAuth2 endpoint
import requests
resp = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'refresh_token': creds['refresh_token'],
    'grant_type': 'refresh_token',
})
access_token = resp.json()['access_token']

# 2. Insert events
headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
for ev in events:
    requests.post(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
        headers=headers, json=ev
    )

# 3. Update events (patch reminders or description)
reminders = {
    'useDefault': False,
    'overrides': [
        {'method': 'popup', 'minutes': 40320},  # 28 days (Google's max for 1 month)
        {'method': 'popup', 'minutes': 10080},   # 1 week
        {'method': 'popup', 'minutes': 1440},    # 1 day
    ]
}
requests.patch(f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{cal_id}',
    headers=headers, json={'reminders': reminders, 'description': full_desc, 'location': full_addr})
```

### Event date/time -> Calendar format rules

| List API `event_date` | Calendar `start`/`end` format |
|------------------------|-------------------------------|
| `unknown_start_time: true` + `unknown_end_time: true` | `{"date": "2026-08-15"}` (all-day) |
| Specific times like `17:10:00`–`21:30:00` | `{"dateTime": "2026-08-29T17:10:00+09:00", "timeZone": "Asia/Tokyo"}` |
| Multi-day with no times (`00:00:00`) | `{"date": "2026-09-13"}` / `{"date": "2026-09-15"}` (end = day after last day) |
| Specific hour range across days | `{"dateTime": "2026-09-26T10:00:00+09:00"}` / `{"dateTime": "2026-09-27T15:00:00+09:00"}` |

## Extracted events (2026, from June 16 onward)

| Event | Dates | Venue | Price |
|-------|-------|-------|-------|
| Sand Craft in Mitane | Jul 25 – Aug 31 | Kamayahama Beach, Mitane | ¥500 |
| Noshiro Tanabata 能代七夕 | Aug 2–3 | Noshiro City area | Free |
| Akita Kanto Festival 秋田竿燈まつり | Aug 3–6 | Chuo-dori, Akita City | — |
| Yokote Okuribon Festival 送り盆まつり | Aug 15–16 | Ja-no-saki Bridge, Yokote | Free |
| Omagari Hanabi 大曲の花火 | Aug 29 17:10–21:30 | Omono Riverside Park, Daisen | — |
| Yashima Hassaku Festival 矢島八朔まつり | Sep 13–14 | Yashima Shinmeisha Shrine, Yurihonjo | Free |
| Yokote Yakisoba Festival 横手やきそばフェスティバル | Sep 26–27 10:00–15:00 | Akita Furusato Village, Yokote | ¥2,000 |
| Odate Kiritanpo Festival 本場大館きりたんぽまつり | Oct 11–12 | Nipro Hachiko Dome, Odate | — |
| Yokote Chrysanthemum Festival よこて菊まつり | Oct 30 – Nov 10 | Akita Furusato Village, Yokote | Free |

## Non-English duplicates

The same event appeared in multiple languages (English, German, Italian, Korean, Vietnamese, Russian, Thai, French). All shared the same `id` across languages (linked via `translations` or `alternate` hreflang tags). Deduplicate by checking `lang == "en"` or by tracking `id` across pages.