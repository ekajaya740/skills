# Target: web app (one deployable)

For a single site or app: marketing page, dashboard, API + frontend, an internal tool. One
deployable, one green command.

Use this when there is exactly **one** thing to deploy. Two deployables is a
[monorepo](monorepo.md), even if they share a folder today.

## Tree

```
.
├── AGENTS.md                 # the binding rules; see skill `standard`
├── CLAUDE.md                 # @AGENTS.md
├── .gitignore                # before the first commit
├── .env.example              # every var, no values
├── README.md                 # what it is, how to run it
├── package.json
├── tsconfig.json
├── docs/
│   ├── architecture.md       # module map and why the seams are where they are
│   ├── environment.md        # vars, local services, deploy
│   └── testing.md            # what is tested and what proof is accepted
├── scripts/
│   └── dev.sh                # only if `bun run dev` is not enough
└── src/
    ├── index.ts              # entry point, thin
    ├── routes/               # one file per surface
    ├── lib/                  # pure logic, no framework imports
    ├── db/                   # schema, migrations, queries
    └── components/           # UI, if server-rendered
├── tests/
│   └── <mirrors src/>
└── .github/workflows/ci.yml
```

**Why each folder exists**

| Path | Reason |
| --- | --- |
| `src/routes/` | One file per URL is the lookup an agent does most often |
| `src/lib/` | Where logic goes so tests can call it without a server. If `lib/` imports the framework, the seam is wrong. |
| `src/db/` | Schema and queries together; a schema change and its query drift apart otherwise |
| `tests/` mirroring `src/` | Finding a test is the same lookup as finding its subject |
| `docs/` | Where `AGENTS.md` points instead of growing |

## Green commands

```json
{
  "scripts": {
    "dev": "…",
    "build": "…",
    "check-types": "tsc --noEmit",
    "test": "bun test",
    "lint": "oxlint src tests",
    "format": "oxfmt --write ."
  }
}
```

`AGENTS.md` carries the same table with **Green when: exits 0**. If a script is not worth running
before a commit, delete it rather than documenting it.

## Decisions to record while scaffolding

Write these into `docs/architecture.md` as you choose them. They are the questions the next
session will otherwise re-open:

1. **Where does the boundary live** — one app, or a frontend calling a separate API?
2. **How does data reach the UI** — server-rendered, client fetch, or both?
3. **Where does auth live** — middleware, route guard, or per-handler?
4. **What is the one seam tests sit at** — HTTP handler, module boundary, or component?

## Anti-patterns at scaffold time

- A `src/utils.ts` that collects unrelated helpers. Name the concept or delete the file.
- Framework types leaking into `lib/`. That is what makes `lib/` untestable later.
- `.env` committed "temporarily". It survives every cleanup.
- A `README.md` that documents a command which does not exist yet.

## Related

- Stack choices → [`../DEFAULTS.md`](../DEFAULTS.md)
- Astro on Cloudflare → [`cloudflare.md`](cloudflare.md)
- Several deployables → [`monorepo.md`](monorepo.md)
