# Changelog

All notable changes to the `repo-init` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.5.0] - 2026-10-31

### Added

- `INIT.md` § 1b: branch topology, asked rather than inferred. Step 1 can read branch *names*
  from `git branch -r`; it cannot read which one mirrors production, so the question is put to
  the user with the reasoning attached — deployments fire per target branch, a permanent branch
  is a review boundary, and release automation keys on the name. Records the answers as one
  table plus one binding line in `AGENTS.md`.

## [0.4.0] - 2026-10-31

### Added

- `INIT.md` § 0 and `SKILL.md` § Step 0: ask whether the project uses `ekajaya740/dotfiles`
  before reading anything else. The entry point carries the gate too, because an agent loads
  `SKILL.md` first and would otherwise reach the question only from the deep file; the step count
  is now eight everywhere it is stated.
  The dotfiles are tuned for omp (omp-jev routing, 9router model aliases, the `claude/` and `jev/`
  deploy scripts), so a repo on another harness inherits wiring it never reads. A `yes` turns the
  harness shims into a pointer at the machine layer; a `no` means they are written by hand. The
  question has to be asked: `~/dotfiles` existing on the machine is not evidence the repo uses it.

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
