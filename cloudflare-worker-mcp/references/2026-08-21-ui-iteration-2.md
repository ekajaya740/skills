# UI iteration round 2: per-column filters, UTC dates, notes/R2 removal (2026-08-21)

Follow-up to `shadcn-tanstack-table-spa.md` — user corrections on the
investment worker SPA after the shadcn/TanStack round. Commit `586e0c7`.

## Per-column filters replace global search + column-visibility dropdown

User: "bikin filter buat setiap kolom di perusahaan" + "hapus dropdown select
buat disable kolom yg di view, ga guna".

The reusable `DataTable` now renders an `<Input placeholder="Filter…"
className="h-7 max-w-[180px] text-xs">` under EVERY header cell instead of a
single `searchColumn` search box. The column-visibility DropdownMenu
(DropdownMenuCheckboxItem) is deleted — do not re-add it.

Implementation notes:
- Header cell: `className="align-bottom"`, content wrapped in
  `<div className="space-y-1">` (label on top, filter input below).
- Filter wiring: `header.column.getCanFilter()` → render input bound to
  `header.column.getFilterValue()` / `header.column.setFilterValue(...)`.
- Table state drops `columnVisibility`/`rowSelection`; keeps `sorting` +
  `columnFilters`. `getFilteredRowModel()` still drives the row count.
- `searchColumn`/`searchPlaceholder` props removed from the component API;
  callers just pass `columns` + `data`.

## UTC timestamp normalization + dayjs

User: "normalisasi listingnya timenya dong pakai UTC timestamp. terus pakai
dayjs buat convert ke human time".

- D1 stores ISO dates WITHOUT timezone (`2024-12-05T00:00:00`). REST API
  normalizes before returning:
  ```ts
  function normalizeDate(v: unknown): string | null {
    if (typeof v !== "string" || !v) return null;
    const m = /^(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}:\d{2}))?/.exec(v);
    if (!m) return v;
    return `${m[1]}T${m[2] ?? "00:00:00"}.000Z`;
  }
  ```
  Applied in `listCompanies` (map over `results`) and `getCompany` (company
  row only — not the joined tables).
- Client: `bun add dayjs`; format with `dayjs(s).format("DD MMM YYYY")`
  ("05 Des 2024"). Never `s.slice(0, 10)` on raw DB strings.

## Notes tab + R2 removed

User: "hapus tab catatan dan jangan simpan catatan di r2".

- Deleted: Catatan nav link, `/notes` + `/notes/:path` routes, Notes.tsx,
  NoteDetail.tsx, "Catatan Riset" card in CompanyDetail.
- Deleted R2 `FILES` binding from wrangler.jsonc and `FILES: R2Bucket` from
  both Env types (api.ts + mcp.ts).
- Deleted MCP tools `list_notes` + `get_note` (both read R2) → MCP now 15
  tools. D1 `notes` table + `search_notes` tool remain.
- Verify: `wrangler deploy` output shows only `env.CACHE`, `env.DB`,
  `env.ASSETS` bindings; `tools/list` returns 15.

## Verification used

`bun run check-types` → `bun run build:client` (JS dropped 398→320 kB after
removing dropdown-menu + notes pages) → `wrangler deploy` → curl live:
`/api/v1/companies?limit=2` shows `listing_date: "2024-12-05T00:00:00.000Z"`,
`/api/v1/companies/BBRI` detail normalized, `/mcp` tools/list = 15 (no
list_notes/get_note), root + SPA route + new hashed assets all 200.
