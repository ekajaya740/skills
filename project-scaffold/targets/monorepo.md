# Target: monorepo

For several deployables in one repo: `apps/` (things that ship) plus `packages/` (things they
share). Turborepo task graph, one lockfile, one green command at the root.

Use this when there is more than one thing to deploy. A single app with lots of folders is a
[web app](web-app.md) — the folder count is not the signal, the deployable count is.

## Tree

```
.
├── AGENTS.md                   # binding tier, root only
├── CODING_STANDARDS.md         # peers with AGENTS.md; the code-writing rules
├── GLOSSARY-MAP.md             # where each area's vocabulary lives
├── CLAUDE.md                   # @AGENTS.md
├── .env.example
├── package.json                # root scripts only; no dependencies of its own
├── turbo.json
├── tsconfig.json               # base with paths; packages extend, never copy
├── docs/
│   ├── agents/                 # the detail tier: worktree, env, testing, rules…
│   ├── architecture.md
│   └── conventions.md          # the patterns themselves, not the rules
├── apps/
│   ├── web/                    # deployable: public site
│   ├── api/                    # deployable: backend
│   └── admin/                  # deployable or a route group — decide, and record it
├── packages/
│   ├── schema/                 # Zod contracts crossing every boundary
│   ├── ui/                     # components + their DESIGN.md files
│   └── <domain>/               # one package per bounded context
└── .github/workflows/
```

## The two rules that keep it navigable

1. **`apps/` imports from `packages/`, never the reverse.** A package that imports an app is a
   package that cannot be tested alone, and the dependency graph stops meaning anything.
2. **The root owns binding rules; each package owns its area's detail.** A package never restates
   a root rule — it points. That is this standard's one-rule-one-home rule applied to a monorepo;
   see skill `agent-rules`.

## Root scripts

```json
{
  "scripts": {
    "build": "turbo run build",
    "check-types": "turbo run check-types",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "dev": "turbo run dev --parallel"
  }
}
```

Every package exposes the same script names. A package missing `check-types` silently passes the
root gate — that is the failure mode of monorepo CI.

## Where the agent layer goes

| File | Owns | Loaded |
| --- | --- | --- |
| `AGENTS.md` | Index + hard rules | Every session |
| `CODING_STANDARDS.md` | Rules applying to every file | Before editing source |
| `docs/agents/*.md` | Workflow, worktrees, env, testing, releases | On pointer fire |
| `packages/*/DESIGN.md`, `GLOSSARY.md` | Area vocabulary and visual contract | When touching that area |

A per-package `AGENTS.md` is a trap: two binding tiers means the agent reads one and misses the
other. Point from the root index instead.

## Seams to settle before the first package

Write these in `docs/architecture.md`:

1. **Which package owns the domain types** — one schema package, or one per context?
2. **How a package shares code with an app** — build output, source import, or published version?
3. **What the cache invalidates on** — `turbo.json` inputs, or every task re-runs.
4. **Which app is the deployable for each surface** — and where the admin portal lives.

## Anti-patterns

- A `packages/utils/` or `packages/shared/`. It is not a boundary, it is a dumping ground.
- Two lockfiles. The workspaces field and the lockfile must agree.
- A package with its own `tsconfig.json` that copies the root's settings instead of extending.
- Apps importing each other's internals via a deep path. If two apps share logic, it is a package.

## Related

- Stack choices → [`../DEFAULTS.md`](../DEFAULTS.md)
- Agent layer → skill `repo-init`, skill `agent-rules`
- Single deployable → [`web-app.md`](web-app.md)
