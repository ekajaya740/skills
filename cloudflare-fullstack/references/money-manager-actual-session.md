# Money Manager — Session Notes (2026-06-04)

## What Was Built
Full-featured money management app: Astro SSR frontend + Hono API backend on Cloudflare Workers, Neon Postgres, Drizzle ORM, shadcn/ui, Recharts, Files SDK for R2 image uploads.

## Architecture Decision: Parallel Subagent Build
Built the entire app using 2 parallel subagents via `delegate_task(tasks=[...])`:
- **Subagent 1**: Full Hono API (schema, 8 route modules, middleware, files SDK)
- **Subagent 2**: Full Astro frontend (all pages, components, shadcn init, layout)

Both completed successfully in ~5-7 minutes. This is much faster than serial per-task subagents.

Key: Provide each subagent with complete context (schema DDL, route specs, component list, design guidelines) so they don't need to read external plan files.

## Drizzle Kit Generate in Monorepo
`drizzle-kit generate` failed with `bunx` from workspace root because the config couldn't resolve schema path correctly. Fixed by running from `api/` with explicit flags:
```bash
cd api && npx drizzle-kit generate --out ../drizzle --schema ./src/db/schema.ts --dialect postgresql
```
The `--dialect postgresql` flag is mandatory when there's no live DB connection.

## Package Mirror Issue (Tencent Cloud)
`bun` on this VM uses Tencent mirror by default which 404s for some packages. Fixed with:
```bash
npm_config_registry=https://registry.npmjs.org/ npx drizzle-kit generate
```
Or use `npx` from workspace `node_modules/.bin/` which doesn't go through the mirror.

## Files SDK Upload Route
Image keys should use path prefixes: `transactions/{uuid}.{ext}` not just `{uuid}.{ext}`. This organizes R2 objects and avoids key collisions.

## Seed SQL: Only Aggregate db:seed
User explicitly removed `db:seed:categories` — only the generic `db:seed` that iterates `seed/*.sql` is wanted. Don't add per-table scripts.

## .dev.vars Pattern
Committed `.dev.vars.example` with commented instructions for each secret (where to get it). Actual `.dev.vars` gitignored. Users `cp .dev.vars.example .dev.vars` and fill in values.