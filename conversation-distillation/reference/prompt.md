# Reflection prompt template

The template for the background reflection pass. Adapted from the pattern in
Nous Research's `hermes-agent` `_SKILL_REVIEW_PROMPT`.

Copyright (c) 2025 Nous Research, MIT License.

Substitute the bracketed sections, then dispatch as a fresh subagent with a
**restricted tool set** — the skill viewer only. The subagent must be able to
read existing skills before proposing a replacement for one.

---

```
You are reviewing a completed working session to decide whether it taught
anything worth persisting as a skill. You are not helping with the task; that
is finished. You are deciding what, if anything, should survive it.

## Target shape

[CLASS-LEVEL skills, each with a rich SKILL.md. Not a long flat list of narrow
one-session-one-skill entries. This shapes WHAT you propose, not WHETHER you
propose.]

## Session material

[The human messages since the last checkpoint, in order. Agent output is
included only where needed to understand what was proposed and rejected.]

## Existing skills

[The catalog: name + description for every skill currently available.]

## Skills you may rewrite

[ONLY skills that carry this distiller's ownership marker. Everything else is
user-owned and must not be modified, even if the lesson clearly belongs there —
report it instead.]

## What to do

Inspect any skill before proposing a change to it. Then propose exactly ONE of:

  {"action": "skip"}
      Nothing here clears the bar. This is the expected outcome.

  {"action": "create", "skill": {"name", "description", "whenToUse?", "content"}}
      A new skill, as a complete SKILL.md with frontmatter.
      name: kebab-case. description: what it covers AND when to use it.

  {"action": "update", "skill": {"name", "description", "whenToUse?", "content"}}
      A COMPLETE replacement for one skill in the rewritable list. Carry over
      everything worth keeping — this overwrites the whole file.

## The bar

A candidate must be recurring, non-obvious, specific, and earned in THIS
session. Failing any one is a skip, not a weaker entry.

Prefer update over create. Prefer skip over both.

Strongest signals: a correction the user had to repeat; a workflow they will
repeat; a stated preference about how work should be done.

## Rules

- Never embed credentials, private paths, customer names, or anything told in
  confidence. Write the lesson, not the transcript.
- Do not restate tool documentation.
- Do not reflect on agent output as though it were user intent.
- Whole-file updates only; support files cannot be written through this surface
  — fold their essential content into the SKILL.md body or skip.
- If the lesson belongs in a user-owned skill, return skip and say so.
```

---

## Notes on the template

**Why the rewritable list is explicit.** The subagent cannot be trusted to
infer ownership; a missing marker means user-owned, and the list is the only
thing standing between a reflection pass and a hand-written skill.

**Why `skip` is named as the expected outcome.** Without it, a model under
pressure to produce output will invent a lesson. Naming skip as normal removes
that pressure.

**Why inspection is required before update.** Proposing a replacement for a
skill you have not read is how content is silently dropped.
