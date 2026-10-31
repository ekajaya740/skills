---
name: repo-audit
description: Report where an existing repo has drifted from this standard — duplicated or wrongly-tiered rules, harness shims that copy AGENTS.md instead of pointing at it, no command that proves the repo green, commit hooks that would be bypassed, unjustified folders, an undocumented environment, an unstated branch topology. Read-only: it changes nothing, so it runs before anyone has agreed to a fix, in CI, or on a repo you were only asked to inspect. Use when someone asks "how far off is this repo", or when the answer has to be a report rather than an edit.
disable-model-invocation: true
version: 0.1.0
---

# Repo Audit

Answer one question: **how far is this repo from the standard, and what exactly is wrong?**

Nothing here edits. That is the point of it being its own skill:

| | `repo-audit` (this) | `repo-align` |
| --- | --- | --- |
| Writes to the repo | Never | Only what the user names |
| Needs permission first | No | Yes, per finding |
| Safe on a repo you do not own | Yes — read the report, leave | No |
| Runs in CI | Yes, `--strict` | No — a fixer in CI is a fixer nobody reviewed |
| Output | A ranked table of findings | `<id> fixed — <command> → <line>` |

A user who wants the answer but is not ready to change code has no use for a fixer, and handing
them one means the first thing that happens is an edit they did not ask for. Split so the
inspection is free.

Use `repo-init` when there is no `AGENTS.md`. Use `repo-align` when the user wants fixes.

## What kind of repo it thinks this is

The audit reads `Kind: code` or `Kind: knowledge` from `AGENTS.md` and prints it in the first
line, because two checks mean different things by repo kind:

| Kind | `VERIFY-01` | `VERIFY-03` |
| --- | --- | --- |
| `code` | A commands table with a build or test | A repo with commands but no CI is `missing` |
| `knowledge` | A link check or schema lint; a `None yet` row is `manual`, not a failure | Optional — a badge that runs nothing reads as proof |

With no declared kind it guesses from the file list (a manifest or CI means `code`), which
misreads a docs-heavy code repo and a code repo before its first manifest. Say so in the report
when it guessed, and tell the user the one line that fixes it.

## 1. Declare the scope

Print one line, then run only those checks:

```
Auditing: rules, structure, verify. Off: design, skills. Change: `+ design`, `no structure`.
```

Sections match skill `standard`: `rules`, `structure`, `verify`, `design`, `skills`. A section
that is off is not checked, not reported, and not mentioned again.

The script accepts `rules`, `structure`, `verify`, and `design`. `skills` has no mechanical
checks and stays agent-run: the `SKILLS-*` rows in [`CHECKLIST.md`](CHECKLIST.md) are read by
hand. The commit-hook checks (`HOOK-01`, `HOOK-02`) report under `verify` because that is the
section whose question they answer — "prove the repo is green" — and they carry a trap worth
knowing: a hook that is committed but not enabled in this clone is `manual`, not `drift`, because
`core.hooksPath` is per-clone config and a fresh CI checkout never has it.

## 2. Run the script

```bash
python3 scripts/audit.py .              # report only, always exits 0
python3 scripts/audit.py . --strict     # exit 1 on a strict finding — use in CI
python3 scripts/audit.py . --json       # machine-readable
python3 scripts/audit.py . --run        # also execute the green-command table
python3 scripts/audit.py . --section rules,verify
```

`--run` executes the repo's documented commands, so it is the one flag that can have a side effect
(destructive commands are refused, not run). Without it, the audit only reads.

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

Then say which are mechanical (the script decided them) and which are the user's call — an
unstated branch topology cannot be read from files, so it is a question, not a finding.

End with the handoff, not an offer to edit: `Fix which? Name the ids — skill `repo-align` applies
them.` A report that edits on the next turn was never read-only.

**Done when** the report is delivered and the audit left the repo byte-identical.

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

- **Never edits the audited repo.** A report is a proposal; the fix is `repo-align`, after the
  user names the finding.
- **Never reports a check it did not run.** A section that was off is not mentioned, and `n/a` is
  said out loud rather than dropped — a missing row reads as a pass.
- **Never treats `manual` as `ok`.** The script's clean run is the mechanical third only.
- **Never invents a command for the green row.** A repo with nothing mechanical to check gets a
  `None yet` row and a question, not a guessed `npm test`.

## Related

- Every check, with detection and fix → [`CHECKLIST.md`](CHECKLIST.md)
- The mechanical checks as code → [`scripts/audit.py`](scripts/audit.py), split by section
  into `audit_model.py`, `audit_rules.py`, `audit_verify.py`, `audit_hooks.py`,
  `audit_structure.py`
- The file-size gate this repo runs in its commit hook →
  [`scripts/check_file_size.py`](scripts/check_file_size.py); the rule is skill
  `verify-change` § The file-size gate
- Applying a finding the user named → skill `repo-align`
- No `AGENTS.md` at all → skill `repo-init`
- Tiers and rule ownership → skill `agent-rules`
- Proof a fix worked → skill `verify-change`
