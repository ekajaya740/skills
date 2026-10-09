# Investment Vault → D1 — real session notes (2026-08-19)

> **Historical (pre-Notion, 2026-08-19).** `~/investment-vault` is a *separate, still-live* repo — it is
> **not** the personal second brain. Its local `qmd` index is retired (the personal knowledge store moved
> to Notion, `notion-second-brain`); the "QMD index" figures below are a size record from that session.

Source vault: `~/investment-vault` — 22,794 markdown files, 3.8GB
(2.1GB QMD index, 1.5GB Index/), 965 ticker dirs, 962 hub pages.
Git remote `ekajaya740/investment-vault` (push allowed — unlike `~/.hermes`).

## Schema tables (all UUID v7 PKs)

| Table | Source files | Count |
|---|---|---|
| sector_hierarchy | `Sektor/**/*.md` (355 notes) | 355 |
| tickers | `{TICKER}/{TICKER}.md` hub (962) | 962 |
| ticker_sectors | hub "Klasifikasi Sektor" 4 lines | 3799 |
| people / positions | `People/*.md` (8,798) + Management tables | 8817 / 11804 |
| shareholders | `Shareholders/2024-shareholders.md` | 8775 |
| dividends | `Dividends/2024-dividends.md` | 631 (600 tickers) |
| audits | `Audit/2024-audit.md` | 533 (skip year=0 junk rows) |
| subsidiaries | `Subsidiaries/index.md` | 5406 |
| corporate_logs | `Logs/index.md` | 0 (all "No entries yet") |
| stock_groups / _members | user-defined | empty |
| reports_meta | Financial-Reports/Annual+TW | 3997 |
| reports_chunks | bodies ≤60KB | 25882 |
| reports_fts | FTS5 one doc per chunk | 25882 |

Total DB size: 3.1GB (1.4GB body text + ~1.4GB FTS copy).

## Parsing rules learned from real files

- Hub frontmatter: `type: Ticker`, `ticker`, `name`, `board` (Utama/Pengembangan),
  `sector`, `listing_date` (39 files malformed → NULL), `source`.
- Hub body sections: `## Klasifikasi Sektor` (4 `**Sektor:** [name](url)` lines),
  `## Kontak` (Address/Phone/Email/Website/NPWP), `## Pencatatan Saham`
  (Shares Outstanding, dots stripped), `## Bidang Usaha` (plain text).
- Sektor tree: notes named `{dirbasename}.md` — parent formula:
  level2 → `d0/d0`; level>2 → `join(d[:-2]) + "/" + d[-3]`. Orphans=0 after fix.
- Management: 4 sections ×962 — `Board of Directors` (Name|Title),
  `Board of Commissioners` (Name|Title|Independent), `Corporate Secretary`
  (Name|Phone|Email), `Audit Committee` (Name|Position, 953/962).
- Audit table is `Firm | Year | Signing Partner` — rows with year `0` are junk
  (missing data) and must be skipped; all `signing_partner` empty in source.
- Report filenames: `{year}-{type}-{rest}.md` where type ∈ {Annual, TW}.
  Files like `2026-Annual-3b4740d902_e213cfc609.md` = duplicate with hash
  suffix (41 files, 27.8MB) — keep only canonical. Strip duplicated
  `TW-` prefix in title (e.g. `TW-TW-FinancialStatement` → `FinancialStatement`).
- Bare `{year}-TW.md` / `{year}-Annual.md` files exist (630) — generic
  "empty-ish" reports; still import.

## D1 limits reality check (Apr 2026 docs)

- Free 500MB/DB, Paid 10GB/DB, storage per account 1TB paid.
- Max row 2MB; max statement 100KB; 100 bound params; FTS5 supported
  (export skips virtual tables — delete FTS before export, recreate after).
- Paid cost: $5/mo Workers Paid + ~$1.10/GB/mo D1 storage (+writes/reads).

## Cloudflare API token (non-destructive)

- Dashboard → My Profile → API Tokens → Create Custom Token.
- Permissions: Account → D1 → Edit; Account → Workers Scripts → Edit
  (optionally Account Settings → Read). No Zone/R2/Billing grants needed.
- Use `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` env for wrangler.
- Revoke after setup — Worker URL needs no token.

## Build timing

- ~6–7 min for 22K files on VPS (single-threaded python).
- UUID generation adds overhead; run long builds with
  `terminal(background=true, notify_on_complete=true)`.

## MCP tool list (17)

get_ticker_profile, get_management, get_shareholders, get_dividends,
get_audit, get_subsidiaries, get_sector_tickers, list_reports, read_report,
search_reports, list_stock_groups, create_stock_group, add_stock_to_group,
get_stock_group, r2_list_files, r2_get_file, r2_put_file.
