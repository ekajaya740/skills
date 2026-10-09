---
name: conversation-distillation
description: Use when reviewing a finished conversation, session, or working period to distill durable lessons into a reusable skill, or when deciding whether a lesson is worth saving at all. Use when the user had to repeat a correction, when a workflow will recur, or when they stated a preference about how work should be done. Covers the reflection pass, skill-vs-memory, create-vs-update, the ownership rule that stops distillation overwriting hand-written skills, and the failure modes.
version: 1.0.0
---

# Conversation Distillation

Turning a finished conversation into a durable skill. The work is mostly
**judgment about what not to save** — most sessions teach nothing worth
persisting, and a store full of thin entries is worse than an empty one.

This skill is about the *reflection pass*. It assumes you have already finished
the user's actual task; distillation is a separate, quieter activity that never
competes with it.

---

## 1. The two stores, and why the distinction matters

A finished session yields two kinds of durable artifact, and confusing them is
the most common failure:

| | **Memory** | **Skill** |
|---|---|---|
| Captures | who the user is, current situation and state of operations | how to do *this class of task* for this user |
| Shape | short, situational, superseded freely | a procedure, with a trigger condition |
| Example | "deploys via `make release`, not `pnpm publish`" | "how to cut a release in this repo" |
| Ages | rewritten as the situation changes | versioned and refined |

The test: **if the user's situation changed tomorrow, would this still be
correct?** If no, it is memory. If yes, it may be a skill.

The specific trap: when a user complains about *how you handled a task*, the
lesson belongs in the **skill that governs that task**, not only in memory.
Memory records what happened; the skill is what prevents it happening again.

---

## 2. What is worth saving

A candidate must clear all four bars. Failing one is a `skip`, not a weaker
entry.

1. **Recurring** — this class of task will come up again. A one-off fix to a
   one-off problem is not a skill.
2. **Non-obvious** — a competent practitioner would not have guessed it. If
   the lesson is "read the error message", it is not a skill.
3. **Specific** — it names the actual thing: the flag, the file, the ordering,
   the constraint. "Be careful with dependencies" teaches nothing.
4. **Earned here** — it came from this machine, this codebase, this user's
   stated preference. Generic best practice belongs in a book, not a skill.

### Strong signals

- **A correction the user had to repeat.** They told you once, you did it
  again wrong. That repetition is the strongest evidence a skill is missing.
- **A workflow they will repeat.** You worked out an ordering or incantation
  that took several attempts to find.
- **A stated preference about form.** Naming, formatting, structure, tone —
  preferences are *how to do this class of task for this user*, which is
  precisely a skill's job.
- **A trap that cost real time.** A failure mode that was expensive to
  diagnose, where the diagnosis is reusable.

### Weak signals — usually `skip`

- Something you did once and it worked.
- Anything already covered by an existing skill (update it instead, or skip).
- Tool-specific trivia the tool's own docs already state.
- Facts about the current state of the world ("the API is currently down").

---

## 3. Create vs update

Prefer **update** over **create**. A store of many narrow skills is a long flat
list nobody reads; a few rich skills that each own a class of task is what
works. The target shape is **class-level skills**.

Before proposing `create`, search for a skill that already owns the area. If one
exists, the lesson belongs inside it.

**Updates rewrite the whole skill.** Carry over everything worth keeping — an
update that drops hard-won content to add one line is a net loss.

---

## 4. Ownership — never overwrite what you did not write

This is the rule that makes automated distillation safe to leave running.

Only rewrite a skill that **distillation itself created** and that carries its
ownership marker in frontmatter. Specifically, never rewrite:

- hand-written skills,
- skills shipped with a harness or package,
- skills registered at runtime,
- third-party skills installed from upstream.

A target that lacks the marker is treated as **user-owned: skip and note it.**
The cost of a skipped update is one missing lesson. The cost of a wrong update
is destroying work someone else maintains — so the asymmetry is absolute.

Ownership markers are **chosen at write time**. A skill distilled before the
marker existed has none, and will be treated as user-owned forever unless it is
recreated or marked by hand. Expect this and do not "fix" it by force.

---

## 5. The reflection pass

Run it **after** the turn, on your own time, never interleaved with the user's
work. Full prompt template in `reference/prompt.md`.

The loop:

1. **Collect** — gather the human messages since the last checkpoint. Agent
   output is not evidence about the user's preferences; their messages are.
2. **Threshold** — wait for enough new material to be worth a pass. Reflecting
   after every turn produces noise and burns tokens.
3. **Inspect before proposing** — view the current content of any skill you
   might update. Proposing a replacement for something you have not read is how
   content gets silently dropped.
4. **Propose exactly one of**: `skip`, `create`, or `update`.
5. **Validate** — the name is kebab-case, description and content are non-empty,
   and an `update` target exists and carries the marker.
6. **Advance the checkpoint regardless of outcome** — so the next pass covers
   only genuinely new messages and does not re-litigate the same ground.

### Skip is the expected outcome

Silence is the common case. A reflection pass that produces something every
time is not reflecting, it is generating. If most passes do not end in `skip`,
the threshold is too low or the bars in §2 are being applied loosely.

---

## 6. Failure modes

- **Distilling the task instead of the lesson.** Recording "fixed the login
  bug" rather than the reusable procedure that found it.
- **Confident wrongness from thin evidence.** One instance of a pattern is not
  a pattern. If the user mentioned something once in passing, it is not a rule.
- **Duplicating an existing skill** because the search was skipped.
- **Restating documentation.** If upstream docs say it, link the docs.
- **Leaking session detail.** Skills are durable and often shared. Do not embed
  credentials, customer names, private paths, or anything the user said in
  confidence. Write the *lesson*, not the transcript.
- **Whole-file rewrites that lose content.** See §3.
- **Reflecting on agent output as if it were user intent.**

---

## 7. Writing the skill

- **Frontmatter** — `name` must match the directory; `description` must state
  both *what it covers* and *when to use it*, because the description is what
  the model sees when choosing whether to load the skill. `version` is SemVer.
- **Trigger in the description.** A skill nobody loads is a skill that does not
  exist. Enumerate the situations, not just the topic.
- **Procedure over prose.** Numbered steps, tables, decision rules. The reader
  is an agent deciding what to do next.
- **Include the counter-case.** What looks like a match but is not; what to skip.
- **Keep it short enough to be read.** If it needs sections a reader will skip,
  split it or cut it.

---

## Reference

- `reference/prompt.md` — the reflection prompt template.
- `reference/rubric.md` — the §2 bars as a scoring checklist.
