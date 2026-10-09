# IDX.co.id Scraping Reference

## Target
`https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/{KODE}`

## Protection
- Cloudflare WAF (bypassed by `ai-cloudscraper`)
- Nuxt.js SSR with compressed IIFE `__NUXT__` data
- Login wall for some pages (redirects to `/id/masuk`)

## Verified: AADI (PT Adaro Andalan Indonesia Tbk)

### Nuxt IIFE extraction
The `__NUXT__` data is NOT plain JSON — it's a compressed IIFE:
```html
<script>window.__NUXT__=(function(a,b,c,...){...})("USD",1,"RIBUAN",...);</script>
```

### Parsed data structure (278 values)
The positional args array contains all page data. Key indices:

| Index | Value | Meaning |
|-------|-------|---------|
| 0 | "USD" | Mata uang |
| 2 | "RIBUAN" | Satuan |
| 5 | "Aktif" | Status |
| 7 | "1911-01-01T00:00:00" | Tahun buku |
| 15 | "Rintis, Jumadi, Rianto & Rekan" | KAP (Auditor) |
| 37 | "DIREKTUR" | Role label |
| 38 | "Budi Bowoleksono" | Name |
| 45 | "AADI" | Kode saham |
| 46 | "contact@example.com" | Email |
| 47 | "PT Adaro Andalan Indonesia Tbk" | Nama perusahaan |
| 48 | "(021) 2553 3065" | Telepon |

### Shareholder data (indices ~140-160)
Values appear as [name, percentage, ...] pairs:
- PT Adaro Strategic Investments: 41.0965%
- Garibaldi Thohir: 5.8305%
- PT Alamtri Resources Indonesia Tbk: 15.3723%
- Afiliasi: 18.8154%

### Subsidiaries
~50+ PT Adaro* entities listed as string values. Also non-Adaro subsidiaries like PT Indonesia Bulk Terminal, PT Kaltara Power Indonesia, etc.

### Directors & Commissioners
Role labels and names are adjacent in the array. Roles: DIREKTUR UTAMA, DIREKTUR, KOMISARIS UTAMA, KOMISARIS, KETUA, ANGGOTA.

## Financial Reports via API

### Endpoint
`https://www.idx.co.id/primary/ListedCompany/GetFinancialReport`

### Parameters
- `length` — page size (ignored, always returns 10)
- `start` — page offset (BROKEN — always returns same 10 results)
- `ReportType` — "Audit" (only type that returns data)
- `Year` — 2018 through 2024 have data
- `Periode` — "Tahunan" (only period that returns data)
- `search[value]` — searches company names (doesn't filter ticker codes, ignored entirely in practice)

### Known bug: Pagination is broken
The `start` parameter is completely ignored — the Varnish cache returns the same first 10 results (AADI→ADMR) regardless of page. The API correctly reports `ResultCount` (835 for 2024) but you cannot access pages beyond the first 10.

Result: only ~27 tickers alphabetically (AADI through ADMR) have downloadable reports via this API. 935/962 tickers are inaccessible through this endpoint.

### Downloadable report types
| Year | Count | Types |
|------|-------|-------|
| 2024 | 835 | Annual, ESG |
| 2023 | 921 | Annual |
| 2022 | 870 | Annual |
| 2021 | 559 | Annual |
| 2020 | 64 | Annual |
| 2019 | 643 | Annual |
| 2018 | 620 | Annual |

### URL patterns
**New format (2021+, hash-based):**
`https://www.idx.co.id/Portals/0/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/From_EREP/{yyyymm}/{hash}.pdf`

The hash is unpredictable — only discoverable via the API.

**Old format (pre-2021, predictable):**
`https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/Corporate_Actions/New_Info_JSX/Jenis_Informasi/01_Laporan_Keuangan/04_Annual Report/{year}/{ticker}/{ticker}_Annual Report_{year}.pdf`

This old pattern works for some tickers (BBRI 2020 confirmed, BBCA 2020 confirmed).

### Python extraction
```python
import cloudscraper, json

scraper = cloudscraper.create_scraper()
resp = scraper.get(
    "https://www.idx.co.id/primary/ListedCompany/GetFinancialReport",
    params={"length": 10, "start": 0, "ReportType": "Audit", "Year": "2024", "Periode": "Tahunan"},
    headers={
        "Accept": "application/json",
        "Referer": "https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/BBRI",
        "X-Requested-With": "XMLHttpRequest"
    },
    timeout=15
)
data = resp.json()
for r in data.get('Results', []):
    kode = r['KodeEmiten']
    for a in r.get('Attachments', []):
        url = f"https://www.idx.co.id{a['File_Path']}"
        # Download: scraper.get(url)
```

### Broken alternative endpoints
All tested and returning 503 or 0 results:
- `GetAnnouncement`
- `GetCorporateAction`
- `GetStockListing`
- `GetFinancialReportData`
- `GetReportList`
- POST method returns 405

### Other tabs on the profile page
The profile page (`perusahaan-tercatat/profil-perusahaan-tercatat/{KODE}`) has 8 tabs:
1. Profile (Profil) — data embedded in `__NUXT__`
2. Dividend (Dividen)
3. Stock Listing (Pencatatan Saham)
4. Announcement (Pengumuman)
5. Trading Information (Info Perdagangan)
6. Calendar (Kalender)
7. Financial Report (Laporan Keuangan)
```python
import cloudscraper, re

scraper = cloudscraper.create_scraper()
resp = scraper.get(f'https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/{kode}', timeout=30)
raw = resp.text

# Check for login redirect
if '/id/masuk' in raw[:2000]:
    print("Login required")
    return

# Extract __NUXT__ IIFE args
start = raw.find('window.__NUXT__=')
end = raw.find('</script>', start)
script = raw[start:end]

last_brace = script.rfind('}')
after_brace = script[last_brace+1:].strip()

if after_brace.startswith('('):
    depth = 0
    for i, c in enumerate(after_brace):
        if c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                args = after_brace[1:i]
                break
    
    # Manual split on top-level commas
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

## Notes
- Page is Nuxt SSR — data is embedded server-side, no browser rendering needed
- Some pages (like AADI) return full data without login; others may redirect
- Rate limit: add `time.sleep(1)` between requests
- The `__NUXT__` function body itself is ~40KB of minified JS; only the args array (~4.5KB) contains the actual data
