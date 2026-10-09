# Worker Ops & Deploy Forensics (validated 2026-08-20)

Ops playbook for the investment-vault Worker fleet (MCP / API / TanStack
dashboard) — cleanup of stale Cloudflare resources and detecting foreign
overwrite deploys. Companion to `stateless-mcp-workers.md`.

## Cloudflare resource inventory (know what to clean)

Account-level sweep endpoints (all `GET`, bearer token):
- Workers: `GET /accounts/{acct}/workers/scripts` → list names.
- KV: `GET /accounts/{acct}/storage/kv/namespaces?per_page=50`.
- R2: `GET /accounts/{acct}/r2/buckets` → **`result.buckets` array** (NOT a
  bare `result` array — the classic one-liner `[b['name'] for b in
  d['result']]` blows up with `TypeError: string indices must be integers`).
- DO namespaces: `GET /accounts/{acct}/workers/durable_objects/namespaces`.
- Schedules: `GET /accounts/{acct}/workers/scripts/{name}/schedules` →
  `result.schedules` array (empty = none).
- Script bundle: `GET /accounts/{acct}/workers/scripts/{name}` with header
  `Content-Type: text/javascript` → multipart; part 1 is `worker.js`.
- Version metadata: `GET .../workers/scripts/{name}/versions/{id}` → JSON with
  `resources.script.etag`, `last_deployed_from`, `named_handlers`.

General rule: **print raw JSON before trusting `d['result']`** — CF API shapes
vary by endpoint (bare array, wrapped `{buckets:[...]}`, `{schedules:[...]}`,
or 404 for `deployments/by-script`). A dead zone route check returned
`Authentication error` for zone routes — don't chase zone APIs for
workers.dev-only workers.

## Removing a legacy Durable Object cleanly (3-step sequence)

Removing the DO class from a stateless MCP worker — deploying "clean" fails at
step 2 if you try to skip ahead:

1. Delete the DO class + `MCP_SESSIONS` binding from `src/index.ts` and
   `wrangler.toml`, then `wrangler deploy` → FAILS with
   `New version of script does not export class 'X' which is depended on by
   existing Durable Objects ... use a delete-class migration [code 10064]`.
   The CF API also refuses namespace deletion while the binding references it:
   `Cannot delete the Durable Object namespace ... because it is still
   referenced by the binding ...`.
2. Re-add a temporary delete-class migration and deploy:
   ```toml
   [[migrations]]
   tag = "v2"
   deleted_classes = ["McpSessionStore"]
   ```
   Deploy succeeds; the namespace is removed.
3. Remove the temporary migration from `wrangler.toml`, deploy again → clean
   final state. Verify `total_count: 0` on the DO namespaces endpoint.

## Detecting foreign overwrite deploys

Workers deployed from ANOTHER machine/CI can silently clobber your deploy
(observed on both `investment-vault-mcp` and `investment-vault-dashboard` —
7+ `Source: Unknown (version_upload)` deployments, some ~2 seconds after our
own deploy, author email still the account owner).

Symptoms & forensics:
- **HTML served ≠ repo build**: check distinctive markers. Foreign TanStack
  dashboard used Tailwind classes (`min-h-screen`), 2-link nav; our build uses
  custom classes (`topnav`, `brand`) + 3 links. Foreign build lacked `notes`
  routes → 404 on `/notes`, 500 on routes querying dropped tables.
- **`npx wrangler deployments list --name <worker>`** → `Source: Unknown
  (deployment)` / `version_upload` entries created AFTER your deploy. A
  cluster of them (3 in 20s) while you only deployed once = foreign writer.
- **Version etag comparison**: download version metadata JSON for two versions,
  compare `resources.script.etag`. Identical etag + different `created_on` =
  same bundle re-uploaded — the foreign build keeps coming back.
- **Timeline correlation**: a 12-minute quiet gap after the last foreign
  deploy = writer may have stopped; redeploy then, and re-check quickly.
- **Not edge cache**: `wrangler deploy` printing a NEW version ID while the
  live HTML still shows old markers is NOT cache — a newer foreign deployment
  is active. Confirm via `deployments list` timestamps.
- **Check local writers first**: VPS cron (`~/.hermes/cron/jobs.json`), systemd
  user units (`systemctl --user list-units` — a stray `hermes-worker-proc_*`
  scope from an old `wrangler tail` lingers), tmux/screen, other Hermes
  profiles (`~/.hermes/profiles/*/cron/`), GitHub Actions
  (`gh api repos/{owner}/{repo}/actions/workflows`), other machines sharing the
  CF token.
- **Fix**: rebuild + `wrangler deploy` from the repo, verify page markers +
  `deployments list`; if foreign deploys resume, hunt the writer before
  redeploying again.

## Dashboard (TanStack Start on Workers) gotchas

- Server fn call sites: `fn({ data: params.x })`, never `fn(params.x)`;
  `.validator(...).handler(async ({ data }) => ...)`; do NOT set
  `method: 'GET'` on server fns (payload is dropped → `data` undefined).
- `POST /_server_fn` with `{}` returns HTML (router fallback), not JSON —
  probe real routes instead.
- Root render can 500 while a detail route (e.g. `/companies/BBRI`) returns
  200 — always test the full route set (`/`, `/companies`, `/notes`,
  `/companies/{ticker}`, `/notes/{path}`).
- Deployed HTML marker check (compressed!): `curl -s --compressed URL | grep
  -aoE 'min-h-screen|class="topnav'` distinguishes foreign vs repo build.
- Wrangler `tail` is slow to attach; if it captures nothing in 40s, switch to
  the CF API (script bundle + deployments) instead of waiting.

## Cleanup checklist after decommissioning a worker

- Delete worker script (or confirm already gone: `GET .../workers/scripts/{name}`
  → `success: false`, `This Worker does not exist`).
- Delete orphaned KV namespaces not bound by any live worker (grep
  `wrangler.*`/`*.toml` for `id =`).
- Delete DO namespaces via the delete-class migration sequence above.
- Confirm schedules empty across remaining workers.
- Leave R2 buckets alone unless the worker is confirmed gone — buckets are
  shared across projects (portfolio, second-brain).
