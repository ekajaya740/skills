# AGENTS.md

Instructions for agents working in this repository.

This directory is both the published skills repository and the live skill
store on this machine: `~/.agents/skills` is a symlink to it, and
`~/.claude/skills` and `~/.codex/skills` link back into it. Editing a skill
here changes what every harness loads.

## The update rule

Third-party skills are **installed from their upstream source, never vendored**.
They stay on disk for local use but are excluded from this repository by the
`.gitignore` allowlist, because the copyright is someone else's and a vendored
copy goes stale.

To update the installed skills:

```sh
npx skills@latest update -g -y
```

This reads `~/.agents/.skill-lock.json`, fetches each source repository, and
rewrites the skills that changed. It skips deletions in non-interactive mode,
so a skill that upstream has renamed or withdrawn is left in place rather than
removed.

To install a skill that is missing:

```sh
npx skills@latest add <owner>/<repo> -g -y -s <skill-name> -s <other-skill>
```

Pass every skill by name with repeated `-s` flags. Do **not** omit them: without
`-s`, the installer takes the whole repository, which for a large repo means
dozens of unwanted skills. `-g` installs into `~/.agents/skills`.

After either command, re-link the harnesses so the new skills become visible:

```sh
python3 scripts/link_harnesses.py --apply
```

Claude Code and Codex read `~/.claude/skills` and `~/.codex/skills`, which
contain one symlink per skill. A skill that exists in `~/.agents/skills` but has
no link in a harness is invisible to that harness, and a newly installed skill
has no link until this step runs. Restart the harness afterwards: skills are
discovered at session start.

## One route in, not two

`mattpocock/skills` can be taken two ways, and upstream says to pick one:

- the **Claude Code plugin** (`mattpocock-skills`), a managed read-only bundle
  that updates itself, or
- the **skills.sh install**, editable files in this store, updated by hand.

**This machine uses skills.sh.** The plugin must stay disabled, because
enabling it as well loads every skill twice. `~/.claude/settings.json` is
managed by the `ekajaya740/dotfiles` repository; if `enabledPlugins` there ever
contains `mattpocock-skills@mattpocock`, remove that entry rather than dropping
the skills.sh copies, so the skills stay editable and tracked by this repo.


## Recording a new source

When a skill is added, record where it came from in `skills.json` — repository,
author, licence, and the skill names taken. Add the same source to the
`SOURCES` array in `install-skills.sh` so a fresh machine can reproduce it.
Both files are published.

If upstream no longer publishes a skill under the name you have locally, list
it under `notAvailableUpstream` rather than deleting it, so the local copy is
not mistaken for an error.

## Published skills

Only skills authored here are published, and each is allowlisted explicitly in
`.gitignore`. `scripts/validate_skills.py` fails if anything outside the
allowlist is tracked, so a downloaded skill cannot reach the public repository
even if the ignore rules are edited wrongly.

A published skill needs:

- a `version` field in its `SKILL.md` frontmatter (SemVer)
- a matching `## [x.y.z]` heading in its `CHANGELOG.md`
- a row in the README's published skills table with the same version

Releasing is automatic: bump the version and push. See the README.

## Checks

```sh
python3 scripts/validate_skills.py          # allowlist, frontmatter, CHANGELOG, README
python3 scripts/release_skills.py --check   # what would be released
./install-skills.sh --dry-run               # installer parses, commands well formed
```

## Known issues

- **The `jev` CLI is broken.** `~/.local/bin/jev` and `~/.hermes/bin/jev` are
  dangling symlinks into a deleted `/private/tmp/hjs`, so the ten `jev-*` skills
  cannot run. Repairing it means running the upstream installer
  (`kerpopule/hermes-jev-skills`), which also writes plugins and agent files
  outside this repository.
- **`autoprompt` is third-party.** It is the public MIT skill
  `Spielewoy/autoprompt-skill` at v1.0.3, installed by its own CLI
  (`~/.vite-plus/bin/autoprompt`). It is not authored here and must not be
  published; upstream is now at v2.x, a substantial rewrite.
