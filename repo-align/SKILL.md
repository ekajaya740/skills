---
name: repo-align
description: Audit an existing repo against this standard and fix the drift — missing or duplicated rules, wrong tier, broken harness shims, undocumented green command, missing design docs. Use when a repo predates the standard, a rule has drifted, or an agent keeps making the same mistake in a repo that has an AGENTS.md.
disable-model-invocation: true
version: 0.4.0
---

# Repo Align

Bring an existing repo in line with the standard. **Reports first, edits only what you approve.**

Use `repo-init` when there is no `AGENTS.md`. Use this when there is one, and it has drifted —
or when the repo predates the standard and you want to know how far off it is.

## What kind of repo it thinks this is

The audit reads `Kind: code` or `Kind: knowledge` from `AGENTS.md` and prints the answer in the
first line, because two checks mean different things by repo kind:

| Kind | `VERIFY-01` | `VERIFY-03` |
| --- | --- | --- |
| `code` | A commands table with a build or test | A repo with commands but no CI is `missing` |
| `knowledge` | A link check or schema lint; a `None yet` row is `manual`, not a failure | Optional — a badge that runs nothing reads as proof |

With no declared kind it guesses from the file list (a manifest or CI means `code`), which
misreads a docs-heavy code repo and a code repo before its first manifest. Declare it.

## 1. Declare the scope

Print one line, then run only those checks:

```
Aligning: rules, structure, verify. Off: design, skills, tracker. Change: `+ design`, `no structure`.
```

Sections match skill `standard`: `rules`, `structure`, `verify`, `design`, `skills`. A section
that is off is not checked, not reported, and not mentioned again.

The script accepts `rules`, `structure`, `verify`, and `design`. `skills` has no mechanical
checks — it audits this repository's own publishing rules and stays agent-run. The commit-hook
checks (`HOOK-01`, `HOOK-02`) report under `verify` because that is the section whose question
they answer — "prove the repo is green" — and they carry a trap worth knowing: a hook that is
committed but not enabled in this clone is `manual`, not `drift`, because `core.hooksPath` is
per-clone config and a fresh CI checkout never has it.

## 2. Audit

Run the script first. It decides every mechanical check the same way twice:

```bash
python3 scripts/audit.py .              # report only, always exits 0
python3 scripts/audit.py . --strict     # exit 1 on a strict finding — use in CI
python3 scripts/audit.py . --json       # machine-readable
python3 scripts/audit.py . --run        # also execute the green-command table
python3 scripts/audit.py . --section rules,verify
```

It prints `ok`, `drift`, `missing`, `n/a`, and `manual`. **`manual` is not `ok`** — those checks
need judgement and the script cannot give it. Finish them by hand from
[`CHECKLIST.md`](CHECKLIST.md), which is the source of truth for every id and fix. The script
covers the mechanical third; the rest is still yours.

**Done when** every check in every enabled section has a verdict: `ok`, `drift`, `missing`, or
`n/a` — and no `manual` is left unread.

## 3. Report, ranked by blast radius

One table. Highest-consequence first, not file order.

```
| # | Check | Finding | Fix |
| - | ----- | ------- | --- |
| 1 | RULE-DUP-01 | "apps run on host" stated in AGENTS.md:41 and docs/environment.md:12, differently | Keep AGENTS.md as owner, make the other a pointer |
| 2 | VERIFY-01 | No green-command table in AGENTS.md | Add it; 4 commands detected from package.json |
| 3 | SHIM-01 | CLAUDE.md restates all 7 hard rules | Extract the 7 into AGENTS.md § Hard rules, then replace the file with `@AGENTS.md` |
```

Then: **which of these should I apply?** Apply the ones the user names; leave the rest in the
report. Do not batch-apply an audit.

**Done when** the user has picked, or said none.

## 4. Apply

For each approved finding, apply the fix from the checklist exactly. After the batch:

1. Run the repo's green command.
2. Re-run the checks you just fixed.
3. Report one line per fix: `<check-id> fixed — <command> → <first meaningful line>`.

**Done when** the re-run reports `ok` for every applied check.

## The five things worth checking

The full checklist is long; these five catch most drift in most repos.

| Check | Drift looks like | Why it matters |
| --- | --- | --- |
| **RULE-DUP** | The same rule, in two files, worded differently | A drifted rule is violated via the weaker copy |
| **RULE-TIER** | "How to work" rules sitting in a detail file or a skill | An agent that never opens that file breaks it |
| **SHIM** | `CLAUDE.md` restating `AGENTS.md` | Two sources of truth for the same rule — and replacing it before its unique rules are placed deletes them |
| **VERIFY** | No command that proves the repo is green | "It works" becomes unfalsifiable |
| **STRUCT** | Folders nobody can justify, or a `utils/` | An unjustified folder collects orphans |

## What this skill never does

- **Never rewrites `AGENTS.md` wholesale.** An audit is a list of edits, not a replacement. A user
  who wrote that file wants to argue about each line.
- **Never deletes a rule because it looks redundant** without showing both copies first.
- **Never applies a finding the user did not name.** Silence is not approval.
- **Never introduces a rule the repo does not need.** A repo with three hard rules and a green
  command is aligned. Alignment is not the template's full length.

## Related

- Every check, with detection and fix → [`CHECKLIST.md`](CHECKLIST.md)
- The mechanical checks as code → [`scripts/audit.py`](scripts/audit.py)
- No `AGENTS.md` at all → skill `repo-init`
- Tiers and rule ownership → skill `agent-rules`
- Proof a fix worked → skill `verify-change`
