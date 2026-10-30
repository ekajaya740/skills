# Phases, in detail

Each phase: what it prevents, what to do, how to know it is done, and the mistake that looks like
progress.

## Phase 1 — Sharpen

**Prevents:** building the wrong thing correctly.

The most expensive failure in software is not a bug. It is a well-built feature nobody wanted.

**Do:**

1. Read the code and docs first. Ask only about decisions, never about facts you could look up.
2. Walk the design tree: scope → success criteria → surface → naming → edge cases → failure mode.
3. One question at a time. Batch questions get batched answers, and the hard one gets skipped.
4. Write the answers where they survive: glossary for vocabulary, decision record for choices,
   issue for scope.

**Exit questions** — if any is unanswered, the phase is not done:

- What is explicitly **out** of scope?
- What does "working" look like, observably?
- Which surface — which screen, route, or command?
- What happens on the empty, error, and unauthorised path?
- What existing name, type, or module does this reuse?

**Looks like progress, isn't:** a long conversation with no written output. If nothing survives the
session, the next session re-litigates it.

## Phase 2 — Prototype (optional)

**Prevents:** arguing about something that only a running artifact can answer.

Take this phase when the question needs to be **felt**: does this state model hold up, does this
layout read, does this interaction feel right. Not for questions an ADR can settle.

**Do:** build the smallest thing that answers *one* question. Several genuinely different variants
if the question is "which". Throw the losing ones away.

**Exit:** the question is answered, the answer is written down, and the winner is referenced from
the implementation issue. The prototype is a **primary source** — keep it somewhere addressable, or
delete it and accept the answer is now prose.

**Looks like progress, isn't:** a prototype that becomes the product without re-examination. It was
written to answer a question, not to be maintained.

## Phase 3 — Split (multi-session only)

**Prevents:** one enormous branch that cannot be reviewed, reverted, or parallelised.

Skip entirely for a single-session change.

**Do:** collapse the thread into a spec — problem, solution, user stories, implementation decisions,
testing decisions, out-of-scope. Then split into **tracer bullets**: vertical slices, each one
shippable, each declaring its **blocking edges** (which other tickets must land first).

**Exit:** every ticket is independently grabbable — a person or agent can pick one up, with its
blockers either done or named.

**Looks like progress, isn't:** horizontal tickets ("all the database work", "all the UI"). They
cannot be shipped alone, so none of them is ever done.

Publishing to a tracker is a mutation. Ask before you create anything.

## Phase 4 — Plan

**Prevents:** discovering the shape of the work while doing it, at full cost.

**Do:** write scope, acceptance criteria, out-of-scope, and the files to touch. Short — half a page
is normal. The plan is scratch; the issue is the durable record.

**Exit:** every acceptance criterion is checkable by a command or a look. "Works well" is not a
criterion.

**Looks like progress, isn't:** a plan that restates the ticket. If it does not add decisions, it is
a copy.

## Phase 5 — Build

**Prevents:** an unverifiable pile of commits.

**Do:** work from the ticket. Test at the seam agreed in Phase 1 — the highest seam that still
exercises the behaviour. Commit clean: the repo's green command passes before each commit, not after
the last one.

**Exit:** the green command passes.

**Looks like progress, isn't:** a large diff with no passing check. Volume is not progress; a
verified small change is.

## Phase 6 — Review

**Prevents:** shipping something that meets the ticket and violates the repo.

Two axes, reported side by side:

- **Standards** — did it follow the repo's documented patterns, naming, and structure?
- **Spec** — did it do what the ticket asked, and only that?

On UI work, a third: does the design doc match the code?

**Exit:** every finding is either fixed or consciously accepted, with the reason stated.

**Looks like progress, isn't:** a review that only reads the diff. A UI change nobody rendered is
unreviewed.

## Phase 7 — Ship

**Prevents:** a PR that cannot be reviewed, and a claim nobody can check.

**Do:** write the body so a reader can decide without reading the diff — what changed, why it
matters, how it was verified, what the risk is. Before/after for anything visual.

**Exit:** the diff is pushed (only when instructed), the body carries evidence, and the change's
tracker state is updated.

**Looks like progress, isn't:** "tested locally" with no command and no output.

## Phase 8 — Retro

**Trigger: the user's request only.** No automatic run at the end of a task, a session, or a
worktree removal. Removing a worktree is teardown, not a retro prompt.

**Prevents:** the same correction being given twice.

**Do:** look back over the session — and the last several if you have them — and ask one question:
*where did the agent take too long to find something, or trust something out of date?* The answer is
usually a missing pointer, a stale doc, or a check that should exist.

**Propose, never self-apply.** The session that made the mistakes cannot also accept the lessons.
Present candidates; the user decides. A finding is a candidate, not a rule, and binds nothing until
accepted.

Then classify:

- **Mechanical mistake** (a rule that a script could enforce) → a check.
- **Judgement call** (no script can decide) → a written standard.
- **Navigation** (took too long to find) → a pointer.
- **Not a finding** → drop it, and say why in one line.

**Exit:** every candidate is applied or consciously dropped, and the user chose which.

**Verify the doc before you accuse it.** A candidate that quotes a rule the file does not contain
costs the user a fix for a non-problem. Read the cited lines first.

## Phase boundaries

Five options at the gap between two phases, in order:

| Option | Buys | Cost |
| --- | --- | --- |
| **Continue** | Nothing lost | Context grows |
| **Clear** | The whole window back | The *why* is gone — unrecoverable |
| **Hand off** | Portability — a file that travels | One extra file to read |
| **Subagent** | Work runs AFK, main window untouched | No steering mid-task |
| **Compact** | A summary, same harness | The summary can flatten a decision |

Rule them out in that order. Compact is the default, not the first reach.

## Related

- The route and its rules → [`SKILL.md`](SKILL.md)
- Proof a phase is done → skill `verify-change`
- Where decisions land → skill `agent-rules`
