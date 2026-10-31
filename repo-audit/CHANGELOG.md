# Changelog

All notable changes to the `repo-audit` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.1.0] - 2026-11-01

### Added

- The read-only half of what was `repo-align` 0.4.0: scope declaration, `scripts/audit.py`,
  `CHECKLIST.md`, and the ranked report. Split out because auditing a repo and changing it are
  two different permissions — a user who asks "how far off is this repo" has not agreed to an
  edit, and a fixer handed to that question edits something nobody approved.
- The kind table (`code` vs `knowledge`, and what `VERIFY-01`/`VERIFY-03` mean for each), which
  had lived in `repo-align` § What kind of repo it thinks this is.
- `scripts/check_file_size.py`, the 5,000-token-per-file gate (measured as `bytes / 4`), moved
  here from `scripts/` at the repo root so the tooling ships with a skill instead of with one
  repository. It reads the **staged** blobs in hook mode and the tree under `--all`, skips
  lockfiles, minified bundles, sourcemaps, generated code, vendored trees and binaries, and takes
  exemptions from `.file-size-ignore` with a written reason. The rule is skill `verify-change`
  § The file-size gate.

### Changed from `repo-align` 0.4.0

- `scripts/audit.py` is now five modules instead of one 49 KB file, split by section:
  `audit_model.py` (Finding, Context, the shared regex vocabulary), `audit_rules.py`,
  `audit_verify.py`, `audit_hooks.py`, `audit_structure.py`, with `audit.py` as the CLI. Output
  is byte-identical on all three repos it was checked against.
- The report escapes `|` in the Fix column instead of only the Finding column. A fix that quotes
  a `| Check | Command | Green when |` header — `VERIFY-01`'s own fix text does — split the row
  and shifted every column after it, which is how that row arrived mangled in a paste.
- This skill never edits, so it says so in four places: the opening table, § 3's handoff line,
  § What this skill never does, and the script's own docstring. A read-only tool that mentions
  editing once is read as a fixer with a caveat.
