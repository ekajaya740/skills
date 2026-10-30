---
name: workflow
description: The route work takes, idea to shipped — sharpen, prototype, split, plan, build, review, ship, retro — with the done-criterion for each phase and which skill to run at each. Use when deciding what to do next, when a request is underspecified, when a task has grown past one session, or when work was finished but not proven.
disable-model-invocation: true
version: 0.1.0
---

# Workflow

One route, eight phases. The question this answers: **what do I do next, and how do I know this
phase is finished?**

Phases are ordered. Skip one only when it has genuinely nothing to do — not because it feels slow.

| # | Phase | Produces | Done when |
| --- | --- | --- | --- |
| 1 | **Sharpen** | Decisions, vocabulary, recorded constraints | No question on the design tree is silently assumed |
| 2 | **Prototype** *(optional)* | A running answer to one design question | The question is settled and the answer is folded back into the thread |
| 3 | **Split** *(multi-session only)* | Spec + tickets with blocking edges | Every ticket is independently grabbable |
| 4 | **Plan** | A written scope before the work exists | Scope, criteria, out-of-scope, and files are written down |
| 5 | **Build** | Commits, or the changed files | The repo's green command passes — or, with no build, its check does (link/schema lint) |
| 6 | **Review** | Standards + spec findings | Every finding is fixed or consciously accepted |
| 7 | **Ship** | A PR with evidence | The diff is pushed and the PR body carries proof |
| 8 | **Retro** *(on request only)* | Steering-improvement candidates | Every candidate is applied or dropped, by the user |

Full per-phase detail, including the exit questions and the failure each phase prevents:
[`PHASES.md`](PHASES.md).

## The rules that make the route hold

1. **Never guess a specification.** Underspecified scope, criteria, naming, or surface is a Phase 1
   trigger, not a licence to pick a plausible default. Ask the questions; an assumption nobody
   confirmed is not a decision.
2. **Facts are the agent's job; decisions are the user's.** Look up what the code says. Ask what
   the human wants.
3. **Plan before the work.** A scope or approach change lands in writing before the work that implements it — code, prose, or a restructure.
4. **Proof before "done".** Every completion claim names the layer it was verified at — see skill
   `verify-change`.
5. **Retro is manual, and proposes only.** Phase 8 runs **on the user's request** — never
   automatically at the end of a task, a session, or a worktree teardown. The session that made
   the mistakes cannot accept the lessons either: findings go to the user, who decides.

## Which skill runs at each phase

| Phase | If these skills are installed | Otherwise |
| --- | --- | --- |
| Sharpen | `grilling` / `grill-with-docs` / `domain-modeling` | Run the interview directly: one question at a time, decisions first |
| Prototype | `prototype` | Throwaway code in a scratch directory; keep the answer, delete the code |
| Split | `to-spec` → `to-tickets` | Write a spec section in the issue, then one issue per slice |
| Plan | — | Write the scope into the issue or a plan file |
| Build | `implement` → `tdd` | Drive from the spec; test at the seam you agreed in Phase 1 |
| Review | `code-review` | Two axes yourself: did it meet the spec, did it follow the repo's standards |
| Ship | `pr` | Write the PR body by hand — what, why, evidence, risk |
| Retro *(request only)* | `retro` | List candidates in the reply; apply none |

**This table is a router, not a dependency.** With none of the right-hand skills installed, the
route still runs. What you lose is the packaging, not the discipline.

## Routing by situation

The eight phases are the default. Three other shapes are legitimate:

- **Something is broken** → skip to a diagnosis loop: one command that goes red on *this* bug, then
  fix, then a regression test. Do not theorise until the loop exists. Rejoin at Phase 6.
- **The way forward is not visible** (greenfield, foggy, too big for one session) → decide first,
  build later. Resolve the open questions one at a time, record each as a decision, then rejoin at
  Phase 3.
- **A one-line fix with an obvious answer** → Phases 1–4 collapse into one sentence in your reply.
  Run 5–7. Say which phases you skipped and why.

## Context hygiene

Keep Phases 1–3 in **one unbroken context window** — the sharpening, spec, and tickets build on the
same thinking. Each Build run then starts fresh from its ticket.

At a phase boundary, you have five options, in this order of preference: **continue** (costs
nothing), **clear** (context is disposable), **hand off** (something must travel: new harness,
directory, or person), **subagent** (work can run AFK), **compact** (relevant context, same
harness, and you must stay in the loop). Compact is the default, not the first reach.

The failure mode is compacting mid-phase: the summary flattens a decision, and the next session is
confidently wrong about it.

## When to skip the route entirely

- A question with a factual answer. Answer it.
- A README typo. Fix it.
- The user asked for one specific edit. Do that edit.

Declaring eight phases for a one-line change is the same failure as shipping without them — the
process stops meaning anything.

## Related

- Every phase's exit criteria and failure mode → [`PHASES.md`](PHASES.md)
- Proving a phase's output → skill `verify-change`
- Where decisions and rules get written down → skill `agent-rules`
- Bootstrapping the layer a repo needs first → skill `repo-init`
