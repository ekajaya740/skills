# Rubric

The four bars as a checklist. Score every candidate before proposing it.

## The four bars

| Bar | Question | Fail means |
|---|---|---|
| **Recurring** | Will this class of task come up again? | skip — one-off fix to a one-off problem |
| **Non-obvious** | Would a competent practitioner have guessed it? | skip — it is generic best practice |
| **Specific** | Does it name the flag, file, ordering, or constraint? | skip — too vague to act on |
| **Earned here** | Did it come from this machine, codebase, or user's stated preference? | skip — belongs in a book |

All four, or skip. There is no partial credit.

## Signal strength

| Signal | Strength | Why |
|---|---|---|
| User repeated a correction | **Strongest** | The repetition is direct evidence a skill was missing |
| Workflow the user will repeat | Strong | Ordering/incantation found by trial is expensive to rediscover |
| Stated preference about form | Strong | Preferences are *how to do this class of task for this user* |
| Trap that cost real time | Strong | Reusable diagnosis |
| Something done once that worked | Weak | No evidence of recurrence |
| Already in an existing skill | Weak | Update that skill instead |
| Stated in tool documentation | Weak | Link the docs |
| Current state of the world | Weak | Not durable |

## Red flags — any one means skip

- **Task, not lesson.** "Fixed the login bug" instead of the procedure that found it.
- **One instance as a pattern.** Mentioned once in passing ≠ a rule.
- **Existing skill skipped.** The area is already owned.
- **Documentation restated.** Upstream already says it.
- **Session detail leaked.** Credentials, customer names, private paths, confidences.
- **Whole-file rewrite that loses content.** Carrying over is mandatory.
- **Agent output mistaken for user intent.** The agent's own reasoning is not evidence about the user.

## Create vs update

```
Does a skill already own this area?
├─ yes → update it (rewrite whole file, carry over everything worth keeping)
│         └─ is it marked as distiller-owned?
│              ├─ yes → propose update
│              └─ no  → skip; report that the lesson belongs in a user-owned skill
└─ no  → is the lesson class-level, not session-level?
          ├─ yes → propose create
          └─ no  → skip
```

## Final check before returning a proposal

- [ ] All four bars cleared, explicitly.
- [ ] `name` is kebab-case and does not collide with an existing skill.
- [ ] `description` states what it covers **and** when to use it.
- [ ] For `update`: target is in the rewritable list, and its current content
      was read first.
- [ ] Nothing confidential is embedded.
- [ ] Content is a procedure the reader can act on, not prose about the topic.
