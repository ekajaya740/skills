---
name: idx-company-profile-scraper
description: "Scrape IDX company profiles via ai-cloudscraper."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [idx, stock, indonesia, cloudflare, scraping, nuxt]
    related_skills: [spa-data-extraction]
---

# IDX Company Profile Scraper

Use this skill when you need to scrape company profile data from `https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/<KODE_SAHAM>` — the page is protected by Cloudflare WAF and uses Nuxt.js SSR with compressed `__NUXT__` data.

## Prerequisites

```bash
pip3 install git+https://github.com/zinzied/ai-cloudscraper.git
```

## Workflow

### Step 1: Fetch the page

```python
import cloudscraper

scraper = cloudscraper.create_scraper()
resp = scraper.get(f'https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/{kode_saham}', timeout=30)
raw = resp.text
```

### Step 2: Extract the compressed __NUXT__ data

The page embeds data as an IIFE: `window.__NUXT__=(function(a,b,...){...}(arg1,arg2,...));`

```python
import re, json

start = raw.find('window.__NUXT__=')
end = raw.find('</script>', start)
script = raw[start:end]

# Find the args after the last function body brace
last_brace = script.rfind('}')
after_brace = script[last_brace+1:].strip()

if after_brace.startswith('('):
    depth = 0
    args_end = -1
    for i, c in enumerate(after_brace):
        if c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                args_end = i
                break
    
    args_content = after_brace[1:args_end]
    
    # Parse as JSON array (handle Nuxt encoding)
    json_str = '[' + args_content + ']'
    json_str = json_str.replace('\\u002F', '/')
    json_str = json_str.replace('\\u0026', '&')
    json_str = json_str.replace('\\r\\n', '\\n')
    
    data = json.loads(json_str)
```

### Step 3: Manual parse (if JSON fails due to Nuxt compression)

The compressed format may not parse as valid JSON directly. Use a manual top-level comma split:

```python
values = []
depth = 0
in_str = False
current = ''
for c in args_content:
    if c == '"' and (not current or current[-1] != '\\'):
        in_str = not in_str
        current += c
    elif not in_str:
        if c in '({[':
            depth += 1
            current += c
        elif c in ')}]':
            depth -= 1
            current += c
        elif c == ',' and depth == 0:
            values.append(current.strip())
            current = ''
        else:
            current += c
    else:
        current += c
if current.strip():
    values.append(current.strip())
```

### Step 4: Extract known fields

The data is positional. Key indices (for AADI as reference — may vary per company):

| Index | Field |
|-------|-------|
| 0 | Mata Uang (e.g. "USD") |
| 2 | Satuan (e.g. "RIBUAN") |
| 5 | Status ("Aktif") |
| 7 | Tahun Buku |
| 45 | Kode Saham |
| 46 | Email |
| 47 | Nama Perusahaan |
| 48 | Telepon |
| 49+ | Nama-nama direksi/komisaris |
| varies | Alamat (contains "Cyber 2 Tower" or similar) |
| varies | Sektor, Subsektor, Industri, Subindustri |
| varies | NPWP |
| varies | Tanggal Pencatatan |
| varies | Website |
| varies | Pemegang Saham (search by name) |

Scan for known strings to extract structured data:

```python
for i, v in enumerate(values):
    v_clean = v.strip('"')
    if v_clean == kode_saham:
        print(f"Kode Saham: {v_clean}")
    elif 'corsec@' in v_clean:
        print(f"Email: {v_clean}")
    elif 'Cyber 2 Tower' in v_clean or 'Jl.' in v_clean:
        print(f"Alamat: {v_clean.replace(chr(92)+'n', chr(10))}")
    elif v_clean in ['Energi', 'Keuangan', 'Consumer']:
        print(f"Sektor: {v_clean}")
    # ... etc
```

## Data Fields Available

- **Identitas**: Kode Saham, Nama Perusahaan, Status, Papan, NPWP
- **Kontak**: Alamat, Telepon, Fax, Email, Website
- **Klasifikasi**: Sektor, Subsektor, Industri, Subindustri
- **Pencatatan**: Tanggal Pencatatan, Mata Uang, Satuan, Tahun Buku
- **Manajemen**: Direksi (DIREKTUR UTAMA, DIREKTUR), Komisaris (KOMISARIS UTAMA, KOMISARIS, KETUA, ANGGOTA)
- **Pemegang Saham**: Nama + persentase kepemilikan
- **Anak Perusahaan**: Daftar entitas anak (PT ...)
- **Bidang Usaha**: Deskripsi kegiatan usaha
- **KAP**: Kantor Akuntan Publik

## Pitfalls

- **Nuxt compressed format** — the `__NUXT__` data is encoded as a function with minified variable names. Standard JSON parsing may fail; use the manual split approach.
- **Positional data** — field positions vary between companies. Always scan by known string values rather than hardcoding indices.
- **Login wall** — some pages redirect to login. The scraper handles this but data will be limited.
- **Rate limiting** — IDX may throttle. Add `time.sleep(0.5)` between requests.
- **Unicode escapes** — `\\u002F` = `/`, `\\u0026` = `&`, `\\r\\n` = newline. Always decode these.
- **ai-cloudscraper dependency** — requires the `ai-cloudscraper` package from GitHub, not PyPI's `cloudscraper`.

## Example

```python
import cloudscraper, re

scraper = cloudscraper.create_scraper()
resp = scraper.get('https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/AADI', timeout=30)
raw = resp.text

# Extract and parse __NUXT__ data (see Step 2-3 above)
# Then scan for fields (see Step 4)
```
