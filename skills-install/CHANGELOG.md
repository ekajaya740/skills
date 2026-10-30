# Changelog

All notable changes to the `skills-install` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.2.1] - 2026-10-31

### Fixed

- The no-terminal error told the caller to "re-run with --yes", which is exactly
  the move that defeats the gate. It now says the install needs a human, and that
  `--yes` is for sources the user has already approved.
- `--update` prompted before printing a single source: the jev credit and the whole
  lock file came after the question. It now lists every source and count from
  `.skill-lock.json` first, then asks.

## [0.2.0] - 2026-10-31

### Added

- Step 0: get consent before fetching anything. A skill is instructions the agent
  follows, so the source, author, licence and what it runs go to the user first, and
  an instruction to install one skill is not consent for a fifteen-source list.
- `-y` is described as a decision, not a shortcut: only after the user has agreed.

## [0.1.0] - 2026-10-31

### Added

- Attribution as a required step of an install: `author` and `license` in `skills.json`, a
  generated `ATTRIBUTION.md`, and a credit line printed at install time.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- `install-skills.sh --project` installs into the repo's `.agents/skills/` instead of globally.

### Fixed

- `--dry-run` under `set -u` does not abort on an empty scope array.
