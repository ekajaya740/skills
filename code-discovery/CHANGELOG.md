# Changelog

All notable changes to the `code-discovery` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- `scripts/cbm-here.sh`: resolves the index for the current directory and reports
  `fresh` / `stale` / `absent` / `unknown` / `missing`, with `--ensure` to reindex and
  `--project` to print the name without hardcoding it.
- `## Install`: binary placement on `PATH`, `install --clients=<token>` registration with
  `--dry-run` first, uninstall, the duplicate-server trap, and the daemon-lock error.
- `## The rulings`: the seven rules that make the graph trustworthy, each one the fix for a
  confident wrong answer.
- The measured cheapest-first order, with the scope held constant, so the graph is not sold as
  an 8× win it does not deliver.
- The traps that make a query cost more or return a false negative, including the literal `|`,
  the 50-row pagination, and the miss footer.
- Per-directory project resolution, the mode/size trade-off, and teardown.
