# Money Manager v2 session (2026-08-23): Hono + React SPA on one Worker, D1 double-entry

Second-generation rewrite of the legacy Astro+Hono app. User explicitly rejected
Astro mid-build ("i didnt expect it uses astro. i should be using just a plain
react with hono integration") and required TanStack Router. Final stack:

## Architecture (validated live)
ONE Worker (`money-manager-api`) serves both API and frontend via Cloudflare
Static Assets. No Pages, no CORS, first-party cookies.

```toml
# api/wrangler.toml
[assets]
directory = "../app/dist"
binding = "ASSETS"
not_found_handling = "single-page-application"
run_worker_first = ["/api/*"]        # Hono stays authoritative for /api/*
```

Frontend: Vite + React 19 + @tanstack/react-router + Tailwind 4
(`@tailwindcss/vite`). Dev mode: vite dev :4321 proxies `/api` → wrangler :8787.
API_BASE defaults to `''` (same-origin); never hardcode localhost into lib code.

## Google OAuth across multiple domains (the big pitfall)
App is reachable at custom domain AND workers.dev AND localhost. Any value
pinned in env/secrets (GOOGLE_REDIRECT_URI, APP_BASE_URL) breaks every other
domain: redirect_uri_mismatch at login, or post-login bounce to wrong origin →
cookie missing → stuck on /login loop.

Fix: derive BOTH redirect_uri and the post-login redirect base from the request:

```ts
function redirectUri(c: { req: Request; env: Env }): string {
  if (c.env.GOOGLE_REDIRECT_URI) return c.env.GOOGLE_REDIRECT_URI; // explicit override
  return `${new URL(c.req.url).origin}/api/v1/auth/callback`;
}
// callback: const base = new URL(c.req.raw.url).origin;
```
Deleted the pinning secrets afterwards (`wrangler secret delete`). Console needs
each domain's exact `/api/v1/auth/callback` URI (no trailing slash, no `/login`).
Prod cookie must be `Secure; SameSite=None`; localhost keeps `SameSite=Lax`.

## Drizzle + D1
- drizzle-kit 0.30 config: `dialect: 'sqlite'`, driver value is **'d1-http'**
  ('d1' fails Zod validation). dbCredentials: accountId/databaseId/token.
- Config must live in `api/` (resolves drizzle-kit from api/node_modules);
  root-level configs fail module resolution under bun workspaces.
- Empty migration dir needs hand-made `drizzle/meta/_journal.json`:
  `{"version":"7","dialect":"sqlite","entries":[]}`.
- Apply with `wrangler d1 migrations apply <db> --remote` (and --local for dev);
  set `migrations_dir = "../drizzle"` in wrangler.toml.

## Double-entry ledger (user requirement)
accounts (asset|liability|equity|income|expense; wallet=asset,
category=income/expense) + journal + journal_lines (debit/credit INTEGER minor
units). Engine validates sum(debit)=sum(debit) per currency before an atomic
D1 batch insert. Balances/reports computed by SUM, no stored balance column.
Equity account named 'Opening Balance' absorbs adjustments. Friendly endpoints
(/journal/income|expense|transfer) translate UI-speak into balanced lines.
Money helpers: toMinor/fromMinor per-currency decimals (IDR=0, USD=2) — unit
test these.

## MCP merged into the API worker (user insisted, twice)
Stateless per-request Server + WebStandardStreamableHTTPServerTransport at
/api/v1/mcp, auth via Bearer API key (SHA-256 hashed in D1, plaintext shown
once). Tools reuse the same ledger engine as REST. BYO-model path: attachments
exposed as MCP **resources** (`mm://attachments/<id>`, images as base64 blob)
so the calling client's vision reads receipts itself; server-side OCR
(receipt_ocr via Workers AI vision or any OpenAI-compatible endpoint through
VISION_PROVIDER/VISION_BASE_URL/VISION_API_KEY) documented only as fallback
for non-vision callers. PDFs sent as OpenAI-style `file` part with data URL.

## Frontend lessons
- shadcn@latest CLI (4.x) rejects older components.json shapes and its init/add
  prompts are brittle non-interactively; hand-writing radix primitives in
  src/components/ui/ (button/card/dialog/select/tabs/sheet/progress/badge/
  table/label/input/separator) with cn() is faster and fully controlled.
- iconify-icon web component via script tag in index.html; TSX typing requires
  declare module 'react' { namespace JSX { interface IntrinsicElements ... } }
  AND the global JSX augmentation.
- Stale API paths after versioning (/api/auth/login vs /api/v1/auth/login)
  caused a dead login button — unhandled promise rejection, no visible error.
  Always surface async errors in the UI and grep components when routes move.
