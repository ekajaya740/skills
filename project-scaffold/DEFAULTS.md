# Defaults

The stack choices this standard scaffolds, and the reason each is a default rather than a
preference. A default is what you build when the user has not said otherwise — not a rule.

## Runtime and package manager

| Default | Reason | Switch to it when |
| --- | --- | --- |
| **Bun** | One tool for install, run, test, bundle. Fast enough that CI slowness stops being a design constraint. | Node-only library, or a host that refuses Bun at runtime |
| **pnpm** | Strict `node_modules`, real workspace support | The repo already uses it, or a dependency needs hoisting |
| **uv** | Python env + lock + run in one binary | A dependency pins to old resolution, or the team standardises on Poetry |

Mixed repos: keep one package manager per language, and one command at the root that shells to
both. Two lockfiles for one language is a bug.

## Language and types

| Default | Reason |
| --- | --- |
| **TypeScript strict** | `strict: true`, `noUncheckedIndexedAccess: true`. The value is at the boundary, not in the annotations. |
| **Zod at boundaries** | One schema per boundary, types derived from it. Types that are declared separately from their validator drift. |
| **Python 3.12+ with type hints** | Match the version CI runs; hints checked by `mypy` or `pyright` in CI |

## Layout

| Default | Reason | Avoid |
| --- | --- | --- |
| `src/` for source | Every tool assumes it; a flat repo cannot grow | Top-level `lib/` + `utils/` |
| `tests/` mirroring `src/` | Finding a test is the same lookup as finding its subject | Co-located `*.test.ts` in a repo with generated code |
| `docs/` for decisions | Keeps `AGENTS.md` short and gives rules a home | A wiki nobody opens mid-task |
| `scripts/` for repeated commands | A command in a README is a command that breaks silently | `package.json` scripts over 6 lines of shell |

## Tooling

| Concern | Default | Note |
| --- | --- | --- |
| Lint + format | **oxlint + oxfmt** for TS; **ruff** for Python | One binary each; no plugin ecosystem to maintain |
| Test runner | **bun test** or **vitest**; **pytest** | Match the runtime — a second toolchain is a second failure mode |
| CI | One workflow, one job, the same commands as local | CI that runs different commands than the developer is CI that finds different bugs |
| Pre-commit | Optional. Cheap lint + format, plus the repo's one gate; never the full suite | Scope and the disable check belong to skill `verify-change` § The commit hook — one owner, no second copy |

## Astro / Cloudflare

| Concern | Default |
| --- | --- |
| Rendering | Astro SSR on Workers for anything with auth; static for marketing |
| API | Hono on the same Worker, `/api/*`; a separate Worker only when the runtime limits differ |
| Data | Drizzle ORM; Neon/Postgres behind Hyperdrive, or D1 for small edge-local data |
| Assets | R2 + a signed-URL route; never public buckets for user content |
| UI | shadcn/ui + Tailwind v4; tokens in `@theme`, not a JS config |

## Monorepo

| Concern | Default |
| --- | --- |
| Task runner | **Turborepo** — task graph, remote cache, no custom orchestration |
| Boundaries | `apps/` = deployables, `packages/` = libraries. A package never imports from an app. |
| Versioning | Workspace protocol (`workspace:*`), one lockfile at root |
| Shared config | One root `tsconfig.json` with `paths`; packages extend, never copy |

## When to break a default

Break it when the user names a constraint, when an existing repo already committed to the
alternative, or when a host genuinely forbids the default. Write the reason in
`docs/architecture.md` — a default broken without a recorded reason gets re-litigated every
session.

## Related

- Which target uses which defaults → [`SKILL.md`](SKILL.md) § Classify the project
- Per-target trees → [`targets/`](targets/)
