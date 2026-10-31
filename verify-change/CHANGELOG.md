# Changelog

All notable changes to the `verify-change` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.2.0] - 2026-10-31

### Added

- `## The commit hook`: the owned rule for pre-commit wiring, which previously had no home — one
  opinion row in `project-scaffold` and a third-party `setup-pre-commit` skill that contradicted
  it. Covers what may run (cheap, never the full suite), scope (a slow check takes
  `git diff --cached`; a cheap one may read the whole index), and the difference between a hook
  that exists and a hook that runs (`core.hooksPath` is per-clone config, so the repo has to ship
  the enable command).
- The distinction that a `git ls-files` file list is the index while the file contents read are the
  working tree, so a partially staged file is checked as it sits on disk.

### Changed

- The trap log gains "the hook is in the repo and never fires" — a dead hook is indistinguishable
  from a passing one until you stage a file you know is wrong.

## [0.1.0] - 2026-10-31

### Added

- `## When there is nothing to run`: the ladder for a vault, corpus, writing or slide repo — rungs 1
  and 2 become a link check or frontmatter lint instead of a build, and the trap where rung 4 feels
  sufficient because nothing can be run.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- Initial release.
