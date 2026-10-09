---
name: cloudflare-fullstack
description: "Build full-stack apps on Cloudflare: Astro SSR + Hono API on Workers, R2 storage, Neon Postgres via Hyperdrive, Drizzle ORM, shadcn/ui."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cloudflare, workers, astro, hono, drizzle, neon, r2, shadcn, fullstack]
    related_skills: [writing-plans, subagent-driven-development]
---

# Cloudflare Full-Stack Apps

Architect and build full-stack web applications on Cloudflare's edge platform using:
- **Astro 5 SSR** (Cloudflare adapter) for frontend with React islands + shadcn/ui
- **Hono** for the API backend on Cloudflare Workers
- **Neon Postgres** (serverless driver) with **Hyperdrive** for connection pooling
- **Drizzle ORM** for type-safe schema and queries
- **R2** for object storage (image uploads, files)
- **Bun** as runtime/package manager

## When to Use

- User wants to build a web app deployed to Cloudflare
- Astro + Hono stack is specified or implied by "Workers + SSR frontend"
- Neon/Hyperdrive for Postgres
- Any combination of the above technologies

## Architecture

```
money-manager/
├── package.json          # Workspace root
├── drizzle.config.ts
├── app/                  # Astro SSR frontend
│   ├── astro.config.mjs
│   ├── wrangler.toml
│   └── src/
│       ├── pages/
│       ├── components/   # React islands + shadcn/ui
│       └── lib/
│           └── api.ts    # Fetch wrapper → Hono API
├── api/                  # Hono Worker
│   ├── wrangler.toml
│   └── src/
│   ├── index.ts      # Hono app entry
│   ├── lib/
│   │   └── files.ts  # Files SDK instance factory
│   ├── db/
│       │   ├── schema.ts # Drizzle schema
│       │   └── index.ts  # DB connection
│       ├── routes/        # Route modules
│       └── types.ts      # Env bindings
└── drizzle/              # Migrations
```

**Key insight:** The Astro app calls the Hono API via `fetch()` — they're separate deployments (Pages + Workers) that communicate over HTTP. During local dev, both run on different ports.

## Setup Steps

### 1. Initialize workspace

```bash
mkdir money-manager && cd money-manager
# Root package.json with workspaces: ["app", "api"]
bun install
```

### 2. Create Hono API

```bash
cd api
bun add hono drizzle-orm @neondatabase/serverless files-sdk @aws-sdk/client-s3 @aws-sdk/s3-presigned-post @aws-sdk/s3-request-presigner
bun add -d wrangler drizzle-kit @cloudflare/workers-types
```

**wrangler.toml bindings:**
```toml
name = "app-api"
main = "src/index.ts"
compatibility_date = "2024-12-01"

[[r2_buckets]]
binding = "IMAGES"
bucket_name = "app-images"

[[hyperdrive]]
name = "DB"
id = ""  # wrangler hyperdrive create DB --connection-string=...
```

**Env types (api/src/types.ts):**
```typescript
export interface Env {
  DATABASE_URL: string;
  HYPERDRIVE?: Hyperdrive;
  IMAGES: R2Bucket;
  R2_ACCOUNT_ID: string;
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
}
```

### 3. Create Astro app

```bash
cd app
bun add astro @astrojs/react @astrojs/cloudflare @astrojs/tailwind react react-dom
npx shadcn@latest init -d
npx shadcn@latest add button card input select dialog badge progress tabs table sheet label
```

**astro.config.mjs:**
```javascript
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  output: 'server',
  adapter: cloudflare(),
  integrations: [react(), tailwind()],
});
```

### 4. API client pattern

```typescript
// app/src/lib/api.ts
const API_BASE = import.meta.env.API_URL || 'http://localhost:8787';

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

// For file uploads (R2):
export async function uploadImage(file: File): Promise<{ key: string; url: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}
```

### 5. R2 image upload via Files SDK

Use [files-sdk](https://files-sdk.dev) (`files-sdk` npm package) with the `files-sdk/r2` adapter for all R2 operations. It provides a unified, web-standards API (`upload`, `download`, `head`, `delete`, `url`, `signedUploadUrl`) and works with the R2Bucket binding inside Workers (zero egress) plus S3 credentials for presigned URLs.

**Install:**
```bash
cd api && bun add files-sdk @aws-sdk/client-s3 @aws-sdk/s3-presigned-post @aws-sdk/s3-request-presigner
```

**Env types — include R2 credentials for presigned URL support:**
```typescript
export interface Env {
  DATABASE_URL: string;
  HYPERDRIVE?: Hyperdrive;
  IMAGES: R2Bucket;
  R2_ACCOUNT_ID: string;
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
}
```

**Files SDK instance factory:**
```typescript
// api/src/lib/files.ts
import { Files } from "files-sdk";
import { r2 } from "files-sdk/r2";
import type { Env } from "../types";

export function createFiles(env: Env) {
  return new Files({
    adapter: r2({
      binding: env.IMAGES,           // R2Bucket binding — zero egress in-Worker
      bucket: "app-images",
      accountId: env.R2_ACCOUNT_ID,  // for presigned URLs via S3 API
      accessKeyId: env.R2_ACCESS_KEY_ID,
      secretAccessKey: env.R2_SECRET_ACCESS_KEY,
    }),
  });
}
```

**Upload routes:**
```typescript
// api/src/routes/upload.ts
import { Hono } from 'hono';
import type { Env } from '../types';
import { createFiles } from '../lib/files';

export const uploadRoutes = new Hono<{ Bindings: Env }>();

uploadRoutes.post('/', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('file') as File;
  if (!file) return c.json({ error: 'No file provided' }, 400);

  const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  if (!allowed.includes(file.type)) return c.json({ error: 'Invalid file type' }, 400);
  if (file.size > 10 * 1024 * 1024) return c.json({ error: 'File too large (max 10MB)' }, 400);

  const key = `uploads/${crypto.randomUUID()}.${file.type.split('/')[1]}`;
  const files = createFiles(c.env);
  const buffer = await file.arrayBuffer();
  await files.upload(key, buffer, { contentType: file.type });

  return c.json({ key, url: `/api/upload/${key}` }, 201);
});

uploadRoutes.get('/:key{.+}', async (c) => {
  const key = c.req.param('key');
  const files = createFiles(c.env);
  try {
    const [data, head] = await Promise.all([files.download(key), files.head(key)]);
    return new Response(data, {
      headers: {
        'Content-Type': head.contentType || 'application/octet-stream',
        'Cache-Control': 'public, max-age=31536000',
      },
    });
  } catch {
    return c.json({ error: 'Not found' }, 404);
  }
});

uploadRoutes.delete('/:key{.+}', async (c) => {
  const key = c.req.param('key');
  const files = createFiles(c.env);
  await files.delete(key);
  return c.json({ success: true });
});
```

**Set R2 secrets:**
```bash
npx wrangler secret put R2_ACCOUNT_ID
npx wrangler secret put R2_ACCESS_KEY_ID
npx wrangler secret put R2_SECRET_ACCESS_KEY
```

**Dev `.dev.vars.example` (committed to git as template):**
```
# Money Manager API — Local Development Variables
# cp .dev.vars.example .dev.vars  then fill in your values
# NEVER commit .dev.vars to git!

# Neon Postgres connection string
DATABASE_URL=postgresql://user:***@ep-xxx.aws.neon.neon.tech/money-manager?sslmode=require

# R2 Object Storage (Cloudflare dashboard → R2 → Manage R2 API Tokens)
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=***
```

The actual `.dev.vars` is gitignored. Users copy the example and fill in their real values.

### 6. Drizzle schema + connection

```typescript
// api/src/db/index.ts
import { drizzle } from 'drizzle-orm/neon-serverless';
import { Pool } from '@neondatabase/serverless';
import * as schema from './schema';

export function createDb(connectionString: string) {
  const pool = new Pool({ connectionString });
  return drizzle(pool, { schema });
}

export type DB = ReturnType<typeof createDb>;
```

**Usage in routes — single fallback pattern:**
```typescript
const db = createDb(c.env.HYPERDRIVE?.connectionString ?? c.env.DATABASE_URL);
```

Hyperdrive provides a pooled `connectionString` in production. In dev where it's undefined, falls back to raw `DATABASE_URL`. One function, one call — no manual branching.

### 7. Hono entry with route registration

```typescript
// api/src/index.ts
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import type { Env } from './types';
import { walletRoutes } from './routes/wallets';
import { uploadRoutes } from './routes/upload';

const app = new Hono<{ Bindings: Env }>();

app.use('*', logger());
app.use('*', cors({ origin: '*' }));
app.route('/api/wallets', walletRoutes);
app.route('/api/upload', uploadRoutes);
app.get('/api/health', (c) => c.json({ status: 'ok' }));

export default app;
```

### 8. Computed balances pattern

For money/finance apps, don't store running balances — compute them:

```sql
SELECT
  COALESCE(SUM(CASE WHEN type = 'income' THEN CAST(amount AS NUMERIC) ELSE 0 END), 0)
  + COALESCE(SUM(CASE WHEN type = 'transfer' AND to_wallet_id = :id THEN CAST(to_amount AS NUMERIC) ELSE 0 END), 0)
  + COALESCE((SELECT SUM(CAST(new_balance AS NUMERIC) - CAST(old_balance AS NUMERIC)) FROM balance_adjustments WHERE wallet_id = :id), 0)
  - COALESCE(SUM(CASE WHEN type = 'expense' THEN CAST(amount AS NUMERIC) ELSE 0 END), 0)
  - COALESCE(SUM(CASE WHEN type = 'transfer' AND wallet_id = :id THEN CAST(amount AS NUMERIC) ELSE 0 END), 0)
  AS balance
FROM transactions WHERE wallet_id = :id OR to_wallet_id = :id
```

Audit trail via `balance_adjustments` table — stores old_balance, new_balance, reason, timestamp.

### 9. Local dev

```bash
# Terminal 1: API
cd api && npx wrangler dev

# Terminal 2: App
cd app && bun run dev
```

API on `:8787`, Astro on `:4321`. The Astro app's `api.ts` fetches from `localhost:8787`.

**R2 local dev:** Wrangler dev supports R2 bindings natively — no separate MinIO needed.

### 10. Deploy

```bash
# Create R2 bucket (once)
npx wrangler r2 bucket create app-images

# Create Hyperdrive config (once)
npx wrangler hyperdrive create DB --connection-string="postgres://..."

# Deploy API
cd api && npx wrangler deploy

# Deploy Astro (Cloudflare Pages)
cd app && npx wrangler pages deploy dist/

# Set secrets
npx wrangler secret put DATABASE_URL
npx wrangler secret put R2_ACCOUNT_ID
npx wrangler secret put R2_ACCESS_KEY_ID
npx wrangler secret put R2_SECRET_ACCESS_KEY
```

## Pitfalls

- **Don't use `numeric` Drizzle columns in arithmetic without `CAST`.** Drizzle maps `numeric(18,2)` to string in JS. Always cast in SQL: `CAST(amount AS NUMERIC)`. Raw `SUM(amount)` returns a string; arithmetic on strings silently concatenates.
- **DB connection: use single fallback pattern.** `createDb(c.env.HYPERDRIVE?.connectionString ?? c.env.DATABASE_URL)` — one function, not separate Hyperdrive vs direct variants. Hyperdrive provides a `connectionString` property that's a standard Postgres URL; in dev where Hyperdrive is undefined, fall back to raw `DATABASE_URL`.
- **R2 key collisions.** Always use `crypto.randomUUID()` in keys — never rely on filenames from uploads. Prefix keys by domain: `transactions/{uuid}.{ext}`, `avatars/{uuid}.{ext}`.
- **CORS in dev.** Hono's `cors()` middleware is essential when Astro (port 4321) calls the API (port 8787). Without it, browser blocks fetches.
- **Astro `output: 'server'` is required** for Cloudflare adapter. Default is `static` which won't work.
- **Astro 5 + Tailwind CSS 4: `@astrojs/tailwind` may not be needed.** Astro 5 handles CSS natively. If `@astrojs/tailwind` causes issues, remove it and use a `globals.css` with `@import "tailwindcss"` imported in the layout instead. Check compatibility before adding.
- **shadcn init in monorepo.** `npx shadcn@latest init -d` inside `app/` — not at workspace root. The `components.json` must live beside `package.json`. shadcn v4+ uses `npx shadcn@latest` (not `shadcn-ui`).
- **Form data vs JSON for uploads.** R2 uploads must use `FormData`, not `JSON.stringify`. The Hono route reads `c.req.formData()`, not `c.req.json()`.
- **`files.upload()` takes `ArrayBuffer`, not `File`.** Do `const buffer = await file.arrayBuffer()` then `files.upload(key, buffer, { contentType })`. Passing a `File` object directly won't work — `files-sdk` expects raw bytes.
- **Use files-sdk for R2, not raw R2 binding API.** The `files-sdk/r2` adapter wraps the R2Bucket binding with a unified API and supports presigned URLs via S3 credentials. Raw `c.env.IMAGES.put/get/delete` works but doesn't give you `url()`, `signedUploadUrl()`, `copy()`, `move()`, or provider portability.
- **R2 presigned URLs need S3 credentials.** The R2Bucket binding alone can't generate presigned URLs. You need `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` as secrets, passed to the `r2()` adapter alongside the binding.
- **Transfers are wallet-to-wallet only.** No external accounts. Cross-currency transfers require user to manually enter `toAmount` — no auto-conversion. Exchange rates are view-only reference data.
- **Bun install location on read-only `/home`.** If `~/.bun` is read-only, install to `~/.hermes/bun` via `BUN_INSTALL=~/.hermes/bun bash` and add to PATH.
- **Wrangler R2 dev** stores objects in `.wrangler/state/` — ephemeral. Don't rely on persisted uploads across `wrangler dev` restarts.
- **Building both workspaces in parallel.** When the API and app are independent (app calls API via fetch, shares no imported code), dispatch 2 parallel subagents via `delegate_task(tasks=[...])` — one for the API, one for the app. This is far faster than serial per-task subagents. Provide each subagent with full context (schema, env types, route specs) so they don't need to read plan files.
- **Drizzle relations with multiple FKs to the same table.** When a table has two foreign keys to the same table (e.g., `transactions.walletId` and `transactions.toWalletId` both reference `wallets`), you MUST use `relationName` on both the `one()` and `many()` sides. Without it, Drizzle throws "There are multiple relations to the same table." See `references/money-manager-plan.md` for the exact pattern.
- **Drizzle Kit `generate` requires explicit flags in monorepo.** When running from a workspace package (`api/`), the config at repo root can't resolve the schema path correctly. Use explicit flags: `bunx drizzle-kit generate --out ../drizzle --schema ./src/db/schema.ts --dialect postgresql`. The `--dialect` flag is mandatory when you don't have a live DB connection or a `dbCredentials` block with a reachable URL.
- **Seed data belongs in `seed/`, not `drizzle/`.** Drizzle Kit owns the `drizzle/` directory — it rewrites the `_journal.json` on every `generate`. Put hand-written seed SQL in a separate `seed/` directory at workspace root. Add `db:seed` npm scripts that run `psql` or `bun` against those files.
- **Commit `.dev.vars.example`, gitignore `.dev.vars`.** Always create a `.dev.vars.example` with commented placeholders and instructions (which dashboard to get values from). The actual `.dev.vars` must be in `.gitignore`. Users run `cp .dev.vars.example .dev.vars` then fill in their secrets.
- **Standard `db:*` scripts for monorepo.** Always add these to the root `package.json` so database workflows are one command away:

  ```json
  {
    "db:generate": "cd api && bunx drizzle-kit generate --out ../drizzle --schema ./src/db/schema.ts --dialect postgresql",
    "db:migrate": "cd api && bunx drizzle-kit migrate",
    "db:push": "cd api && bunx drizzle-kit push",
    "db:studio": "cd api && bunx drizzle-kit studio",
    "db:seed": "for f in seed/*.sql; do echo \\\"→ $f\\\" && psql \\\"$DATABASE_URL\\\" -f \\\"$f\\\"; done",
    "db:reset": "psql \\\"$DATABASE_URL\\\" -c \\\"DROP SCHEMA public CASCADE; CREATE SCHEMA public;\\\" && bun run db:push && bun run db:seed"
  }
  ```
  This covers the full lifecycle: generate migrations, apply them, push schema directly (dev), browse data, seed, and nuclear reset.

## References

- Example plan/session references for a finance app built with this stack were archived (see ~/.trash/money-manager-skills-20260902/).
- See [`templates/seed-categories.sql`](templates/seed-categories.sql) for a starter categories seed SQL file.