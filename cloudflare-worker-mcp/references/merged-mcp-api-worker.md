# Merged MCP+API Worker & Dashboard Round (2026-08-20)

Validated live: `investment-vault-api` serves BOTH `/mcp` (17 MCP tools,
Streamable HTTP) and `/api/v1` (REST JSON) from ONE Worker. The separate
`apps/mcp` worker was deleted.

## Why merge

MCP became stateless (no DO session store) → the only reason to split workers
vanished. MCP and REST shared identical bindings (D1/KV/R2), same `Env` type,
same vanilla-fetch transport. Merging = one deploy, one config, one URL.

## The merged skeleton

```
apps/api/src/index.ts   → fetch(): if pathname === "/mcp" → handleMcp(request, env)
                          else GET /api/v1/*  (REST handlers)
apps/api/src/mcp.ts      → tool registry (valibot → toJsonSchema), 17 tools,
                          handleMcp() = fresh Server + stateless transport per request
```

`handleMcp` keeps its own `let currentEnv` — set per-request, same pattern as
REST handlers. Bump server version (0.1.0 → 0.2.0) when merging; tools list
probes (`tools/list`) confirm deployment.

## R2 cleanup pattern

```bash
npx wrangler r2 object delete investment-vault/notes/<key>.md --remote -y
```

- Syntax: positional `{bucket}/{key}` — `--bucket` flag does NOT exist.
- No `list` subcommand in wrangler; enumerate keys via the MCP tool
  (`tools/call list_notes`) or the worker's R2 `list()`.
- Verified: after deleting all `notes/*`, `list_notes` returns `[]`; D1 table
  `notes` and the vault markdown remain untouched (source of truth).

## Hermes wiring of a remote MCP server

`hermes mcp add <name> --url https://...workers.dev/mcp` is INTERACTIVE:
- asks "Does this server require authentication?" → n
- asks "Enable all N tools?" → Y
- `echo n |` does NOT work (prompt reads TTY). Use `terminal(pty=true,
  background=true)` and answer via `process submit`.
- Result: config.yaml `mcp_servers.<name>: {url, enabled: true}` + enabled
  tools; tool names appear only in a NEW session (no hot reload).

## Tanstack Start dashboard pitfalls (companies/$ticker never rendered)

1. **Parent route must render `<Outlet />`** — `companies.tsx` / `notes.tsx`
   had no Outlet, so the child route `/companies/$ticker` never rendered;
   /companies/BBRI showed the 500-row list page. Fix: layout route renders
   `<Outlet />`, index route moves to `companies/index.tsx` with
   `createFileRoute('/companies/')`.
2. **`routeTree.gen.ts` is stale after moving routes** — regenerate by running
   `vite build` (the TanStack plugin rewrites it), then typecheck.
3. **react-start 1.168 entry files drift** from the template:
   - `StartClient` is NOT exported from `@tanstack/react-start` main — use
     `@tanstack/react-start/client`.
   - `StartClient()` takes NO props (`router` prop doesn't exist — router is
     provided via context).
   - `createStartHandler(getRouterManifest)` is wrong for this version; use
     `createStartHandler(defaultStreamHandler)` — router + manifest come from
     plugin virtual modules.
   - The entry files' `tsc` errors were pre-existing (build passed because
     vite doesn't typecheck) — fix the entry files, don't delete them.
4. **`env.DB.prepare(...).all()` returns `Record<string,unknown>[]`** — pass
   explicit type param `.all<T>()` on every query or the return type fails
   assignability to your typed arrays.
5. **dashboard tsconfig `types`**: including `@cloudflare/workers-types`
   without the dep in devDependencies breaks `tsc` — either add the dep or
   drop the entry.

## Dark mode (SSR + no-flash)

- CSS vars + `:root[data-theme="dark|light"]`; `color-scheme` per theme.
- Default DARK (user preference: "dark mode too. its important").
- Toggle button writes `data-theme` + `localStorage['theme']`.
- Anti-flash: inline `<script dangerouslySetInnerHTML>` in `<head>` sets
  `data-theme` before paint; `React.useState('dark')` initial matches.

## Project-restructure sweep that worked

- Deleted `apps/mcp`, `packages/repository`, `packages/service`,
  `packages/cache` (dead code — apps query D1 via raw SQL; schema lives in
  `packages/database`).
- `bun install` after workspace change (lockfile refresh).
- Root `check-types` script updated to drop deleted packages.
- Typecheck BEFORE deploy: `bun run check-types` (catches the D1 `.all<T>()`
  and entry-drift errors), then `bun run build`, then `npx wrangler deploy`.
