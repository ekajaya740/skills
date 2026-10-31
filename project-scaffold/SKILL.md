---
name: project-scaffold
description: Scaffold a new project of any kind — pick the layout, stack defaults, and agent layer, and get to the first green run. Covers TypeScript/Node, Astro/Cloudflare, Python, monorepo, and agent-only/skill repos.
disable-model-invocation: true
version: 0.2.0
---

# Project Scaffold

Start a project that is already shaped the way an agent can work in it. The goal is not a
template — it is a **first green run** you can hand to `verify-change` as evidence.

Read [`DEFAULTS.md`](DEFAULTS.md) before choosing anything. It holds the stack choices and why
they are defaults rather than preferences.

## 1. Classify the project

One question decides everything else: **what has to exist when the project is done?**

| Kind | Answer | Target |
| --- | --- | --- |
| Web app, one deployable | A URL | [`targets/web-app.md`](targets/web-app.md) |
| Multi-package repo, several deployables | Several URLs from one repo | [`targets/monorepo.md`](targets/monorepo.md) |
| CLI, service, script, data work | A binary or a running process | [`targets/python.md`](targets/python.md) |
| Skills, rules, prompts — no build | Files an agent reads | [`targets/agent-only.md`](targets/agent-only.md) |
| Docs vault, research corpus, writing, notes | Files a human reads, that must stay valid | [`targets/agent-only.md`](targets/agent-only.md) § Non-code repos |
| Astro SSR on Cloudflare Workers | A Worker + Pages | [`targets/cloudflare.md`](targets/cloudflare.md) |

Ambiguous? Pick by *deployable count*, not by language. One deployable is a web app even if it has
twenty folders. Several is a monorepo even if they share a language.

**No deployable at all is not a lesser project.** A vault, a corpus or a book has the same three
needs as a service — a stated structure, an agent layer, and one command that proves it is still
valid. Only the third differs: a link check or schema lint instead of a build. Do not scaffold a
`package.json` into a notes repo to satisfy a template.

**Done when** you can name the target file and the single command that will prove the project
is valid.

## 2. Write the structure before the content

Each target file gives the directory tree with a reason per folder. Copy it, then delete folders
you cannot justify in one line. An unjustified folder becomes a home for nothing.

Three folders every non-trivial project gets, whatever the stack:

| Folder | Holds | Why it exists |
| --- | --- | --- |
| `docs/` | Decisions, architecture, environment, testing | The place `AGENTS.md` points at instead of growing |
| `scripts/` | Repeatable commands a human or CI runs | Anything run twice stops being a one-liner in a README |
| `.github/workflows/` | CI | The green check `verify-change` reads |

**Done when** the tree has a stated reason for every top-level folder and no folder is empty.

## 3. Lay down the agent layer

Per skill `repo-init`.

### Ask about dotfiles first

Ask this and wait for the answer before writing anything below:

> Does this project use your `ekajaya740/dotfiles`? They are tuned for **omp** — omp-jev routing,
> 9router model aliases, the `claude/` and `jev/` deploy scripts — so a repo on another harness
> inherits wiring it will never read.

Ask once and wait. `~/dotfiles` existing on the machine is not a yes.

| Answer | What changes |
| --- | --- |
| **Yes** | Point at the machine layer, never copy it: `AGENTS.md` names `~/dotfiles` and `bash ~/dotfiles/bootstrap.sh` as the machine setup step, and the harness shims come from there. |
| **No** | Write `CLAUDE.md` / `.cursor/rules` by hand, and record no dotfiles dependency. |

**Done when** `AGENTS.md` carries one line under the stack section: either "machine layer:
`ekajaya740/dotfiles` (omp-tuned)" or "self-contained, no dotfiles dependency".

Then the layer itself, minimum, in this order:

1. `AGENTS.md` — stack, the green-command table, hard rules, out-of-bounds.
2. `CLAUDE.md` → `@AGENTS.md` (and any other harness shim the user needs).
3. `.agents/skills/` + `skills-lock.json` — the project-local skill store, pinned and reproducible.
4. `docs/architecture.md` — only if the project has more than one module.
5. `.gitignore` — before the first commit, never after. Ignore `.agents/` and `.claude/skills/`;
   track `skills-lock.json`, which no rule ignores.

**Done when** a fresh agent could run the project from `AGENTS.md` alone, and a clean checkout
restores its skills with one command.

## 4. Get green once, deliberately

Install, build, typecheck, test, lint — whatever the target's table lists. Fix what fails **now**,
while the project is small enough to understand completely. A scaffold that ships yellow becomes a
repo where yellow is normal and nobody can tell a new break from the old one.

Record the exact commands and their output in the reply. That is the evidence `verify-change`
will accept later.

**Done when** a clean checkout runs the green command to exit 0, and you have pasted the line
that proves it.

## 5. Commit the baseline

One commit, message stating the stack and that it is a working baseline. Not "initial commit" —
a year later that tells nobody what a working baseline was.

## What not to scaffold

- **No placeholder files.** An empty `utils.ts` is a promise nobody keeps. Delete it; adding a file
  later is one command.
- **No example code.** A sample route nobody asked for is code that has to be maintained and
  reviewed and teaches the wrong shape.
- **No test file with a fake assertion.** `expect(true).toBe(true)` is worse than no test: it makes
  the suite green while proving nothing.
- **No license, README badges, or CI matrix** the user did not ask for. Ask once, in the reply,
  then drop it.

## Related

- Stack choices and their reasons → [`DEFAULTS.md`](DEFAULTS.md)
- The agent layer in detail → skill `repo-init`, and its [`SKILLS.md`](../repo-init/SKILLS.md) for the pin set
- Proving the result → skill `verify-change`
