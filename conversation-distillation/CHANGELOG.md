# Changelog

All notable changes to the `conversation-distillation` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [1.0.0] - 2026-10-09

First release. The skill documents the reflection pass that runs after a
working session ends, and the judgment required to decide what — if anything —
should be persisted from it.

### Added

- `SKILL.md` — the memory-vs-skill distinction, the four bars a candidate must
  clear, create-vs-update precedence, the ownership rule that prevents
  overwriting hand-written skills, the reflection loop, failure modes, and
  guidance on writing the resulting skill.
- `reference/prompt.md` — the reflection prompt template, with notes on why the
  rewritable list is explicit and why `skip` is named as the expected outcome.
- `reference/rubric.md` — the four bars as a checklist, signal-strength table,
  red flags, and a create-vs-update decision tree.
