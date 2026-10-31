# Changelog

All notable changes to the `project-scaffold` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.2.1] - 2026-10-31

### Changed

- `DEFAULTS.md` § Tooling: the pre-commit row said "optional, and only lint + format", which
  competed with the third-party `setup-pre-commit` skill's "lint-staged + typecheck + test" — two
  answers, no owner. The row now names the repo's one gate as fair game and points at skill
  `verify-change` § The commit hook for scope, so the detail lives in exactly one place.

## [0.2.0] - 2026-10-31

### Added

- § 3 asks whether the project uses `ekajaya740/dotfiles` before the agent layer is laid down.
  They are tuned for omp, so a `yes` makes the harness shims a pointer at the machine layer
  (`bash ~/dotfiles/bootstrap.sh`) and a `no` means writing `CLAUDE.md` and `.cursor/rules` by
  hand. Recorded as one line under the stack section, either way.

## [0.1.0] - 2026-10-31

### Added

- `targets/agent-only.md` § Non-code repos: the tree, the one real check (link/schema/render), and
  the four conventions that must be hard rules because no compiler enforces them.
- A classify row for docs vaults, research corpora and writing projects. No deployable is not a
  lesser project, and a notes repo does not get a `package.json` to satisfy a template.

### Changed

- § 2 is "before the content", not "before the code".

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- The agent layer now includes the project-local skill store and its lock file.
