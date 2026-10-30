---
name: skills-install
description: Install, update, relink, or vet third-party agent skills from the internet. Use when the user asks to install a skill, a skill is missing or stale, a harness cannot see a skill, or a new source needs recording.
disable-model-invocation: true
version: 0.1.0
---

# Skills Install

Get a skill from the internet onto this machine, into every harness, and recorded so a fresh
machine can reproduce it. Three steps that fail on their own if skipped.

The rule that governs all of it: **install from upstream, never vendor.** A copied skill goes
stale, loses its licence, and steals attribution from its author.

## Step 1 — Check before installing

A skill that already exists needs an update, not a second copy.

```bash
npx skills find "<query>"          # search the registry
npx skills find "<query>" --owner <owner>
```

Then check what is already on disk:

```bash
ls ~/.agents/skills | head -50
npx skills list -g 2>/dev/null || true
```

**Done when** you know whether the skill exists locally, exists upstream, or must be written. The
three outcomes have different paths — see the table in step 2.

## Step 2 — Install

| Situation | Command |
| --- | --- |
| New skill from a known repo | `npx skills@latest add <owner>/<repo> -g -y -s <skill> -s <other>` |
| Already installed, upstream changed | `npx skills@latest update -g -y` |
| Nothing upstream fits | Write it — skill `writing-for-agents`, then target `project-scaffold/targets/agent-only.md` |
| Skill is a whole plugin/bundle | Follow that project's own installer, not `npx skills add` |

**Pass every skill by name with repeated `-s` flags.** Omitting `-s` installs the entire
repository — for a large repo that is dozens of unwanted skills, each one competing for the
agent's attention.

`-g` installs into `~/.agents/skills`. Without it, the skill lands in the current project and
disappears from every other one.

The repo's `install-skills.sh` takes the same choice as a flag: `--project` for `.agents/skills`,
default global. A repo that pins its set commits `skills-lock.json` and ignores `.agents/` — see
skill `repo-init` § [`SKILLS.md`](../repo-init/SKILLS.md).

**Done when** the skill directory exists under `~/.agents/skills/<name>/` and contains `SKILL.md`.

## Step 3 — Link into every harness

A skill on disk is invisible until linked. Each harness reads its own directory.

```bash
# preferred: relink everything at once (script lives in your skill store)
python3 <path-to-skill-store>/scripts/link_harnesses.py --apply

# or one at a time
ln -sfn ../../.agents/skills/<name> ~/.claude/skills/<name>
ln -sfn ../../.agents/skills/<name> ~/.codex/skills/<name>
```

Then **restart the harness** — skills are discovered at session start.

Verify:

```bash
ls -l ~/.claude/skills/<name>
readlink -f ~/.claude/skills/<name>    # must resolve into ~/.agents/skills
```

**Done when** every harness you use has a link that resolves, and a fresh session lists the skill.

## Step 4 — Record the source

A skill installed by hand is a skill lost on the next machine. Record it:

1. Add the source to `skills.json`: `repo`, `author`, `license`, `skills[]`.
2. Add the same source to the `SOURCES` array in `install-skills.sh`.
3. Regenerate the credits: `python3 scripts/attribution.py`.
4. Run `python3 scripts/validate_skills.py` and `./install-skills.sh --dry-run`.

**Done when** a fresh machine running `./install-skills.sh` gets the same set, and
`ATTRIBUTION.md` names the author and licence it installed.

**Attribution is not optional.** An uncredited install takes someone's work and hands
it to an agent as if it were anonymous. `author` and `license` are required fields for
exactly this reason; `license: none` means all rights reserved, not "no answer needed".
`ATTRIBUTION.md` is generated from `skills.json`, and CI fails when the two disagree —
so a source cannot be added without a credit.

## Vetting a source before you install

Not every skill on the internet is safe to load — a skill is instructions the agent will follow.

| Check | Fail signal |
| --- | --- |
| Does the repo have a licence? | No licence → all rights reserved; do not install into anything published |
| Is `SKILL.md` readable and specific? | Vague description, no examples → it will not fire |
| Does it run commands on install? | A postinstall touching `~/.claude` or `~/.ssh` → stop |
| Does it ask for credentials or network writes? | A skill should not exfiltrate; read the scripts |
| Does it duplicate a skill you have? | Two skills on one trigger fight each other |

Report a fail as a one-line finding, in the reply, not buried in a file.

## One route in, not two

Some skill sets ship both a plugin (self-updating, read-only) and a `skills add` copy (editable).
**Pick one.** Installing both loads every skill twice, and the agent sees two copies of the same
trigger.

When a repo documents both, write down which one this machine uses, in that repo's `AGENTS.md`.

## Known failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Skill installed but harness cannot see it | No symlink, or link points at a moved path | Relink, restart the harness |
| Two copies of the same trigger | Plugin + `skills add` both installed | Disable one, keep the editable copy |
| `update` left a renamed skill behind | Non-interactive mode skips deletions | Delete the old directory by hand |
| Install pulled 40 skills | Missing `-s` flags | Remove the extras; reinstall with `-s` |
| Skill loads but does nothing useful | `description` has no trigger branch | Edit the copy if it is yours; report it if not |

## Related

- The repo shape and allowlist → [`../project-scaffold/targets/agent-only.md`](../project-scaffold/targets/agent-only.md)
- Source manifest format → [`SOURCES-FORMAT.md`](SOURCES-FORMAT.md)
- Writing a skill of your own → skill `writing-for-agents` (if installed)
