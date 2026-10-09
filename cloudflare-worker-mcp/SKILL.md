---
name: cloudflare-worker-mcp
description: "Host MCP servers on Cloudflare Workers (D1, KV, R2, DO)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [cloudflare, workers, mcp, d1, kv, r2, durable-objects, elysia, drizzle, bun]
    related_skills: [building-mcp-servers, native-mcp, cloudflare-fullstack]
---

# Cloudflare Worker MCP Servers

Host Model Context Protocol (MCP) servers on Cloudflare Workers so Hermes (or
any MCP client) reaches them over Streamable HTTP — no local process, no R2
proxy machine. Data lives in **D1** (SQLite), cached in **KV**, large files in
**R2**, and MCP session state in a **Durable Object**.

## When to Use

- User wants an MCP server "hosted in the cloud" / accessible remotely
- Data source is (or becomes) a SQLite/D1 database, possibly huge (GBs)
- Stack involves Cloudflare bindings (D1/KV/R2/DO) behind an MCP endpoint
- Anything Elysia 2 + elysia-mcp + Drizzle on Workers

## Stack (validated 2026-08)

| Piece | Version / notes |
|---|---|
| Elysia | `2.0.0-beta.5` (npm tag `next`; `rc` tag is 1.2.x) |
| elysia-mcp | `0.1.1` — peer `elysia >=1.4.21`; use `--legacy-peer-deps` |
| Drizzle ORM | `1.0.0-rc.4` — import from `drizzle-orm/d1` |
| MCP SDK | `@modelcontextprotocol/sdk ^1.30` |
| zod | **v3** (`^3.25`), NOT v4 — v4 breaks MCP SDK tool-schema types |
| uuid | `^14` — has `v7` export (UUID v7 time-ordered PKs) |
| bun | via mise (`mise install bun@1.3.14 && mise use -g bun@1.3.14`) |
| wrangler | 4.x (`npx wrangler`) |

## Monorepo layout (bun workspaces — user preference)

```
d1/
├── package.json              # { "workspaces": ["packages/*"] }
├── scripts/build_d1.py       # ingestion pipeline (markdown → SQLite/D1)
└── packages/
    ├── db/                   # @investment-vault/db (shared)
    │   ├── src/schema.ts     # Drizzle schema
    │   └── migrations/       # 0001_xxx.sql (wrangler naming!)
    └── server/               # @investment-vault/server (the Worker)
        ├── src/index.ts      # Elysia + elysia-mcp
        └── wrangler.toml     # D1/KV/R2/DO bindings
```

- Root `package.json` workspaces + root scripts (`build`, `check`, `dev`,
  `deploy`) delegating with `bun run --cwd packages/server ...`.
- `packages/db` exports `./src/index.ts`; server imports `@investment-vault/db`
  (workspace:* dep). Path alias in server `tsconfig.json` → `../db/src/index.ts`.
- Migrations live in the **db package** at `packages/db/migrations/0001_*.sql`
  — wrangler requires `000N_*` numbering, applied via
  `npx wrangler d1 migrations apply <db> --remote`.

## wrangler.toml bindings

```toml
name = "investment-vault-d1"
main = "src/index.ts"
compatibility_date = "2026-08-19"
compatibility_flags = ["nodejs_compat"]

[[d1_databases]]
binding = "DB"
database_name = "investment-vault"
database_id = "<real id from `wrangler d1 create`>"

[[kv_namespaces]]
binding = "CACHE"
id = "<real id from `wrangler kv namespace create`>"

[[r2_buckets]]
binding = "FILES"
bucket_name = "investment-vault"

[[durable_objects.bindings]]
name = "MCP_SESSIONS"
class_name = "McpSessionStore"

[[migrations]]
tag = "v1"
new_sqlite_classes = ["McpSessionStore"]
```

## Worker skeleton (index.ts)

```ts
export type Env = { DB: D1Database; CACHE: KVNamespace; FILES: R2Bucket; MCP_SESSIONS: DurableObjectNamespace };
let currentEnv: Env | null = null;   // set per-request in fetch()

export default { fetch(request: Request, env: Env) { currentEnv = env; return app.fetch(request); } };
```

Key patterns (each one is a pitfall if missed):
- **Elysia 2 handler**: `app.fetch(request)` returns a Response — pass the
  Worker fetch directly.
- **Durable Object `implements` not `extends`**: `class McpSessionStore implements DurableObject` with `constructor(state: DurableObjectState)`. `extends DurableObject` fails TS ("Cannot extend an interface").
- **Lazy env access**: any `new DoEventStore(currentEnv!...)` at module scope
  runs BEFORE the env binding is set. Pass factories: `new DoEventStore(() => currentEnv!.MCP_SESSIONS)`.
- **KV cache**: wrap reads with `cached(key, ttl, fn)`; invalidate keys on writes (e.g. group list after create).
- **R2** for large text/files: `list()`, `get(key)`→`obj.text()`, `put(key, content)`.

## D1 ingestion pipeline (the hard part)

D1 limits that dictate design (from Cloudflare docs, Apr 2026):
- Free: **500MB / DB**; Paid: **10GB / DB**; max row 2MB; statement 100KB
- Unlimited rows; **FTS5 virtual tables ARE supported** (export skips them)
- `wrangler d1 execute --file` accepts a SQLite file for import

Chunk everything: body text rows ≤60KB (comfortably under 100KB statement
and 2MB row). FTS5 rows per chunk (one FTS doc per chunk, not whole report),
so each doc stays under limits.

**UUID v7 PKs** (time-ordered, k-sortable, ideal for SQLite/D1 index append):
- JS: `import { v7 } from "uuid"` (uuid@14)
- Python (ingester): implement manually — see `scripts/verify_uuid_v7.py` for
  the correct bit layout and a self-check. Pitfall: variant bits must be
  `(0x2 << 62)`, NOT `0x8 << 62`; naive hex-string concatenation yields a
  30-char invalid UUID.

**Idempotent rebuild**: with AUTOINCREMENT PKs, `INSERT OR IGNORE` grows
duplicate rows on every rebuild. Use stable composite keys
(`ticker, year, report_type, filename`) + `INSERT OR REPLACE` for metadata,
and `DELETE FROM children WHERE parent_id=...` before re-inserting chunks/FTS
rows.

## Verification (run before claiming done)

1. `python3 scripts/build_d1.py ...` → dry-run SQLite at /tmp
2. Spot-check counts, PK format (`GLOB` pattern), `PRAGMA foreign_key_check`
3. `bun run check` (tsc --noEmit)
4. `npx wrangler deploy --dry-run` → confirms all bindings resolve

## Hermes wiring (client side)

```yaml
mcp_servers:
  investment_vault:
    url: "https://investment-vault.<sub>.workers.dev/mcp"
    timeout: 180
```

`elysia-mcp` mounts Streamable HTTP at `/mcp` by default.

## Pitfalls

- **elysia-mcp peer conflict**: peer range is `>=1.4.21`; Elysia 2.0.0-beta
  fails semver. Fix: `bun install --legacy-peer-deps` (bun warns but proceeds).
- **Elysia 2 + Workers**: `elysia` ships `adapter/web-standard`; the Worker
  `default` export + `app.fetch` works. Dry-run deploy to confirm bundling
  (~400KB gzip).
- **Drizzle rc.4**: `drizzle(db, { schema })` option is GONE — call
  `drizzle(db)` only.
- **FTS5 'rebuild'**: `INSERT INTO fts(fts) VALUES('rebuild')` is invalid for
  external-content tables. Standalone FTS with direct row inserts is simpler.
- **FTS5 prepared binding**: `WHERE reports_fts MATCH ?` with
  `.bind(query, ticker, limit)` on `DB.prepare()` — never interpolate.
- **tmpfs `/tmp` (VPS) fills**: a 3GB SQLite + npm cache together overflow
  `/tmp` → `npm error errno -122 EDQUOT`. Set `npm config set cache
  ~/.npm-cache` (disk, not tmpfs).
- **Cloudflare auth**: dashboard API token with Account→D1→Edit +
  Workers Scripts→Edit only (no Zone/R2/Billing) is enough for create/import/
  deploy; revoke after deploy — the Worker URL itself needs no token.
- **Free tier shock**: full import >500MB requires Workers Paid ($5 + storage
  ~$3-4/GB/mo). Offer structured-only (~25MB) import as a free-path option.

## References

- `references/investment-d1-session.md` — real session: schema tables,
  per-ticker parsing rules, counts, and the Cloudflare API-token guidance.
- `templates/wrangler.toml` — full bindings template with placeholders.
- `scripts/verify_uuid_v7.py` — validates a Python uuid7 implementation
  (correct bit layout + regex), run before trusting generated IDs.
