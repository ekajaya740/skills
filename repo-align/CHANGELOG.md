# Changelog

All notable changes to the `repo-align` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

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
