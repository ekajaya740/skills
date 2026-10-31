# Changelog

All notable changes to the `workflow` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [0.2.0] - 2026-10-31

### Added

- `BRANCHES.md`: the permanent-versus-working branch topology, why a repo needs a permanent
  branch at all (deployments fire per target branch; a permanent branch is also a review
  boundary, and it is what release automation and branch protection key on), the four questions
  to ask the user, and the shape of the topology record. States explicitly that one permanent
  branch is a complete answer — the count is not the defect, an unstated purpose is.
- Rule 6 on `SKILL.md`: know where the work lands before starting it; never author on a permanent
  branch.
- `BRANCHES.md` § Permanent branches are never merged into each other, and a `Syncs from` column in
  the record table. Two permanent branches that both carry work have diverged, so a merge between
  them is conflict resolution that deletes the target's own work — measured on PROFILL, where `seo`
  has never taken a commit from `beta-master` and nothing reaches `master` by merging `seo` down.
  The record can therefore never say "either way".
- The record table carries permanent branches only. Working branches are created per issue and per
  worktree and deleted on landing, so enumerating them makes the table stale the day it is written.
- The example names are marked as examples: a branch is identified by its role, and the project
  supplies the word (`master`/`main`, `beta-master`/`staging`, `playbook`/`docs`). The doc now says
  to take the names from `git branch -r` and never to introduce a branch to match the table.
- Working-branch cleanup: delete a merged branch, never `-D` one carrying commits absent from every
  permanent branch — that is the only reference to them.
- The separate "worktree farm" section folded into the working-branch bullet; it repeated the same
  one-issue-one-worktree rule in the same file.

## [0.1.0] - 2026-10-31

### Changed

- Phase 4 is "plan before the work" and phase 5 accepts a non-code deliverable whose check is a
  link or schema lint. The route is the same; only the proof differs.

## [0.0.1] - 2026-10-31

First public version. Nothing was published before this, so the entire body of the
skill — every rule, section and script — lands here rather than pretending to a
history it never had.

### Changed

- Phase 8 states its trigger: the user's request only. No automatic run at the end of a task,
  session, or worktree teardown.
