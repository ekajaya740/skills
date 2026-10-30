# Changelog

All notable changes to the `repo-init` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.3.0] - 2026-10-31

### Changed

- Done-when names `Kind`, the proving command, and the branch — and accepts a knowledge repo
  whose check is a link or schema lint, or an explicit `None yet` row with nothing invented.
- `TEMPLATE-AGENTS.md` carries the `Kind:` line the audit reads.

## [0.2.0] - 2026-10-31

### Added

- `SKILL.md` § Stop here if the folder is empty: an empty folder has no build command, green
  command or branch, so the honest output is a question, not a shorter document. Says when to
  hand off to `project-scaffold`, and gives a partial `AGENTS.md` that lists what is not yet
  known instead of filling it with plausible defaults.

### Fixed

- `INIT.md` and `SKILLS.md` no longer pass `-y` to `npx skills@latest add`. It answered the
  consent question on the user's behalf, contradicting `skills-install` 0.2.x.

## [0.1.0] - 2026-10-31

### Added

- `SKILLS.md` § Attribution: a pinned skill keeps its upstream licence, so the repo names the
  author by reference rather than vendoring a copy.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- Added step 6: pin the project's skill store into `.agents/skills/` with a committed
  `skills-lock.json`, and a new [`SKILLS.md`](SKILLS.md) reference with the full pin set.
