# Target: agent-only / skill repo

For a repo whose product is files an agent reads: skills, rules, prompts, templates. No build, no
runtime. The "green" check is a validator.

Use it for a personal skill store, a shared rules repo, an internal prompt library. The repo is
both the published artifact and the live install location more often than people expect — decide
which, first.

## Tree

```
.
├── AGENTS.md                # how to add, update, publish; the allowlist rule
├── README.md                # published table: name | version | description
├── LICENSE                  # explicit, even for a private repo
├── .gitignore               # deny-by-default allowlist; see § Allowlist
├── skills.json              # third-party sources: repo, author, licence, names
├── install-skills.sh        # reproduce a fresh machine from skills.json
├── scripts/
│   ├── validate_skills.py   # frontmatter, changelog, README, allowlist
│   └── link_harnesses.py    # one symlink per skill per harness
├── <skill-a>/
│   ├── SKILL.md             # frontmatter: name, description, version
│   ├── CHANGELOG.md         # `## [x.y.z]` heading matching the version
│   └── <reference>.md       # detail, reached by a pointer from SKILL.md
└── .github/workflows/
    ├── validate.yml
    └── release.yml
```

## The three-file contract per skill

| File | Required | Holds |
| --- | --- | --- |
| `SKILL.md` | yes | Frontmatter (`name`, `description`, `version`, `disable-model-invocation`) + the body |
| `CHANGELOG.md` | yes, when published | Newest first, `## [x.y.z] - YYYY-MM-DD` heading matching the version |
| `README.md` row | yes, when published | `\| [name](./name) \| x.y.z \| description \|` |

A skill without all three is a skill that drifts from its released version. The validator exists
to make that impossible to miss.

## Frontmatter

```yaml
---
name: my-skill
description: "What it does. Use when … . NOT for: … (use other-skill instead)."
version: 1.0.0
disable-model-invocation: true   # only if it fires by name only
---
```

| Field | Rule |
| --- | --- |
| `name` | Must equal the directory name. The validator checks this. |
| `description` | The only thing loaded every turn. Front-load the trigger; one trigger per branch; state what it is NOT for. |
| `version` | SemVer. Matches a CHANGELOG heading. |
| `disable-model-invocation` | Omit for a skill the agent should reach on its own; set `true` for user-invoked-only. |

A `description` that says "helps with projects" fires on nothing. Name the branch: "Use when the
user asks to install a skill, a skill is stale, or a harness does not see a skill."

## Allowlist `.gitignore`

Deny everything, allow back only what you publish:

```gitignore
/*                     # deny by default

!/AGENTS.md
!/README.md
!/LICENSE
!/skills.json
!/install-skills.sh
!/scripts/
!/.github/

# your own skills
!/my-skill/
```

Why deny-by-default: the directory is the live store, so a downloaded skill lands here. Without
the allowlist, one `git add -A` publishes someone else's copyrighted work under your name.

**Never vendor third-party skills.** Record them in `skills.json` and reinstall from upstream; a
vendored copy goes stale and steals attribution. Full install and update procedure: skill
`skills-install`.

## The green command

```bash
python3 scripts/validate_skills.py     # exits 0: allowlist, frontmatter, CHANGELOG, README agree
./install-skills.sh --dry-run          # exits 0: the installer still parses
```

Wire both into `.github/workflows/validate.yml`. The allowlist check is the leak guard: it fails
if anything outside the allowlist is tracked, which catches an accidental `git add -A` before it
reaches a public remote.

## Linking harnesses

`~/.agents/skills` is the source of truth; each harness reads its own directory. A skill on disk
with no link is invisible.

```bash
ln -sfn ../../.agents/skills/my-skill ~/.claude/skills/my-skill
```

One symlink per skill per harness. Restart the harness afterwards — skills are discovered at
session start. Details: skill `skills-install`.

## Anti-patterns

- A skill with no `description` triggers. It is a file, not a skill.
- A `description` listing every synonym for the same trigger. That is one branch written twice.
- Publishing a third-party skill because it was convenient.
- Version bumped in `SKILL.md` with no changelog heading. The release workflow will skip it
  silently.
- Editing a skill in `~/.claude/skills/` directly. You have diverged it from the store and the
  next relink overwrites the edit.

## Related

- Installing and updating third-party skills → skill `skills-install`
- Writing the skill body → skill `writing-for-agents` (if installed)
- Rule ownership → skill `agent-rules`
