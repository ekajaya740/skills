---
name: repo-align
description: Apply the fixes an audit named — bring an existing repo in line with this standard by editing only what the user approved, then prove each fix with the repo's own command. Also refreshes the machine's installed skills, because a stale skill is the standard being violated by the tool that enforces it. Use when an audit report exists and the user has named which findings to fix, or when they say "align this repo". Use repo-audit to get the report; use this only once someone has agreed to a change.
disable-model-invocation: true
version: 0.5.0
---

# Repo Align

Change the repo. **Only what the user named, one finding at a time, each with a command that shows
it worked.**

This skill is the editing half of the standard's alignment. The reading half is `repo-audit`, which
writes nothing; it owns every check id and the report. Keeping them in one skill meant the only way
to learn how far off a repo was, was to run something allowed to edit it.

| | `repo-audit` | `repo-align` (this) |
| --- | --- | --- |
| Writes | Nothing | Only the named findings |
| Needs consent | No | Yes, before the first edit |
| Output | Ranked findings | `<id> fixed — <command> → <line>` |

## 0. Refresh the installed skills

Aligning a repo against an older copy of the standard produces a repo aligned to a standard nobody
is reading. So the installed store gets refreshed first — but **in the store, not in the repo being
aligned**: the scripts live with the skills, and a repo that merely adopts the standard has neither
`install-skills.sh` nor `scripts/link_harnesses.py`.

```bash
cd ~/skills                        # the store; `.agents/skills` where the repo pins its own set
./install-skills.sh --dry-run      # every source it would touch; runs nothing
./install-skills.sh --update       # shows each source, asks once, then updates
python3 scripts/link_harnesses.py --apply
```

**Stop when there is nothing to update.** No `~/.agents/.skill-lock.json` means no recorded
sources, so `--update` would be an install from scratch — say that and move on to § 1. A repo that
pins its own set (`skills-lock.json` committed, `.agents/` ignored) was aligned against that pin;
refreshing the store does not move it, and the pin stays unless the user asks to bump it.

Three rules, and the third is the one that gets skipped:

1. **Consent before the fetch.** Show the source, author, licence, and what changed. `--yes` answers
   "install this" on the user's behalf; pass it only after they have said yes to these exact
   sources in this conversation. Refreshing the store is not a licence to fetch anything new.
2. **A failed refresh does not block the alignment.** A network error, a missing CLI, or a source
   the user declined is reported once and then ignored — the repo edit proceeds against the skills
   as installed, and the report says which version that was.
3. **Relink and restart.** A skill on disk with no harness symlink is invisible, and neither Claude
   Code nor Codex discovers a new one until it restarts. `link_harnesses.py --apply`, then tell the
   user a restart is pending — before the next session, not before this edit.

**Done when** the refresh either ran or was reported as unnecessary, and the user knows which
installed version the alignment used.

## 1. Take the findings, not the repo

The input is a report with ids. If there is none, run `repo-audit` first — do not let a fixer
choose its own scope, because that is how an "align this repo" request turns into an unrequested
rewrite.

Confirm the set back in one line, then stop:

```
Fixing: RULE-DUP-01, VERIFY-01, SHIM-01. Leaving: STRUCT-03, BRANCH-01. Say the word to change the list.
```

**Done when** the user has named the findings, or said none. Silence is not approval.

## 2. Apply

For each approved id, the fix is the one in
[`repo-audit/CHECKLIST.md`](../repo-audit/CHECKLIST.md) — that file is the source of truth, and this
skill does not restate it. Two constraints on top:

- **One id, one edit.** Two findings touching the same file land as two steps, so a failure is
  attributable.
- **Move rules, never delete them.** Replacing a shim or demoting a rule means placing what it
  said first. A shim's unique rules have to land in `AGENTS.md` or `docs/agents/` before the shim
  becomes `@AGENTS.md`; otherwise the fix is a deletion wearing a tidy name.

## 3. Prove each one

After the batch, in this order:

1. Run the repo's green command from `AGENTS.md`.
2. Re-run each fixed check, from the audited repo:
   `python3 <skill-store>/repo-audit/scripts/audit.py . --section <section>`
   (`<skill-store>` is `~/skills` on a normal install; `.agents/skills` in a repo that pins the set).
3. Report one line per fix: `<check-id> fixed — <command> → <first meaningful line>`.

A fix whose check still reports `drift` is not a fix; say so instead of summarising it as done.
The ladder is skill `verify-change`: a re-run is rung 2, and "the file looks right" is not a rung.

**Done when** every applied id reports `ok`, and the green command still exits 0.

## What this skill never does

- **Never rewrites `AGENTS.md` wholesale.** Alignment is a list of edits. A user who wrote that
  file wants to argue about each line.
- **Never edits a finding the user did not name.** A report is a menu, not a queue.
- **Never deletes a rule because it looks redundant** without showing both copies first.
- **Never introduces a rule the repo does not need.** A repo with three hard rules and a green
  command is aligned. Alignment is not the template's full length.
- **Never updates the machine's skills without showing the sources first.** `--yes` before consent
  breaks the one rule that keeps third-party instructions trustworthy.

## Related

- The report this skill consumes, and every check id → skill `repo-audit`
- Installing, vetting, or relinking skills → skill `skills-install`
- No `AGENTS.md` at all → skill `repo-init`
- Tiers and rule ownership → skill `agent-rules`
- Proof a fix worked → skill `verify-change`
