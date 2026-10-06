# Skills

My own agent skills, published for use across machines and agents.

This directory is also the live skill store on my machine (`~/.agents/skills`
points here), so it holds skills written by other people too. Those are **not**
published here — see [Third-party skills](#third-party-skills) — and the
`.gitignore` is written as an allowlist so that a newly downloaded skill can
never be committed by accident.

## Published skills

| Skill | Version | Description |
|-------|---------|-------------|
| [design-system](./design-system) | 1.0.0 | The design system for workofekajaya.com — an Astro 6 + React 19 + Tailwind v4 dark portfolio. Use when building, editing or reviewing any UI on that site. |

## Third-party skills

Around fifty skills in this directory were written by other people and
installed from their upstream repositories. They stay on disk for local use but
are deliberately excluded from this repository: the copyright is theirs, and
copying them here would mean maintaining stale forks instead of tracking
upstream.

[`skills.json`](./skills.json) records where each one comes from, who wrote it
and under which licence. [`install-skills.sh`](./install-skills.sh) installs
them:

```sh
./install-skills.sh            # install anything missing
./install-skills.sh --update   # update everything already installed
./install-skills.sh --dry-run  # print the commands, run nothing
```

Some skills I have locally are no longer published upstream (renamed, bundled
into a larger skill, or withdrawn). Those are listed under
`notAvailableUpstream` in `skills.json`; the installer skips them.

## Adding a skill

A skill is a directory containing a `SKILL.md`. To publish a new one of my own,
create the directory and then un-ignore it in `.gitignore`:

```gitignore
# Your own skills
!/design-system/
!/my-new-skill/
```

Nothing else needs changing: everything not explicitly allowed stays untracked.

## Versioning

Each published skill carries a `version` field in the frontmatter of its
`SKILL.md`, and follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — a change that invalidates how the skill was previously used
  (renamed files, removed sections, changed required inputs).
- **MINOR** — new guidance, references or capabilities that are additive.
- **PATCH** — corrections, clarifications and typo fixes.

Releases are tagged `‹skill›-v‹version›`, for example `design-system-v1.0.0`.
The tag and the frontmatter `version` are kept in step, so a consumer such as
the `ekajaya740.github.io` submodule can pin an exact revision:

```sh
git -C .agents/skills fetch --tags
git -C .agents/skills checkout design-system-v1.0.0
```

Each skill keeps its own `CHANGELOG.md`, newest first, with the released version
and date as headings.

## Releasing

Releases are automated. To ship a new version of a skill, bump the `version`
field in its `SKILL.md` and add a matching section to its `CHANGELOG.md`:

```md
## [1.1.0] - 2026-10-06

### Added

- What changed.
```

Pushing that to `main` is the whole procedure. The Release workflow in
`.github/workflows/release.yml` compares each skill's version against the tags
that already exist; anything untagged is released as `‹skill›-v‹version›`, with
the release notes taken from the CHANGELOG section and a GitHub Release created.
Skills whose version has not changed are left alone, so several skills can be
released in one push.

The Validate workflow in `.github/workflows/validate.yml` runs on every push and
pull request. Its most important job is the leak check: it fails if anything
outside the `.gitignore` allowlist is tracked, which is what stops a downloaded
skill from reaching this public repository. It also checks that every published
skill has valid frontmatter and a CHANGELOG entry for its version, that
`skills.json` is valid JSON, and that the installer still parses.

Both scripts run locally:

```sh
python3 scripts/validate_skills.py          # checks; exits non-zero on problems
python3 scripts/release_skills.py --check   # what would be released
```

`release_skills.py --tag` creates the tags without pushing, if you ever need to
release by hand.

## Notes

- `~/.agents/skills` is a symlink to this directory, so editing files here
  changes the skills every agent on the machine sees.
- `ekajaya740.github.io` consumes this repository as a git submodule at
  `.agents/skills`. Changes to `design-system/` therefore need a submodule
  pointer bump in that repository to take effect.

## Licence

My own skills are MIT licensed — see [LICENSE](./LICENSE). Third-party skills
are covered by their own licences, recorded in [`skills.json`](./skills.json).
