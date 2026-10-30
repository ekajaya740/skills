# Target: Cloudflare (Astro SSR + Worker API)

Astro SSR on Workers with a Hono API in the same Worker, Neon Postgres via Hyperdrive, R2 for
user assets, shadcn/ui. For a public site with auth or an app that must be fast from many regions.

Only reach for this when the project needs either edge latency or a genuinely cheap deploy. A
boring Node host is simpler and you should say so.

## Tree

```
.
├── AGENTS.md
├── CLAUDE.md                 # @AGENTS.md
├── astro.config.mjs          # adapter: cloudflare, output: server
├── wrangler.jsonc            # bindings: DB, R2, KV, vars per environment
├── .dev.vars.example
├── package.json
├── docs/
│   ├── architecture.md
│   ├── environment.md        # local dev, remote bindings, deploy, secrets
│   └── testing.md
├── src/
│   ├── pages/                # Astro routes; SSR by default
│   ├── islands/              # React islands only where interactivity is needed
│   ├── api/                  # Hono app mounted at /api/* in one catch-all route
│   ├── db/                   # Drizzle schema + queries (Hyperdrive client)
│   ├── lib/                  # pure logic, no Astro imports
│   └── components/           # shadcn/ui + project components
├── drizzle/                  # generated migrations; committed
├── tests/
└── .github/workflows/
```

## Bindings, one per concern

| Binding | Holds | Why |
| --- | --- | --- |
| `HYPERDRIVE` | Postgres connection string | Pooling at the edge; never put the raw URL in a var |
| `ASSETS` (R2) | User uploads | Signed URLs; never a public bucket |
| `KV` | Sessions or small cached lookups | Only where a Postgres round-trip is measurably too slow |
| Vars | Public config | Anything secret is a Worker secret, not a var |

`wrangler.jsonc` declares the bindings per environment; `.dev.vars.example` lists what a local
run needs. A binding added in code but not in `wrangler.jsonc` is a deploy that fails at runtime,
not a build error — that is why the file is reviewed like source.

## Green commands

```bash
bun install
bun run check-types
bun run build              # astro build + wrangler dry-run deploy
bun run test
bunx wrangler deploy --dry-run    # proves bindings resolve without shipping
```

`--dry-run` is the cheap proof that a binding change is coherent. Use it before any real deploy.

## Local development

```bash
bun run dev                # astro dev, local bindings via wrangler
bunx wrangler dev          # to test real bindings (R2, Hyperdrive local)
```

Hyperdrive locally needs `wrangler dev`; plain `astro dev` uses the `DATABASE_URL` from
`.dev.vars`. Say in `docs/environment.md` which one a task needs — the difference costs an hour
the first time it bites.

## Seams

1. **`/api/*` is Hono**, mounted once. One place for auth middleware, one place for error shaping.
2. **Data access only in `src/db/`**, taking a client argument. A query that builds its own client
   cannot be tested against a local Postgres.
3. **Islands are the interactive boundary.** A page that is SSR-only should not import React.
4. **R2 access goes through one module** with signed URLs. Scattered `env.ASSETS.put` calls make
   the access policy unreviewable.

## Anti-patterns

- Secrets in `wrangler.jsonc` `vars`. They are visible in the dashboard and the repo.
- `output: 'static'` on a route that reads a cookie. It builds and then 500s.
- A Worker that opens a Postgres connection per request without Hyperdrive.
- Migrations applied by hand in the dashboard and never committed. `drizzle/` is source.
- Two Workers where one would do. Split when the runtime limits differ, not by folder aesthetics.

## Related

- Stack choices → [`../DEFAULTS.md`](../DEFAULTS.md)
- Single deployable, non-edge → [`web-app.md`](web-app.md)
- Proving a deploy → skill `verify-change`
