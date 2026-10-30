---
name: repo-init
description: Bootstrap a repo's agent layer from nothing — AGENTS.md, detail tier, harness shims, and the commands table. Covers code repos, non-coding repos (docs vaults, research notes, writing) whose green check is a link or schema lint rather than a build, and empty folders that have no facts to record yet. Use only when a repo has no AGENTS.md at all. For a repo that already has one, use repo-align.
disable-model-invocation: true
version: 0.3.0
---

# Repo Init

Build the instruction layer for a repo that has none, in seven steps, ending with a green check
you can paste as evidence.

The failure this prevents: a repo where every session re-derives the same facts, and the rules
that matter live in a skill the agent never opens.

Read [`INIT.md`](INIT.md) and run it. This file is only the entry point: what the job is, what it
produces, and how to know it is done.

## First, what kind of repo is this

Three shapes reach this skill, and only one of them is the empty case. Tell them apart before
reading anything else, because "no manifest" is not the same as "no content".

```bash
ls -A | grep -v '^\.git$' | head    # any content at all?
ls *.md docs/ content/ 2>/dev/null | head
cat package.json pyproject.toml Cargo.toml go.mod Makefile 2>/dev/null | head -40
```

| Shape | Test | What it is |
| --- | --- | --- |
| **Empty** | Nothing but `.git` | No content, no facts to record |
| **Non-coding** | Files exist, but no manifest and no build | Docs vault, research notes, writing, a knowledge base |
| **Code** | A manifest, or a build/CI config | Run the seven steps normally |

A docs vault is **not** empty. It has a tree, conventions, a schema, and often a link graph — all
of them facts `AGENTS.md` should carry. Treating it as empty would throw that away and tell the
user their folder is blank when it is full of work.

## Empty folder

Every section of an `AGENTS.md` is a fact about a project, and an empty folder has none. Step 1
asks you to read the build command, the green command and the primary branch from files. There are
no files, so the honest output is not a shorter document — it is a question.

**If nothing but `.git` is there**, do not write `AGENTS.md`. Say what is missing and ask what the
folder will hold:

> This folder is empty, so there is no stack, green command or branch to record — the three things
> `AGENTS.md` is mostly made of. What will it hold: code, or something else? If code,
> `project-scaffold` picks the stack first and lays down the agent layer after, which is the order
> that avoids inventing facts.

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

## Non-coding repo

Files exist but nothing builds. This is a real repo with real facts — do not downgrade it to the
empty case, and do not pretend it has a `bun test`. It has a different green check, and finding
that check is the whole job.

### What replaces the green command

A code repo proves itself by compiling. A non-coding repo proves itself by **staying valid**, and
what "valid" means depends on what the files are:

| Content | The green check | Catches |
| --- | --- | --- |
| Markdown docs, notes, a vault | A link check — every `[x](./y.md)` resolves | Rot: renamed files, dead cross-refs |
| Structured notes (frontmatter, tags, dates) | A schema lint — required keys present, values in range | A note the tooling cannot read |
| Anything rendered (site, PDF, slides) | A build that emits the artifact, exit 0 | A broken include, a missing asset |
| Prose with a stated house style | A lint for the stated rules only (heading depth, tense, banned words) | Drift from the style the repo claims |
| Nothing checkable | **None** — and say so | Nothing; do not invent one |

Write the one that fits into the commands table, with its real invocation:

```md
| Check | Command | Passes when |
| --- | --- | --- |
| Links | `lychee --offline .` | exit 0, no broken relative link |
| Frontmatter | `python3 scripts/check_frontmatter.py` | exit 0 |
```

If the repo has no tooling at all, the honest table is one row:

```md
| Check | Command | Passes when |
| --- | --- | --- |
| None yet | — | Manual read; no mechanical check exists |
```

That row is a finding, not a failure. It tells the next session exactly how much proof exists.

### What the rest of the file becomes

| Section | Non-coding equivalent |
| --- | --- |
| Stack | What the repo *is*: Obsidian vault, docs site, research corpus, slide deck. Name the tools that read it. |
| Build command | Omit unless something renders. A vault has no build. |
| Primary branch | Same question, same answer. |
| Out-of-bounds | The paths an agent must not touch: published output, `_archive/`, other people's notes, anything with a licence. |
| Hard rules | The repo's own conventions — filename scheme, frontmatter contract, where new notes go. These bind harder here than in code, because nothing else enforces them. |

**The rules that matter most in a non-coding repo** are the ones a compiler would have caught:
where a new file goes, what its name must look like, what frontmatter it must carry, and which
files are read-only. Nothing else will fail loudly if they are broken.

**Done when** the commands table names a real check or says plainly that none exists, and the
conventions that nothing else enforces are written down as hard rules.

## What it produces

| Artifact | Tier | Holds |
| --- | --- | --- |
| `AGENTS.md` | Binding | What this repo is, hard rules, the commands table, out-of-bounds. Under ~150 lines. |
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

1. `AGENTS.md` states the repo's kind (`Kind: code` or `Kind: knowledge`), the command that
   proves it valid, and the primary branch — all copied from files, not memory.
2. Every fact collected has exactly one destination, and nothing is in two.
3. A harness opening the repo lands in `AGENTS.md` in one hop.
4. That command passes on a clean checkout, and you have pasted the line that proves it. For a
   knowledge repo that is the link check or schema lint; where none exists, the table says so and
   the rule is that no command was invented.
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
