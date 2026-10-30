# Pinning the project's skills

A repo's agent layer has two halves. `AGENTS.md` carries the rules that are **always** loaded. The
skill store carries the procedures that load **when named**. Both are part of the repo, so both need
a reason to exist and a way to be reproduced.

The failure this prevents: a fresh clone where the agent reads `AGENTS.md`, follows its pointer to
a skill, and finds nothing — so it improvises the procedure the repo already standardised.

## Project-local, not global

Install into `.agents/skills/`, never `~/.agents/skills`. A global install is invisible to
teammates and to CI, and a project that depends on it is a project that works on one machine.

```bash
cd <repo-root>
npx skills@latest add <owner>/<repo> -s <skill> -s <other> -y
```

Omit `-g`. Without it the CLI writes `.agents/skills/<name>/`, symlinks each harness's directory,
and records every install in `skills-lock.json` — the pin file that makes the set reproducible.

**Pass every skill by name with repeated `-s`.** Omitting `-s` installs the whole repository:
dozens of skills, each competing for the agent's attention.

If the repo carries the standard's `install-skills.sh`, one flag does the whole set:

```bash
./install-skills.sh --project      # ./.agents/skills, no -g
./install-skills.sh --project --dry-run   # print the commands, run nothing
```

`--project` resolves the repo root with `git rev-parse` and drops `-g`, so the install lands in
`.agents/skills/`. `--dry-run` prints what would run.

## What gets pinned

The full working set, not a minimal one. A project that halves its skills to save attention spends
it back later re-deriving what the missing skill said.

| Source | Skills | Why |
| --- | --- | --- |
| `mattpocock/skills` | `grilling`, `grill-with-docs`, `domain-modeling`, `wayfinder`, `to-spec`, `to-tickets`, `implement`, `tdd`, `code-review`, `pr`, `retro`, `diagnosing-bugs`, `writing-for-agents`, `handoff`, `codebase-design` | The process route: sharpen, split, build, review, ship |
| `emilkowalski/skills` *(UI projects only)* | `prototype`, `pick-ui-library`, `break-ui`, `review-animations`, `improve-animations`, `animate`, `animation-vocabulary`, `apple-design` | The design bar, and the vocabulary to name what is wrong |
| `pbakaus/impeccable` *(UI projects only)* | `impeccable` | Full-interface craft pass |
| `alejandrobailo/no-use-effect` *(React only)* | `no-use-effect` | The effect-free data flow rule |
| `ayghri/i-have-adhd` | `i-have-adhd` | Reply voice. `standard` inlines it as a fallback, so this is optional |
| `ekajaya740/skills` (this standard) | `standard`, `repo-init`, `repo-align`, `agent-rules`, `project-scaffold`, `workflow`, `verify-change`, `design`, `skills-install` | The standard itself, when the machine has no global install. Pinned only in repos that adopt the standard; a project that only uses it does not need a copy |

Drop a row only when the project genuinely cannot use it — no UI means no `emilkowalski/skills`, no
React means no `no-use-effect`. "We will not use it much" is not a reason.

## The lock file is the reproducible artifact

A project-local install writes three things at the repo root:

| Path | What it is | Track? |
| --- | --- | --- |
| `.agents/skills/<name>/` | A checked-out copy of someone else's work | **No** — generated, and it goes stale |
| `.claude/skills/<name>` | A symlink into the store, written by the CLI | **No** — a committed symlink breaks on a fresh checkout |
| `skills-lock.json` | Source, path, and hash per skill | **Yes** — this is the pin |

```gitignore
.agents/
.claude/skills/
```

Ignore `.claude/skills/`, not `.claude/` — a settings or hooks file in there is yours and belongs in
the repo. `skills-lock.json` sits at the root and no rule ignores it, so it needs no negation.

A fresh clone then runs:

```bash
npx skills@latest experimental_install
```

Verified: it reads `skills-lock.json`, clones each source, and materialises the exact set. No skill
names to remember, no drift.

If the repo also keeps a `skills.json` (the list of *upstream sources* for the whole machine),
that is a different file with a different job — `skills-install` owns it. The lock is per repo.

## Done when

1. `.agents/skills/` holds the pinned set and every harness directory symlinks into it.
2. `skills-lock.json` is committed; `.agents/` and `.claude/skills/` are ignored.
3. `npx skills@latest experimental_install` in a clean checkout reproduces the set.
4. `AGENTS.md` names the skill store and the one command that restores it.

## Related

- Installing, updating, and vetting a source → skill `skills-install`
- Where the rule lives in the layer → [`INIT.md`](INIT.md) § 6
- Auditing an existing repo for a missing or stale store → skill `repo-align`

## Attribution

A pinned skill is someone else's work sitting in your repository, so the repo owes it a
credit. Two rules:

- **Pin by reference, not by copy.** The lock file names a source and a version; the skill
  itself stays upstream. A vendored copy drops the author's licence and goes stale silently.
- **Name the author where a reader will look.** The README's "Skills" section, or an
  `ATTRIBUTION.md` if the set is large. A table of `repo | author | licence` is enough.

If the repo carries the standard's `install-skills.sh`, `ATTRIBUTION.md` is generated from
`skills.json` and checked in CI, so a new pin cannot land without its credit.
