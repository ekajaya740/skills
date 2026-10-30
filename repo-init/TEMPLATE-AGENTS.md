# AGENTS.md template

Copy, fill from the repo, delete every row with no true answer. Placeholders are in `«angle
quotes»` so a missed one is visible.

Keep the whole file under ~150 lines. The index table is the only part that grows freely —
each extra row costs one line and is reached only when it fires.

---

```md
# Agent Guide — «Project Name»

## What this is

«One paragraph, from the user's perspective. What the product does, who for, what breaks
expensively. Not the tech stack — that is the next section.»

## Stack

«Runtime · language · framework · database · host. One line. Include versions only where the
version changes what an agent may write.»

## The standard, by area

Everything the agent must obey is either in this file or in a file below. Load only the file
for the area you are touching.

| Topic | File | Load it when |
| ----- | ---- | ------------ |
| «Writing code — patterns, banned APIs» | `«CODING_STANDARDS.md»` | Before editing source |
| «Where things live» | `«docs/architecture.md»` | Orienting, or moving modules |
| «Running it, env vars, deploys» | `«docs/environment.md»` | Starting a server, touching config |
| «Testing and what proof is accepted» | `«docs/testing.md»` | Deciding whether or how to verify |

## Hard rules

Each names the file holding its full statement. These bind every task; a rule lives here only
if an agent that never opened a detail file would still break it.

- **Never guess a specification.** Underspecified scope, criteria, naming, or surface → stop and
  ask. An assumption nobody confirmed is not a decision. `«docs/workflow.md»`
- **Prove it before calling it done.** A claim names the layer it was verified at. "Should work"
  is not evidence. `«docs/testing.md»`
- **One rule, one home.** A rule is stated once; every other mention points at the owner.
  Duplicated rules drift, and a drifted rule is violated. `«docs/rules.md»`
- **«Never touch production.»** «State the boundary concretely: which host, which database URL,
  which deploy command.»
- **«Comment only what the code cannot say.»** «A non-obvious why — a constraint, a trap, a
  rejected alternative. Never narrate the diff.»
- **«Record every trap you hit.»** Symptom → cause → fix, in the file that owns that area,
  before moving on. `«docs/lessons.md»`

## Commands

| Check | Command | Green when |
| ----- | ------- | ---------- |
| Install | `«bun install»` | exits 0 |
| Build | `«bun run build»` | exits 0 |
| Types | `«bun run check-types»` | exits 0 |
| Tests | `«bun test»` | exits 0 |

## Out of bounds

«What the agent must not touch, and what it must ask before touching: generated files, lockfiles,
migrations, vendor directories, secrets, the deploy pipeline. Concrete paths.»

## Machine-local state

«What belongs to this machine and must not be committed: ports, worktree mappings, absolute
tool paths, a security policy that belongs in harness config. Say where it lives instead.»
```

---

## Filling it in

- **Hard rules cap at seven.** More than that and none of them bind, because the agent is
  trading them against each other. If you have ten, four are detail — move them.
- **Every hard rule names a consequence**, not just a prohibition. "Never touch production"
  means nothing without "which host". Fill the concrete in.
- **Delete the Commands table row you cannot run.** A command documented but broken is worse
  than a command undocumented.
- **No rule restates the stack.** If `package.json` says it, the file does not need to.

## Related

- The tier test and rule ownership → skill `agent-rules`
- The bootstrap that produces this file → [`INIT.md`](INIT.md)
