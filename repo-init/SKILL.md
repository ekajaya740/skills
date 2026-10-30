---
name: repo-init
description: Bootstrap a repo's agent layer from nothing — AGENTS.md, detail tier, harness shims, and the green-command table. Use only when a repo has no AGENTS.md at all. For a repo that already has one, use repo-align.
disable-model-invocation: true
version: 0.2.0
---

# Repo Init

Build the instruction layer for a repo that has none, in seven steps, ending with a green check
you can paste as evidence.

The failure this prevents: a repo where every session re-derives the same facts, and the rules
that matter live in a skill the agent never opens.

Read [`INIT.md`](INIT.md) and run it. This file is only the entry point: what the job is, what it
produces, and how to know it is done.

## Stop here if the folder is empty

An empty folder cannot produce an `AGENTS.md`, because every section of one is a fact about code
that does not exist yet. Step 1 asks you to read the build command, the green command and the
primary branch from files. On an empty folder there are no files, so the honest output is not a
shorter document — it is a question.

Check first:

```bash
ls -A | head           # nothing but .git → the folder is empty
git branch -r 2>/dev/null | head
```

**If there is no code, no manifest, and no CI**, do not write `AGENTS.md`. Say what is missing and
ask what the folder will hold:

> This folder has no code, manifest or CI, so I can't write the stack, the green command or the
> branch — the three things `AGENTS.md` is mostly made of. What will it hold: code, or something
> else? If code, `project-scaffold` picks the stack first and lays down the agent layer after,
> which is the order that avoids inventing facts.

Two outcomes:

| The user says | Do |
| --- | --- |
| "Scaffold it too" / names a stack | Skill `project-scaffold` — it creates the project *and* the agent layer, with real commands to record |
| "Just the AGENTS.md, I'll add code later" | Write a **partial** file, below |

### The partial file

Only two things are true before any code exists, and neither comes from the folder:

1. The three project-independent hard rules — never guess a spec, prove before done, one rule one
   home.
2. An explicit list of what is not yet known.

```md
# Agent Guide — «Project Name»

## Status

Scaffolded before any code. The sections below are deliberately incomplete; fill each one at the
first commit that makes it answerable, then delete this section.

## Hard rules

- **Never guess a specification.** Underspecified scope → stop and ask.
- **Prove it before calling it done.** A claim names the layer it was verified at.
- **One rule, one home.** Stated once; every other mention points at the owner.

## Not yet known — do not invent

| Fact | Fill it when |
| --- | --- |
| Stack | The first dependency is added |
| Build command | `package.json` / `pyproject.toml` / `Makefile` exists |
| Green command | There is a test or typecheck to run |
| Primary branch | The first push |
| Out-of-bounds | The first path an agent should not touch |
```

**Never fill a row with a plausible default.** A green command that was guessed is worse than an
empty one: the agent runs it, it fails, and the file teaches the agent to distrust the file. An
`AGENTS.md` with four known-unknowns is honest and useful; one with `bun test` in a repo that has
no `package.json` is a lie the next session will act on.

**Done when** either the folder has enough evidence to run the seven steps, or the user has been
asked and has chosen a path.

## What it produces

| Artifact | Tier | Holds |
| --- | --- | --- |
| `AGENTS.md` | Binding | Stack, hard rules, the green-command table, out-of-bounds. Under ~150 lines. |
| `docs/agents/` | Detail | One file per area. Created on the first detail rule that earns a file — not before. |
| `CLAUDE.md`, `.cursor/rules/*.mdc`, … | Shim | A pointer to `AGENTS.md`. Never a second copy. |
| `.agents/skills/` + `skills-lock.json` | Store | The pinned skills the repo's procedures live in. Lock committed, directory ignored. |

Template: [`TEMPLATE-AGENTS.md`](TEMPLATE-AGENTS.md). Copy it, fill it from the repo, delete every
row with no true answer.

## The one rule that makes it work

**Never write a second copy of a rule for a second harness.** A harness that cannot follow a
pointer gets the pointer plus a one-line summary, not the file. Two copies drift, and a drifted
rule is violated — see skill `agent-rules` § One rule, one home.

## Done when

1. `AGENTS.md` names the build command, the green command, and the primary branch — all copied
   from files, not memory.
2. Every fact collected has exactly one destination, and nothing is in two.
3. A harness opening the repo lands in `AGENTS.md` in one hop.
4. The green command passes on a clean checkout, and you have pasted the line that proves it.
5. `skills-lock.json` is committed, and a clean checkout restores the set with `npx skills@latest
   experimental_install`.

Step 7 of [`INIT.md`](INIT.md) has the test: hand `AGENTS.md` to a fresh agent and ask what it
would get wrong about this repo without it. Every missing answer is a binding rule; every answer
that would never be broken is noise.

## Repo already has `AGENTS.md`

Do not rewrite it. Run the audit instead: skill `repo-align`. It reports wrong, duplicated, and
missing rules against the same template, and changes nothing until you approve.

## Related

- The seven steps → [`INIT.md`](INIT.md)
- What to pin and how → [`SKILLS.md`](SKILLS.md)
- The file to copy → [`TEMPLATE-AGENTS.md`](TEMPLATE-AGENTS.md)
- Tiers and ownership → skill `agent-rules`
- Audit an existing repo → skill `repo-align`
- The whole routing table → skill `standard`
