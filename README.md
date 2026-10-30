# Skills

My own agent skills, published for use across machines and agents.

This repo holds the ten skills of the engineering standard — the profile,
voice, workflow, and repo skills I wrote myself. Third-party skills live in
`~/skills`, the live skill store, and are not vendored here. The `.gitignore`
is an allowlist, so a downloaded skill can never be committed by accident.

## Published skills

| Skill | Version | Description |
|-------|---------|-------------|
| [agent-rules](./agent-rules) | 0.0.1 | Writing and maintaining the agent instruction layer — AGENTS.md tiers, one-rule-one-home ownership, resolving a rule that drifted or collided, and the issue-first/plan-first tracker gates. |
| [code-discovery](./code-discovery) | 0.1.0 | Answer structural code questions from a persistent code graph instead of reading files — who calls this, what does it call, the shape of a module — and prove the index is current before trusting it. Covers index freshness, the grep-vs-graph cost order, per-directory project resolution, and reclaiming disk. |
| [design](./design) | 0.0.1 | The craft bar for UI work — tokens, layout, motion, states, and the design doc that must match the code. Use when building, editing, or reviewing any interface, or when deciding whether a UI change is finished. |
| [project-scaffold](./project-scaffold) | 0.1.0 | Scaffold a new project of any kind — pick the layout, stack defaults, and agent layer, and get to the first green run. Covers TypeScript/Node, Astro/Cloudflare, Python, monorepo, and agent-only/skill repos. |
| [repo-align](./repo-align) | 0.1.0 | Audit an existing repo against this standard and fix the drift — missing or duplicated rules, wrong tier, broken harness shims, undocumented green command, missing design docs. Ships `scripts/audit.py`, which decides the mechanical checks deterministically and prints the judgement ones as `manual`. Use when a repo predates the standard, a rule has drifted, or an agent keeps making the same mistake in a repo that has an AGENTS.md. |
| [repo-init](./repo-init) | 0.2.0 | Bootstrap a repo's agent layer from nothing — AGENTS.md, detail tier, harness shims, and the green-command table. Use only when a repo has no AGENTS.md at all. For a repo that already has one, use repo-align. |
| [skills-install](./skills-install) | 0.2.1 | Install, update, relink, or vet third-party agent skills from the internet. Use when the user asks to install a skill, a skill is missing or stale, a harness cannot see a skill, or a new source needs recording. |
| [standard](./standard) | 0.1.0 | Router over the engineering standard — choose the right rule, repo, scaffold, workflow, verify, or design skill, and see which sections are on. Shapes every reply to Answer / Why / Steps / Evidence / Next. |
| [verify-change](./verify-change) | 0.1.0 | Decide what counts as proof a change works, and say it correctly. Use before claiming done, fixed, or working, when choosing between a test and a manual check, or when a change touches UI, data, or a deploy. |
| [workflow](./workflow) | 0.1.0 | The route work takes, idea to shipped — sharpen, prototype, split, plan, build, review, ship, retro — with the done-criterion for each phase and which skill to run at each. Use when deciding what to do next, when a request is underspecified, when a task has grown past one session, or when work was finished but not proven. |


## Install

Two routes, and they differ in what they touch. Neither one vendors anything.

### As a human

```sh
git clone https://github.com/ekajaya740/skills ~/skills
ln -sfn ~/skills ~/.agents/skills        # the store every harness reads
python3 ~/skills/scripts/link_harnesses.py --apply
```

That links the ten skills into `~/.claude/skills`, `~/.codex/skills`, and any
other harness the script knows. Restart the harness afterwards — skills are
discovered at session start, so a new link is invisible until then.

To add the third-party skills as well:

```sh
cd ~/skills
./install-skills.sh --dry-run    # print the 68 commands, run nothing
./install-skills.sh              # shows every source, then asks once
```

### As an agent

Read the list before you run anything, and **get the user's consent first.**
Installing a skill is not a file copy: it is instructions the agent will follow,
written by someone the user has not vetted, loaded by every harness on the
machine.

```sh
./install-skills.sh --dry-run    # always this first; safe, touches nothing
```

Then show the user the source list and ask. Only after they say yes:

```sh
./install-skills.sh --yes
```

`--yes` is for when the user has already agreed in this conversation. It is not
a way to skip asking them. The script refuses to run in a non-interactive shell
without it, so an unattended agent cannot install by accident.

## Installing something new

Every install carries the same three questions, and a `no` to any of them is a
`no` to the install:

| Question | Why it stops the install |
| --- | --- |
| **Who wrote it, and under what licence?** | No licence means all rights reserved, not "free to take". `ATTRIBUTION.md` records the answer. |
| **What will it run?** | A skill can add hooks, edit harness config, or shell out on load. Read `SKILL.md` and any script before it lands. |
| **Do you already have this trigger?** | Two skills on one trigger fight, and the agent sees both. |

Report a failure as one line in the reply. Do not install it and mention it
afterwards.

## Third-party skills

Third-party skills are **not** in this repo. They live in `~/skills`, the live
skill store that `~/.agents/skills` points at, and are installed from their
upstream repositories there.

[`skills.json`](./skills.json) records every source — repository, author,
licence — so a fresh machine can reproduce the store, and
[`ATTRIBUTION.md`](./ATTRIBUTION.md) names each author and licence in a form a
human can read. Both are generated from the same record, and CI fails if they
disagree.
[`install-skills.sh`](./install-skills.sh) does the installing:

```sh
./install-skills.sh            # show every source, ask once, then install
./install-skills.sh --update   # update everything already installed
./install-skills.sh --dry-run  # print the commands, run nothing
./install-skills.sh --yes      # skip the prompt (only after the user agreed)
```

Without `--yes`, the installer prints every source with its author and licence
and asks once before running anything. It exits rather than guess when there is
no terminal, so a script or an unattended agent cannot install by accident.

Some skills are no longer published upstream (renamed, bundled into a larger
skill, or withdrawn). Those are listed under `notAvailableUpstream` in
`skills.json`; the installer skips them.

## Adding a skill

A skill is a directory containing a `SKILL.md`. To publish a new one of my own,
create the directory and then un-ignore it in `.gitignore`:

```gitignore
# Published skills
!/standard/
!/my-new-skill/

Nothing else needs changing: everything not explicitly allowed stays untracked.

## Versioning

Each published skill carries a `version` field in the frontmatter of its
`SKILL.md`, and follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — a change that invalidates how the skill was previously used
  (renamed files, removed sections, changed required inputs).
- **MINOR** — new guidance, references or capabilities that are additive.
- **PATCH** — corrections, clarifications and typo fixes.

Releases are tagged `‹skill›-v‹version›`, for example `repo-align-v0.0.1`.
The tag and the frontmatter `version` are kept in step, so a consumer such as
the `ekajaya740.github.io` submodule can pin an exact revision:

```sh
git -C .agents/skills fetch --tags
git -C .agents/skills checkout repo-align-v0.0.1
```

Each skill keeps its own `CHANGELOG.md`, newest first, with the released version
and date as headings.

## Releasing

Releases are automated. To ship a new version of a skill, bump the `version`
field in its `SKILL.md` and add a matching section to its `CHANGELOG.md`:

```md
## [0.0.1] - 2026-10-31

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

- [`AGENTS.md`](./AGENTS.md) documents how to install, update and re-link the
  third-party skills, and what agents working in this repository must not do.
- The live skill store is `~/skills`. `~/.agents/skills` points there, and
  `~/.claude/skills` and `~/.codex/skills` hold one symlink per skill pointing
  back into it. This repository is separate: the ten skills here are linked
  into that store, so editing one changes what every harness loads.
- `ekajaya740.github.io` consumes this repository as a git submodule at
  `.agents/skills`. Changes to a skill therefore need a submodule pointer bump
  in that repository to take effect.

## Licence

My own skills are MIT licensed — see [LICENSE](./LICENSE).

Third-party skills are not mine and are not covered by that licence. Each one
belongs to its original author under its own terms; [`ATTRIBUTION.md`](./ATTRIBUTION.md)
names every author and licence, generated from [`skills.json`](./skills.json).
Installing a skill does not make it part of this repository, and no third-party
code is vendored here.
