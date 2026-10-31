---
name: standard
description: Router for the engineering standard — choose the right rule, repo, scaffold, workflow, verify, or design skill, and see which sections are on.
disable-model-invocation: true
version: 0.1.0
---

# The Standard

One entry point over eleven skills. You do not remember which one applies, so ask here.

A **profile** is a named bundle of sections. A **section** is one area of the standard
(`rules`, `discovery`, `structure`, `workflow`, `skills`, `verify`, `design`, `tests`, `tracker`, `style`) and the
unit you switch off. Nothing here is all-or-nothing.

## Activating

At the start of the first task in a session, print one line and continue:

```
Style: adhd (on). Sections: rules, structure, workflow, verify, design. Off: tests, tracker.
Change: `lite`, `strict`, `no design`, `no style`.
```

Rules for that line:

- **Once per session or task**, not per message. Re-declare only when the user changes it.
- **Only name sections that bear on this task.** A README edit does not need `design` in the list.
- **`Style` comes first and is on in every profile**, including `lite`, because it governs every
  reply. It is off only on an explicit word: `no style`, `normal mode`, `stop adhd`.
- The escape hatch is part of the line. The user should never have to ask what to type.

When `style` is off, say so once in the declaration line and write plainly after — no half-style,
no apology, no re-raising it later in the session.

The line is a declaration, not a question. Do not wait for approval. If the user says
`no design` on the next turn, drop it silently and carry on — no re-summary.

## Profiles

| Profile      | On                                                                  | Use when                                    |
| ------------ | ------------------------------------------------------------------- | ------------------------------------------- |
| **`lite`**   | `style`, `verify`                                                   | A scratch script, a throwaway, a spike.      |
| **`standard`** | `style`, `verify`, `rules`, `structure`, `workflow`, `discovery`  | Default for any repo you will keep.          |
| **`strict`** | Everything, every gate treated as blocking                          | Client work, anything with a deploy step.    |

Override one section at a time: `+ tests`, `no tracker`, `no style`. A bare section name
toggles it. There is no config file to maintain — the declaration line is the state, and the
user's last word wins.

**`style` appears in every row on purpose.** The other sections are chosen by the work; the voice
is chosen by the reader, and defaults to on.

**A gate the user switched off stays off.** Do not re-raise `tests` as a suggestion every
turn; raise it once at the end if it would have caught something real.

## The sections

Each section is owned by exactly one skill. Read that skill before acting on the section —
these summaries are orientation only.

| Section     | Skill                | Owns                                                                  | Fires when                                              |
| ----------- | -------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| `rules`     | `agent-rules`        | AGENTS.md tiers, rule ownership, when a rule is binding vs detail      | Writing or editing agent instructions, resolving a conflict |
| `discovery` | `code-discovery`     | Code-graph queries, index freshness, grep-vs-graph, per-directory projects | A structural question about unfamiliar code              |
| `structure` | `project-scaffold`   | Repo layout, stack defaults, the first green run — or, for a docs vault or writing repo, the first valid check | Starting a new project, code or not, or restructuring one |
| `workflow`  | `workflow`           | The phase route, each phase's done-criterion, context hygiene          | Deciding what to do next; a task grew past one session    |
| `skills`    | `skills-install`     | Installing, updating, relinking third-party skills; vetting a source    | "install a skill for X", a skill is missing or stale     |
| `verify`    | `verify-change`      | The evidence ladder — what counts as proof a change works; link/schema checks when there is no build | Before saying "done", "fixed", "works"                   |
| `design`    | `design`    | Craft bar, design docs, tokens, motion, UI review                      | Any visual or structural UI change                       |
| `style`     | — (this file)        | Reply shape + voice. **On by default; off only on request.**            | Every reply, unconditionally unless switched off         |
| `tests`     | `verify-change`      | What gets a test, what gets a manual check, what gets nothing          | Deciding how to pin a behaviour                          |
| `tracker`   | `agent-rules`        | Issue-first, plan-first, which mutations need the user's go-ahead      | Work that outlives the session                           |

## The repo commands

| Command | Skill | Use when |
| --- | --- | --- |
| **`repo-init`** | `repo-init` | The repo has no `AGENTS.md`, or has one that is stale or copied from a template |
| **`repo-audit`** | `repo-audit` | Anyone asks how far the repo is from the standard. Read-only, so it is safe before consent, in CI, or on a repo you do not own |
| **`repo-align`** | `repo-align` | An audit report exists and the user has named which findings to fix. Edits only those, then proves each one |

`repo-init` writes the layer from nothing. `repo-audit` inspects an existing one and writes
nothing — that is the whole reason it is separate: a report nobody has agreed to act on must not
be produced by something allowed to act. `repo-align` is the only one of the three that edits, and
it edits only named ids. None of them writes a second copy of a rule for a second harness — the
shim points at `AGENTS.md`; see skill `agent-rules` § One rule, one home.

## The reply skeleton

Every reply fills these blocks in order. Skip an empty block; never write a placeholder.

| #   | Block        | Holds                                                              |
| --- | ------------ | ------------------------------------------------------------------ |
| 1   | **Answer**   | The action, verdict, or result — command, path, or snippet first.   |
| 2   | **Why**      | Only the fact that changes what the reader does next. Three lines max. |
| 3   | **Steps**    | Numbered, one bounded action each — only when there is more than one. |
| 4   | **Evidence** | The command run and its first meaningful line; a check and its status. |
| 5   | **Next**     | One action under two minutes, actor named when it is the reader.     |

Blocks 1 and 5 must carry the answer alone: what happened, and what to do about it. Headings
appear only at three or more blocks. A file handed to the reader travels with its absolute
path on its own line, inline render or not.

The skeleton fixes the *order*. The voice inside it comes from the `i-have-adhd` skill — if it is
installed, invoke it; if it is not, the fallback below is the whole voice, and you do not need the
other skill to write well.

**The voice, inline** (use this whenever `i-have-adhd` is absent):

1. **Lead with the next action.** First line is a command, path, or snippet — not context, not a plan.
2. **Number multi-step work.** One bounded action per step; no step contains "and then" twice.
3. **End with one concrete next action** under two minutes, actor named when it is the reader.
4. **Restate position every turn.** `Step 3 of 5 done: schema updated. Next: backfill.`
5. **Specific time estimates.** "About 15 minutes if tests cover this; an afternoon if not."
6. **Matter-of-fact errors.** Cause and fix, never "uh oh" or "there seems to be a problem."
7. **No preamble, no recap, no closer.** Start with the answer; end when the answer is done.

Both shapes apply; neither overrides an engineering rule or a gate.

**The voice defaults to on and is the reader's call, not the work's.** It does not depend on
profile, repo, or task size. It turns off on `no style`, `normal mode`, or `stop adhd` — and then
the skeleton still applies, written plainly.

## Where the style yields

Four places the skeleton adapts rather than wins:

1. **A gated action stays gated.** Action-first formatting does not turn an unrequested
   mutation into a permitted one. Phrase the ask as one bounded next step.
2. **A verification report is never capped.** When completeness is the answer, list every
   finding. Group it; do not drop items to hit a count.
3. **Write-back is standing work.** Recording a trap you hit is not a tangent. Report it once,
   at the end, as its own short block.
4. **Restating position is not a recap.** `Step 2 of 5 — schema updated. Next: backfill.` is
   required. "Here is everything I just did" is not.

## When the standard and the repo disagree

The repo wins, and the disagreement is a finding. Record it once: which file states the
conflicting rule, and which one you followed. Do not silently pick. See `agent-rules` § When
two rules collide.

## Related

- Bootstrapping a repo → skill `repo-init`
- Auditing a repo that already has `AGENTS.md` → skill `repo-audit` (read-only)
- Applying an audit finding → skill `repo-align`
- The phase route → skill `workflow`
- Rule ownership and tiers → skill `agent-rules`
- New project, any stack → skill `project-scaffold`
- Installing skills from the internet → skill `skills-install`
- Deciding between the code graph and grep → skill `code-discovery`
- Proving a change works → skill `verify-change`
- UI work → skill `design`
