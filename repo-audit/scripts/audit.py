#!/usr/bin/env python3
"""Audit a repo against the standard, mechanically. Reports; never edits.

This is skill `repo-audit`. `CHECKLIST.md` holds ~40 checks; about a third of
them are decidable by a shell command and a comparison, and those live here. The
rest need judgement ("would an agent break this rule without opening a detail
file?") and are printed as `manual` so a clean run is never mistaken for full
alignment.

Nothing here writes to the audited repo. Applying a fix is skill `repo-align`,
which reads this report.

The checks are split by section so no file carries the whole audit:

    audit_model.py      Finding, Context, and the shared regex vocabulary
    audit_rules.py      AGENTS.md, rule cap, tiers, duplication, harness shims
    audit_verify.py     the green-command table, what CI actually runs
    audit_hooks.py      commit-hook scope and wiring, branch topology
    audit_structure.py  folder shape, .env.example, the skills store

Usage:
    python3 audit.py [path]              report only, always exits 0
    python3 audit.py --strict            exit 1 when a strict check drifts
    python3 audit.py --json              machine-readable findings
    python3 audit.py --section rules,verify
    python3 audit.py --run               also execute the green-command table

Exit codes: 0 clean or report-only, 1 strict drift, 2 bad invocation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from audit_hooks import check_branch_topology, check_hook_scope, check_hook_wiring
from audit_model import SECTIONS, Context, Finding
from audit_rules import (
    check_agents_length,
    check_agents_present,
    check_rule_cap,
    check_rule_dup,
    check_rule_noop,
    check_shim_claude,
    check_shim_cursor,
)
from audit_structure import (
    check_docs_scripts,
    check_dump_folders,
    check_env_example,
    check_store_ignored,
    check_store_matches_lock,
)
from audit_verify import check_verify_ci, check_verify_runs, check_verify_table


# ── manual ───────────────────────────────────────────────────────────────────

MANUAL = (
    ("RULE-TIER-01", "rules", "Is each hard rule needed every session, or is it detail?"),
    ("RULE-BOUND-01", "rules", "Does each prohibition name a concrete boundary?"),
    ("RULE-REG-01", "rules", "Is there a registry mapping rule -> owner -> detail?"),
    ("VERIFY-05", "verify", "Does each test fail before the fix and pass after?"),
    ("STRUCT-01", "structure", "Can every top-level folder be justified in one line?"),
    ("DESIGN-02", "design", "Do the design docs still match the tokens in code?"),
    ("DESIGN-03", "design", "Do raw colour literals sit outside the token layer?"),
)

def run_checks(ctx: Context, sections: set[str], run: bool) -> list[Finding]:
    findings: list[Finding] = []
    for fn in (
        check_agents_present,
        check_agents_length,
        check_rule_cap,
        check_shim_claude,
        check_shim_cursor,
        check_rule_dup,
        check_rule_noop,
        check_verify_table,
        check_verify_ci,
        check_hook_scope,
        check_hook_wiring,
        check_branch_topology,
        check_dump_folders,
        check_docs_scripts,
        check_env_example,
        check_store_ignored,
        check_store_matches_lock,
    ):
        findings.append(fn(ctx))
    findings.append(check_verify_runs(ctx, run))
    for cid, section, question in MANUAL:
        findings.append(
            Finding(cid, section, "manual", question, "Needs agent judgement; see CHECKLIST.md.")
        )
    return [f for f in findings if f.section in sections]

# ── output ───────────────────────────────────────────────────────────────────


def print_report(findings: list[Finding], root: Path, kind: str = "code") -> None:
    order = {"drift": 0, "missing": 1, "manual": 2, "ok": 3, "n/a": 4}
    # State the kind: a downgraded check that does not say why reads as a bug.
    print(f"Auditing {root}  (kind: {kind})\n")
    for section in SECTIONS:
        group = [f for f in findings if f.section == section]
        if not group:
            continue
        group.sort(key=lambda f: (order.get(f.status, 5), f.id))
        drift = sum(1 for f in group if f.status == "drift")
        missing = sum(1 for f in group if f.status == "missing")
        manual = sum(1 for f in group if f.status == "manual")
        ok = sum(1 for f in group if f.status == "ok")
        na = sum(1 for f in group if f.status == "n/a")
        parts = [
            f"{n} {label}"
            for n, label in (
                (drift, "drift"), (missing, "missing"), (manual, "manual"),
                (ok, "ok"), (na, "n/a"),
            )
            if n
        ]
        print(f"## {section} — {', '.join(parts)}")
        print("| # | Check | Status | Finding | Fix |")
        print("| - | ----- | ------ | ------- | --- |")
        for i, f in enumerate(group, 1):
            # Both cells can carry a pipe — a fix that quotes a `| Check |` table
            # header is the common one — and a raw one splits the row and shifts
            # every column after it. Escape, don't strip: the reader needs the
            # character to know what the fix is asking for.
            fix = (f.fix if f.bad else "").replace("|", "\\|")
            detail = f.detail.replace("|", "\\|")
            print(f"| {i} | {f.id} | {f.status} | {detail} | {fix} |")
        print()

    counts = {s: sum(1 for f in findings if f.status == s) for s in
              ("ok", "drift", "missing", "manual", "n/a")}
    strict_bad = [f for f in findings if f.strict and f.bad]
    summary = [
        f"{len(findings)} checks",
        f"{counts['ok']} ok",
        f"{counts['drift']} drift",
        f"{counts['missing']} missing",
        f"{counts['manual']} manual",
        f"{counts['n/a']} n/a",
    ]
    print(", ".join(summary))
    if strict_bad:
        print(f"{len(strict_bad)} blocking (strict): {', '.join(f.id for f in strict_bad)}")
        print("Apply which? Name the check ids. Nothing has been edited.")


def ctx_read(root: Path) -> str | None:
    p = root / "AGENTS.md"
    return p.read_text(errors="replace") if p.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a repo against the standard.")
    ap.add_argument("path", nargs="?", default=".", help="repo root (default: cwd)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any strict finding")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--run", action="store_true", help="execute the green-command table")
    ap.add_argument(
        "--section",
        default=",".join(SECTIONS),
        help=f"comma-separated sections (default: {','.join(SECTIONS)})",
    )
    args = ap.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    sections = {s.strip() for s in args.section.split(",") if s.strip()}
    unknown = sections - set(SECTIONS)
    if unknown:
        print(f"unknown section(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    ctx = Context(root=root, agents=ctx_read(root))
    findings = run_checks(ctx, sections, args.run)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print_report(findings, root, ctx.kind)

    strict_bad = [f for f in findings if f.strict and f.bad]
    return 1 if (args.strict and strict_bad) else 0

if __name__ == "__main__":
    sys.exit(main())
