# Changelog

All notable changes to the `repo-audit` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.1.2] - 2026-11-01

### Fixed

- `STRUCT-09` still failed a **pure pin**. 0.1.1 stopped counting the gitlink as a leaked file, but
  the lock requirement was untouched: a repo whose store *is* the submodule, with no
  `skills-lock.json`, still reported "skills-lock.json is neither tracked nor ignored" and blocked
  strict. A submodule pointer names an exact commit, which is what a lock is for, so a pin now
  satisfies the lock requirement. Three policies are coherent — lock tracked, store and lock both
  machine-local, store pinned — and only committed store *files* with no record are drift. Found by
  building the case instead of assuming: `/tmp/pin` with `.agents/skills` and no lock.
- `VERIFY-03` had a right boundary but no left one, so a one-word row matched inside a longer
  command: documented `install` was satisfied by `bun install`, and `audit.py` by
  `repo-audit/scripts/audit.py`. Both ends are bounded now.
- Workflow **comments** counted as execution: `# TODO: bun run build` satisfied the check with no
  step running it. Whole-line comments are dropped before matching. Mid-line `#` is left alone,
  because it is as likely to be inside a quoted string, and a false "CI never runs" is the worse
  error.
- `pinned` and `tracked` each ran `git ls-files -s`; one call now feeds both.

## [0.1.1] - 2026-11-01

### Fixed

- `STRUCT-09` reported `drift` on a repo that pins the standard as a submodule. `git ls-files`
  lists a gitlink, so `.agents/skills -> ekajaya740/skills` counted as "1 file(s) under .agents/ are
  tracked" — the one correct way to keep the store out of a repo, marked as the failure. Mode
  `160000` entries are now separated from real files and named in the detail line; a leaked file
  inside the store still reports.
- `VERIFY-03` matched only the first word of each documented command, so a workflow containing
  `bun` anywhere satisfied every `bun …` row. `bun run build` passed on a CI that only ran
  `bun install --frozen-lockfile`. Now the whole command is matched with a right boundary:
  `bun run build:ci` and `bun install` do not satisfy it, `bun run build --filter=x` does.
  Whitespace is normalised, so a wrapped or re-spaced command still matches.

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
