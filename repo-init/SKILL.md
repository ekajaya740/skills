---
name: repo-init
description: Bootstrap a repo's agent layer from nothing — AGENTS.md, detail tier, harness shims, and the green-command table. Use only when a repo has no AGENTS.md at all. For a repo that already has one, use repo-align.
disable-model-invocation: true
version: 0.0.1
---

# Repo Init

Build the instruction layer for a repo that has none, in seven steps, ending with a green check
you can paste as evidence.

The failure this prevents: a repo where every session re-derives the same facts, and the rules
that matter live in a skill the agent never opens.

Read [`INIT.md`](INIT.md) and run it. This file is only the entry point: what the job is, what it
produces, and how to know it is done.

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
