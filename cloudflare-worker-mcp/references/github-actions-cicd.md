# GitHub Actions CI/CD for the investment Worker (2026-08-21)

User asked: *"buat repo private. github action juga untuk semua perubahan"*.
Repo `ekajaya740/investing-ai` already existed (private) with `origin` set;
remote was 3 commits behind local — push before adding CI.

## Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  check:
    name: Typecheck & Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - name: Install dependencies
        run: bun install --frozen-lockfile
      - name: Typecheck
        run: bun run check-types
      - name: Build client
        run: bun run build:client

  deploy:
    name: Deploy to Cloudflare Workers
    if: github.ref == 'refs/heads/main'
    needs: check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - name: Install dependencies
        run: bun install --frozen-lockfile
      - name: Build client
        run: bun run build:client
      - name: Deploy Worker
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: deploy
```

Key points:
- `bun install --frozen-lockfile` — CI must match the committed `bun.lock`.
- Deploy job gated on `github.ref == 'refs/heads/main'` + `needs: check`.
- `wrangler-action@v3` reads `wrangler.jsonc` from the repo root — no extra
  config needed; the D1/KV bindings resolve from the checked-in file.

## Secrets pitfall (blocked this session)

The workflow needs two repo secrets: `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID`. On this VPS there is **no `gh` CLI login and no
GitHub token** (only an SSH key that can push). `gh auth status` → "not logged
into any GitHub hosts". So the agent CANNOT set repo secrets itself — the user
must either set them in GitHub UI (Settings → Secrets and variables → Actions)
or provide a token. Do not burn time trying `gh secret set` on a machine
without `gh` auth; ask the user up front.

## Repo visibility check without a token

`curl https://api.github.com/repos/{owner}/{repo}` unauthenticated returns
`404 Not Found` for a **private** repo (and for a nonexistent one) — so a 404
does NOT mean the repo is missing. Confirm existence via
`git ls-remote origin` (works over SSH) instead.
