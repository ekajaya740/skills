# shadcn/ui + TanStack Table in the Worker-SPA (2026-08-21)

User asked: "use shadcn as the UI. please use tanstack table too" on top of
the single-app Elysia worker (see `elysia-aot-false-single-app.md`).

## Setup that worked

```bash
bun add tailwindcss @tailwindcss/vite @tanstack/react-table@^8.21.0 \
  class-variance-authority clsx tailwind-merge lucide-react \
  @radix-ui/react-slot @radix-ui/react-dropdown-menu
```

- **Tailwind v4** — vite plugin `@tailwindcss/vite`, CSS entry
  `@import "tailwindcss"` + `@custom-variant dark (&:is(.dark *))` +
  `@theme inline` mapping `--color-*` vars. NO `tailwind.config.js`, no
  PostCSS config, no `@tailwindcss/postcss`.
- **TanStack Table v8 pin is mandatory** — v9 (current `latest`) is a full
  API rewrite (hooks renamed, no `useReactTable`/`flexRender`). The shadcn
  data-table docs/ecosystem is v8-only. `bun add @tanstack/react-table@^8.21.0`
  explicitly. v9 was installed first by mistake (`bun add` without version)
  and had to be downgraded.
- **shadcn components are hand-rolled** — `shadcn init` isn't scripted here;
  copy the standard component files into `src/client/components/ui/` (button,
  card, input, badge, table, dropdown-menu) and add `components.json` +
  `@/lib/utils.ts` (cn). The new-york style variants work as-is.
- **Aliases**: `components.json` `@/*` → `./src/client/*`; wire BOTH
  `tsconfig.json` `paths` AND vite `resolve.alias` (`"@"` → absolute path of
  `src/client`). Missing vite alias = dev/build module-not-found; missing
  tsconfig paths = tsc errors on `@/` imports.

## DataTable component (reusable)

shadcn data-table pattern verbatim: `useReactTable` with
`getCoreRowModel/getPaginationRowModel/getSortedRowModel/getFilteredRowModel`,
state: sorting / columnFilters / columnVisibility / rowSelection.
Sortable headers via `Button variant="ghost" size="sm"` +
`column.toggleSorting(column.getIsSorted() === "asc")`; filter via
`table.getColumn(searchColumn)?.setFilterValue(...)`; column visibility
toggle via DropdownMenuCheckboxItem. Pagination buttons use
`table.getCanPreviousPage()/nextPage()`.

## Dark mode with class strategy

- `index.html` gets `class="dark"` on `<html>` + inline anti-flash script
  that removes it when `localStorage.theme === "light"`.
- Toggle button does `document.documentElement.classList.toggle('dark', next==='dark')`
  + writes localStorage. React state starts `'dark'`.
- The old CSS-var `data-theme` approach is replaced by Tailwind `.dark`
  class; `pre.note` styling moved into the Tailwind CSS file.

## Pitfalls

- **CSS bundling**: import the stylesheet in `main.tsx`
  (`import "./styles/app.css"`), NOT a `<link href="/styles/app.css">` in
  index.html — the file isn't in `public/` so the bare link 404s. Vite
  bundles the import into `dist/client/assets/*.css`.
- **Do NOT render `<script>` inside React components** (theme bootstrap) —
  it does nothing. Inline scripts belong in `index.html` `<head>`.
- **fetch typing**: every `fetch(...).then(r => r.json())` needs
  `as Promise<{data: T}>` (or `{data?: T; error?: string}` for detail
  pages) or tsc errors `'d' is of type 'unknown'`.
- **Elysia async handlers** (from the merge round, still biting): route
  callbacks returning a Promise must be `async`/`await`ed — a sync arrow
  returning a promise serializes as `{"data":{}}`.
- **Visual verification on this VPS**: Playwright Chromium download fails
  (`Unknown system error -122` — CDN write error, retried twice, also raw
  curl of the zip fails). Browser_exec also fails with "chrome-not-running".
  Verify UI via build + `wrangler dev --remote` + curl asset/SPA checks
  instead; the `web-screenshot-capture` skill's lightpanda route is the only
  DOM-level check available. Do NOT record playwright as a dependency.

## Verification used

`bun run check-types` (tsc clean) → `bun run build:client` (vite, expect
Tailwind CSS ~25KB + JS ~400KB) → `wrangler dev --remote` → curl:
`/` (200 html), `/companies/BBRI` (200 html SPA fallback), new hashed
`/assets/*.css` + `/assets/*.js` (200), REST `/api/v1/stats` unchanged,
`/mcp` tools/list unchanged → `wrangler deploy` → repeat curl battery on
live URL. Deployed `8eccdd4a`, commit `b9daaf2`.
