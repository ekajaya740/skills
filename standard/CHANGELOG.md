# Changelog

All notable changes to the `standard` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- `discovery` section, routed to the new `code-discovery` skill. On in `standard` and
  `strict`, off in `lite`.

- `workflow` section, routed to the new `workflow` skill. On in `standard` and `strict`.
- The `i-have-adhd` voice is inlined as a fallback, so the style holds when that skill is absent.

### Changed

- The description names the `discovery` trigger: a structural question about unfamiliar code.
- `code-discovery` gained its install and registration path, so the section is usable on a fresh
  machine rather than only where the tool already runs.

- The `design` section now routes to skill `design` (renamed from `design-standard`), so every
  section name matches the skill that owns it.
- Corrected the count to eight routed skills.

- Description no longer claims the repo-bootstrap trigger, which belongs to `repo-init`.

- `style` (the `i-have-adhd` voice) is on by default in every profile, including `lite`, and is
  switched off only by an explicit word: `no style`, `normal mode`, `stop adhd`.
- The activation line now leads with the style state and names the opt-out.

### Fixed

- The router says ten skills, matching the ten published after `code-discovery`. The count had
  drifted from eight to nine to ten without the sentence moving.
