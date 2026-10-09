# Elysia on Cloudflare Workers — verified incompatible (2026-08-21)

## Conclusion

Elysia does **not** run on Cloudflare Workers — ANY version. Both
`2.0.0-beta.5` and latest stable `1.4.29` bundle successfully but fail at
RUNTIME on the first request with:

```
EvalError: Code generation from strings disallowed for this context
    at composeErrorHandler (file:///…/elysia/dist/compose.mjs)
    at composeGeneralHandler (file:///…/elysia/dist/compose.mjs)
    at get fetch (file:///…/elysia/dist/index.mjs)
    at _Elysia.handle (file:///…/elysia/dist/index.mjs)
```

Elysia composes route handlers at runtime via JIT `new Function`. Workers'
CSP blocks all code generation from strings. This is a platform
incompatibility, not a config problem — no flag or build step fixes it.

## Why dry-run tricks you

`wrangler deploy --dry-run` and `wrangler dev --local` START successfully
(~840 KiB / ~155 KiB gzip bundle). The EvalError is thrown **lazily** the
first time a route handler is composed — i.e. on the first HTTP request.
A green `--dry-run` proves nothing about runtime compatibility.

## Spike reproduction

```bash
mkdir -p /tmp/elysia-spike/src && cd /tmp/elysia-spike
```

package.json:
```json
{
  "name": "elysia-spike",
  "private": true,
  "type": "module",
  "dependencies": { "elysia": "^1.4.29" },
  "devDependencies": {
    "wrangler": "^4.74.0",
    "@cloudflare/workers-types": "^4.20250815.0",
    "typescript": "^5.9.2"
  }
}
```

wrangler.jsonc:
```json
{ "name": "elysia-spike", "main": "src/index.ts",
  "compatibility_date": "2026-08-19",
  "compatibility_flags": ["nodejs_compat"] }
```

src/index.ts:
```ts
import { Elysia } from "elysia";
const app = new Elysia()
  .get("/api/v1/hello", () => ({ hello: "world" }))
  .post("/api/v1/echo", ({ body }) => ({ body }));
export default {
  async fetch(request: Request) { return app.handle(request); },
} satisfies ExportedHandler;
```

```bash
bun install
bun x wrangler deploy --dry-run --outdir dist   # OK — bundles fine
bun x wrangler dev --local --port 8791          # OK — starts fine
curl http://127.0.0.1:8791/api/v1/hello         # ERROR — EvalError
```

## Working alternatives (both proven in production)

- **Vanilla fetch** — the investment-vault worker (`investing-ai`) routes
  `/mcp` + `/api/v1/*` with plain `fetch` routing. Live.
- **Hono** — used by the Money-Manager stack (see `cloudflare-fullstack`
  skill). Live.

## Next lesson

`wrangler deploy --dry-run` verifies **bundling only**, never runtime
compatibility. Before trusting a framework-on-Workers claim, run
`wrangler dev --local` and curl an actual route.
