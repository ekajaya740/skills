---
name: agent-rules
description: Writing and maintaining the agent instruction layer — AGENTS.md tiers, one-rule-one-home ownership, resolving a rule that drifted or collided, and the issue-first/plan-first tracker gates.
disable-model-invocation: true
version: 0.0.1
---

# Agent Rules

How the instruction layer is written and kept honest. Read this before adding a rule, and when
two rules disagree.

The problem it solves: a rule stated twice is a rule stated *zero* times plus a drift. The two
copies diverge, a reader finds the incomplete one, and the rule is violated — often by an agent
that would have obeyed either copy alone.

## The tier test

Every rule has exactly one home. Which tier it belongs to is decided by one question:

> **Would an agent that never opened the detail file break this rule?**

- **Yes → binding tier.** `AGENTS.md` § Hard rules, and `CODING_STANDARDS.md` § Rules that apply
  to every file. Loaded every session, so a line here costs on every turn.
- **No → detail tier.** `docs/agents/<area>.md` or the nearest `DESIGN.md`. Reached only when
  its pointer fires.

A rule that governs *how to work* is binding. A rule that governs *how to do one task* may be
detail. The test is about the agent's default behaviour, not about how important the rule feels.

Full reasoning, including why a rule that matters but sits in a skill gets missed:
[`RULE-TIERS.md`](RULE-TIERS.md).

## One rule, one home

1. **Find the owner.** If the rule already exists, extend that owner's statement. Do not write a
   second copy.
2. **State it once**, at the place a reader would look for it.
3. **Point, don't restate.** Every other mention is a link phrased so it reads correctly where it
   sits: `the apps run on the host — see environment.md § Docker`.
4. **Name the consequence.** A prohibition with no concrete boundary ("never touch production")
   is decoration. Say which host, which path, which command.

## Adding a rule

| Step | Ask | If the answer is no |
| --- | --- | --- |
| 1 | Does an existing rule already cover this? | Extend that rule. |
| 2 | Would a fresh agent break this without being told? | It is a no-op. Delete it. |
| 3 | Can it be stated as a positive behaviour? | Try harder; see § Negation below. |
| 4 | Does it carry a concrete boundary? | Add the boundary, or it will not bind. |
| 5 | Is it already stated in another file? | You found a duplicate. Fix the duplicate. |

A rule earns its cost only when a competent default would get it wrong. "Be thorough", "write
clean code", "follow best practices" fail step 2 and are noise.

**Cap the binding tier at about seven rules.** Past that, rules trade against each other and none
dominate. If you have ten, four are detail.

## Negation

Steering by prohibition drags the forbidden behaviour into context and makes it *more* available.
Prompt the target behaviour instead: "write one-line comments explaining the why" beats "don't
write long comments".

A prohibition earns its place only as a hard guardrail you cannot phrase positively — and even
then, pair it with the positive target so attention lands on what to do.

## When two rules collide

The repo's own files outrank this skill, and a generic instruction outranks a stylistic one.
Beyond that:

1. **Safety, then correctness, then policy, then style.** A style rule never turns a blocked
   action into a permitted one.
2. **The more specific owner wins.** A rule about `packages/ui` beats a repo-wide rule on the same
   subject.
3. **State the collision once**, in the reply, naming both files. Then obey the winner. Silence
   looks like agreement and the drift survives the session.
4. **Write it down** if it will recur: the loser becomes a pointer or gets deleted.

## Keeping the registry

The registry is the index of binding rules: rule → one-line statement → owner → detail file.
It is a *quote*, never a second statement of the rule. Full format and maintenance procedure:
[`RULE-REGISTRY.md`](RULE-REGISTRY.md).

Regenerate or spot-check it whenever you add a binding rule. An unregistered rule is invisible to
the next reader and to any duplication check.

## Tracker gates

When the section `tracker` is on, work that outlives the session moves **issue → plan → code**:

1. **Issue first.** No implementing code, no branch, no plan file until the issue exists. An issue
   written from a finished diff is a record, not a scope — it cannot be reviewed or declined.
2. **Plan before code.** Scope or approach changes land in a plan file before the implementing
   code.
3. **Never mutate the tracker unprompted.** No creating, editing, closing, commenting, or moving
   issues and PRs without the user's go-ahead in this conversation. Filing is a mutation: ask,
   then file.
4. **A runbook is an issue, not a plan.** Steps only a human can execute belong where they survive
   the branch — usually an issue whose body *is* the runbook.

With `tracker` off, the same discipline collapses to a todo list in the reply and no mutations at
all.

## Related

- The tier reasoning → [`RULE-TIERS.md`](RULE-TIERS.md)
- The registry format → [`RULE-REGISTRY.md`](RULE-REGISTRY.md)
- Writing a skill or doc an agent consumes → skill `writing-for-agents` (if installed)
- Bootstrapping the layer → skill `repo-init`
