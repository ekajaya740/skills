# Changelog

All notable changes to the `repo-align` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.5.0] - 2026-11-01

### Changed

- **The audit moved out.** `scripts/audit.py` and `CHECKLIST.md` now belong to skill `repo-audit`,
  which writes nothing. Auditing and editing were one permission here: a user asking "how far off
  is this repo" got a tool allowed to edit it, and the checks could not be run read-only in CI.
  This skill keeps the editing half — § 1 takes the ids the report produced, § 2 applies them, § 3
  proves each one.
- § 2 no longer restates check logic; it points at `repo-audit/CHECKLIST.md` as the owner. Two
  copies of a fix instruction drift exactly like two copies of a rule.
- The scope declaration and the repo-kind table (`code` vs `knowledge`) moved to `repo-audit`
  § 1, because both are about reading the repo, and both were being repeated here.

### Added

- § 0 — refresh the installed skills before aligning a repo. A repo brought in line with an older
  copy of the standard is aligned to a standard nobody is reading. Covers `--dry-run` before
  `--update`, consent before `--yes`, no lock means nothing to update, and the relink-plus-restart
  step that makes a new skill visible to a harness.
- Two constraints on applying: one id per edit, and move rules before deleting the file that held
  them. The second is the `RULE-SHIM-01` bug of 0.4.0 stated as a rule instead of a footnote.

### Fixed

- The description named auditing, so the skill fired on inspection requests it must not act on.

## [0.4.0] - 2026-10-31

### Fixed

- `RULE-SHIM-01` told the reader to "replace with `@AGENTS.md` or a one-line pointer" and said
  nothing about the rules being replaced. `SHIM-01`/`SHIM-02` in `scripts/audit.py` carried the same
  fix text. On a repo whose `CLAUDE.md` is the only place a rule lives, that instruction deletes the
  rule and leaves a shim that resolves, so the next audit reports `ok`. The fix now extracts each
  rule, places it per `RULE-TIER-01`, drops the no-ops per `RULE-NOOP-01`, and replaces the shim only
  after every rule has a destination.

## [0.3.0] - 2026-10-31

### Added

- `HOOK-01` and `HOOK-02` in `scripts/audit.py`, reported under `verify`, plus a `hook` section in
  `CHECKLIST.md`. The standard now had a rule about pre-commit hooks (skill `verify-change`
  § The commit hook) but nothing that checked compliance, so the rule could not drift into a
  finding.
- `HOOK-01` reads only `pre-commit` and `commit-msg`, and strips comment lines before matching. A
  suite in `pre-push` is legitimate, and a hook that *explains* why it avoids the suite must not be
  read as running one.
- `HOOK-02` separates shipped wiring from local wiring: a hook ignored by a deny-by-default
  `.gitignore`, or left uncommitted, is `drift`; a committed hook that this clone does not run is
  `manual`, because `core.hooksPath` is per-clone config and a fresh CI checkout never has it.
- `BRANCH-01` in `scripts/audit.py`, plus a `structure` row in `CHECKLIST.md`: a repo with more
  than one branch must state what each one is for. `missing` when no `| Branch |` table exists in
  `AGENTS.md` or any `docs/agents/*.md`; `ok` when one does, naming the file that owns it. A
  single-branch repo is `ok` by definition. Found by auditing PROFILL, which keeps its topology in
  `merge-policy.md` — the check scans every area doc, because a second copy in `version-control.md`
  would be the drift the standard forbids.

### Fixed

- `HOOK-02` compares resolved paths instead of strings, so `.githooks`, `.githooks/` and the
  absolute form all count as wired. Stripping `./` had eaten the leading dot of the directory name,
  which pinned the check at `manual` for every correctly wired clone.
- `HOOK-02` accepts Husky's shim layout. Husky sets `core.hooksPath=.husky/_`, where `_/pre-commit`
  sources `../pre-commit`; a shim directory directly inside the hooks directory is now `ok`, not
  `manual`. Found by auditing a real Husky repo with the check.

## [0.2.0] - 2026-10-31

### Added

- `Kind: code` / `Kind: knowledge` is read from `AGENTS.md` and printed in the audit header.
  Declared beats detected: the filesystem cannot tell a docs-heavy code repo from a vault, and
  guessing alone silently dropped checks a code repo should run.

### Fixed

- `documented_commands` counted any row with a backticked second cell, so an AGENTS.md *index*
  table (`| Writing code | `CODING_STANDARDS.md` |`) satisfied VERIFY-01 and `--run` tried to
  execute a markdown filename. Now anchored to a commands table or a row stating its own
  green condition.
- `VERIFY-03` is `n/a` when nothing is documented for CI to run, for any repo kind — the gap is
  already VERIFY-01's finding, not a second one.

## [0.1.0] - 2026-10-31

### Added

- `Context.is_empty` and `Context.is_non_coding`: content without a manifest is a real repo, not an
  empty folder.

### Fixed

- `VERIFY-01` accepts `Passes when` as well as `Green when`, and treats an explicit `None yet` row
  as `manual` rather than `missing` — a repo with nothing to check is being honest, not failing.
- `VERIFY-03` no longer demands a CI workflow from a repo with no build. A badge that checks
  nothing reads as proof, which is worse than no badge.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Added

- `scripts/audit.py`: the mechanical checks as a command instead of prose. Checks across
  `rules`, `structure`, `verify`, and `design`, with `--strict`, `--json`, `--run`, and
  `--section`. Deterministic, so two runs on one repo agree.
- `manual` as a distinct verdict. Checks needing judgement are printed rather than silently
  passed, so a clean run is never mistaken for full alignment.
- Owner-plus-pointer exemption in `RULE-DUP-01`: a rule restated in a doc `AGENTS.md` links to
  is the intended pattern, not drift. Only an unlinked restatement is a second source of truth.

- Three new structure checks: the pinned store exists, `.agents/` is ignored while the lock is
  tracked, and a throwaway clone can restore the set.

### Fixed

- `RULE-CAP-01` does not treat its cap of 7 as a law. A flat cap contradicts the standard this
  skill enforces: `RULE-TIER-01` says a rule that governs *how to work* binds every session, so a
  repo whose rules each pass that test can legitimately exceed 7. The Docker-rule regression cited in
  `agent-rules` is the case the cap was meant to catch — a rule demoted out of the binding tier and
  then missed — and a count is the wrong instrument for it, because demoting to satisfy the count is
  the regression. A repo may declare `rules-budget: N` anywhere in `AGENTS.md`; the check reports
  the declared budget alongside the count, and still drifts when the count exceeds it. Repos that
  declare nothing keep the default of 7, unchanged.
- A declared budget is only honoured when the repo also documents the admission test it claims to
  apply, **in a doc other than `AGENTS.md`** — the decisive question ("would an agent that never
  opened the detail file break the rule?") or a tier table naming a binding and a detail tier. A
  number with no test behind it is a mute button: any agent could raise it to silence the check, and
  the file that declares the budget supplying its own justification is the same mute button one
  sentence longer. When the test is missing the check drifts and names what to write; when it passes,
  the ok line names the file the test came from.

- `RULE-DUP-01` resolves links relative to the doc that holds them. A detail doc that pointed at
  `./worktree.md` and one that pointed at `docs/agents/worktree.md` were the same file but compared
  unequal, so the owner-plus-pointer pattern was reported as duplication. It now exempts a second
  site whose link resolves to the same doc `AGENTS.md` links, and reads whole blocks on both sides.
- `STRUCT-09` accepts an ignored lock as a valid policy. It demanded `skills-lock.json` be committed
  and failed a repo that deliberately ignores the store and its lock together — a coherent choice.
  Only a lock that is neither tracked nor ignored is drift now, and the ok line says which policy
  the repo chose.

- `RULE-DUP-01` reads whole rule blocks. Wrapped bullets keep their link on the last line, so a
  line-by-line read reported the repo's own pointer pattern as duplication.
- `STRUCT-02` and `STRUCT-04` prune skipped directories during the walk. Filtering after
  `rglob("*")` walked `node_modules` and took 44s on a real repo; it now takes 6s. Bundler
  output (`.wrangler/`, `storybook-static/`, `.astro/`) is skipped too — that is vendored
  third-party code, and reading it reported library internals as the repo's own env vars.
- `STRUCT-04` does not report vars the repo already provides: those set in a committed
  `wrangler.jsonc`/`turbo.json`/compose file or by a `scripts/*.sh`, those with a `||`/`??`
  fallback at the read site, those named only in a comment, and those read only by tests.
  On a real repo that turned 6 findings into 2 — the remaining two are genuine.
- `DESIGN-02` was filed under `structure`; it now sits in `design`, and `--section design`
  is accepted instead of exiting 2.
- The report's counts reconcile. Section headers and the final line both name every status
  (`drift`, `missing`, `manual`, `ok`, `n/a`) and their totals equal the number of checks run;
  before, 7 of 22 checks were silently uncounted.
