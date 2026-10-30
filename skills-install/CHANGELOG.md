# Changelog

All notable changes to the `skills-install` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- `install-skills.sh --project` installs into the repo's `.agents/skills/` instead of globally.

### Fixed

- `--dry-run` under `set -u` does not abort on an empty scope array.
