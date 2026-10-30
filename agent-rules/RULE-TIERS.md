# The two tiers

Why the instruction layer is split, and how to decide which tier a rule belongs to.

## The failure this fixes

A Docker rule was stated in two places: `AGENTS.md` covered the database, a workflow skill
covered the apps. Neither copy was complete. An agent read the complete-looking one, obeyed the
incomplete one, and the rule was violated three times in a single session.

The rule was not forgotten. It was **found in the weaker place**.

## The split

| Tier | Files | Loaded | Cost |
| --- | --- | --- | --- |
| **Binding** | `AGENTS.md` § Hard rules, `CODING_STANDARDS.md` § Rules that apply to every file | Every session, always | Every line, every turn |
| **Detail** | `docs/agents/*.md`, `docs/*.md`, `GLOSSARY.md`, `DESIGN.md` | On demand, when a pointer fires | One pointer line |

Binding material has **context load**: it spends tokens and attention whether or not it fires.
Detail material escapes that at the price of its pointer — but only if the pointer's wording is
sharp enough to fire at the right moment.

## The test

> **Would an agent that never opened the detail file break this rule?**

| Rule | Fresh agent breaks it? | Tier |
| --- | --- | --- |
| "Never touch production" | Yes — it has no idea which host is live | Binding |
| "Run the build before committing" | Yes — a default agent commits after an edit | Binding |
| "Components over 200 lines get split" | No — it would rarely write one | Detail |
| "Uploads go to the `assets-prod` bucket" | Only when touching uploads | Detail |
| "Use the nearest existing module's shape" | Yes — it invents shapes by default | Binding |

The test is about **default behaviour**, not about importance. A rule can be vital and still be
detail, because the agent only needs it in one branch.

## Common misclassifications

- **"It's important, so put it in AGENTS.md."** Cost, not importance, decides. Important rules
  that only fire in one area belong in that area's file.
- **"It's in a skill, so it's loaded."** A skill is loaded when its description fires. A rule
  about *how to work* in a skill is invisible to a session that never opened it. That is exactly
  how the Docker rule escaped.
- **"The detail file is always read anyway."** It is not. If it were, the pointer would be dead
  weight.

## Signals a rule is in the wrong tier

| Symptom | Move |
| --- | --- |
| A rule has been violated twice in different areas | It is detail being treated as binding, or binding with no pointer — promote it |
| `AGENTS.md` passes 150 lines | Everything below the seventh hard rule is detail |
| A detail file is read in full on every session | Its pointer is too broad; inline the always-needed part |
| A binding rule has no consequence stated | It is vaguely worded, not misclassified. Add the boundary. |

## The registry's job

The binding tier is a flat list, and flat lists rot. The registry (see
[`RULE-REGISTRY.md`](RULE-REGISTRY.md)) makes the list addressable: every binding rule has a row
naming its owner and detail file. That row is what makes duplication detectable — by a human, by a
review, or by a script.

## Standing rule

**One rule, one home.** A rule stated twice is a rule stated zero times plus a drift. Every other
mention is a pointer.
