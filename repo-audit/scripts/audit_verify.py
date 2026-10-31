"""Section `verify` — is there a green command, and does CI run it?

The commands table is the repo's falsifiable definition of done: what to run and
what it prints when it passes. `--run` executes it, CI must call the same
commands, and a repo with nothing mechanical to check says so in one row rather
than inventing a command.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from audit_model import DANGEROUS, GREEN_WHEN, NO_CHECK_ROW, TABLE_COMMAND, Context, Finding

# ── verify ───────────────────────────────────────────────────────────────────


def documented_commands(ctx: Context) -> list[tuple[str, str]]:
    """Rows of a commands table, and only those.

    A backticked second cell is not enough: the AGENTS.md index table
    (`| Area | Load it when |`) also has one, and counting it as a command made
    VERIFY-01 report "ok" on a repo with no check at all — then `--run` tried to
    execute a markdown filename. A commands table is identified by its header
    (or by a row that states its own green condition), not by shape alone.
    """
    if ctx.agents is None:
        return []
    out = []
    in_commands = False
    for line in ctx.agents.splitlines():
        if not line.lstrip().startswith("|"):
            in_commands = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # A header row names the pass condition; the separator row follows it.
        if any(GREEN_WHEN.search(c) for c in cells):
            in_commands = True
        m = TABLE_COMMAND.match(line)
        if not m:
            continue
        label, cmd = m.group(1).strip(), m.group(2).strip()
        if not cmd or cmd.startswith("…"):
            continue
        # In a commands table every row counts. Outside one, only a row that
        # states its own green condition does.
        if in_commands or any(GREEN_WHEN.search(c) for c in cells[2:]):
            out.append((label, cmd))
    return out


def check_verify_table(ctx: Context) -> Finding:
    if ctx.agents is None:
        return Finding("VERIFY-01", "verify", "n/a", "no AGENTS.md", strict=True)
    cmds = documented_commands(ctx)
    if not cmds:
        # A non-coding repo may honestly have no mechanical check. That is a
        # finding, not a failure: "None yet" is the repo saying how much proof
        # exists, which is exactly what this table is for. Demanding a command
        # would push the author to invent one.
        if NO_CHECK_ROW.search(ctx.agents):
            return Finding(
                "VERIFY-01", "verify", "manual",
                "commands table declares no mechanical check",
                "Confirm that is true, then leave it; a guessed command is worse than none.",
                strict=True,
            )
        if not GREEN_WHEN.search(ctx.agents):
            return Finding(
                "VERIFY-01", "verify", "missing", "no green-command table in AGENTS.md",
                "Add a `| Check | Command | Green when |` table; without it 'it works' is unfalsifiable.",
                strict=True,
            )
    return Finding("VERIFY-01", "verify", "ok", f"{len(cmds)} documented command(s)", strict=True)


def check_verify_runs(ctx: Context, run: bool) -> Finding:
    cmds = documented_commands(ctx)
    if not cmds:
        return Finding("VERIFY-02", "verify", "n/a", "no documented commands", strict=True)
    if not run:
        return Finding(
            "VERIFY-02", "verify", "manual", f"{len(cmds)} command(s) not executed",
            "Re-run with `--run` to prove each exits 0.", strict=True,
        )
    failures = []
    for label, cmd in cmds:
        if any(d in cmd.lower() for d in DANGEROUS):
            failures.append(f"{label}: refused (destructive)")
            continue
        try:
            r = subprocess.run(
                cmd, shell=True, cwd=ctx.root, capture_output=True, text=True, timeout=300
            )
        except (OSError, subprocess.SubprocessError) as exc:
            failures.append(f"{label}: {exc}")
            continue
        if r.returncode != 0:
            first = (r.stderr or r.stdout).strip().splitlines()
            failures.append(f"{label}: exit {r.returncode} — {first[0] if first else 'no output'}")
    if failures:
        return Finding(
            "VERIFY-02", "verify", "drift", "; ".join(failures[:4]),
            "Fix the command or delete the row — never leave a broken row.", strict=True,
        )
    return Finding("VERIFY-02", "verify", "ok", f"{len(cmds)} command(s) exit 0", strict=True)


def _runs(cmd: str, body: str) -> bool:
    """Is `cmd` actually invoked in the workflow bodies?

    A substring test is wrong in both directions. `bun run build` must not be
    satisfied by `bun run build:ci` (a different script) or by a documented
    `install` inside `bun install` (an argument, not a command), and it must be
    by `bun run build --filter=portfolio` (the same script with a flag).

    So both ends are bounded: before the command, no character that would make
    it part of a longer word or path; after it, none that would continue it.
    Whitespace is normalised on both sides, because a workflow wraps its `run:`
    lines and a table cell is written on one.
    """
    pattern = r"(?<![\w./-])" + re.escape(" ".join(cmd.split())) + r"(?![\w:=\-./])"
    return re.search(pattern, body) is not None


def _workflow_body(wf: list[Path]) -> str:
    """Every workflow, with YAML comments dropped and whitespace collapsed.

    A comment is not an execution: `# TODO: bun run build` used to satisfy
    VERIFY-03 with no step running it. Only whole-line comments are removed —
    a `#` mid-line is left alone, because it is as likely to be inside a quoted
    string or a URL as to be a comment, and a false "CI never runs" is the
    failure this check exists to avoid.
    """
    kept = []
    for path in wf:
        for line in path.read_text(errors="replace").splitlines():
            if line.lstrip().startswith("#"):
                continue
            kept.append(line)
    return " ".join(" ".join(kept).split())


def check_verify_ci(ctx: Context) -> Finding:
    wf = sorted(ctx.path(".github/workflows").glob("*.y*ml")) if ctx.path(".github/workflows").is_dir() else []
    if not wf:
        # CI's job is to run the commands table. With no commands there is
        # nothing for it to run, and that gap is already VERIFY-01's finding —
        # reporting it twice teaches the reader to skim. Holds for any repo
        # kind: a code repo mid-setup has the same non-problem.
        if not documented_commands(ctx):
            return Finding(
                "VERIFY-03", "verify", "n/a",
                "no CI, and no documented command for it to run",
                "Add the check first (VERIFY-01), then a job that runs it.",
                strict=True,
            )
        # A repo with a check but no build: CI is cheap to add, not mandatory.
        # Blocking here pushes a notes repo toward a badge that proves nothing,
        # which reads as proof and is worse than none.
        if ctx.is_non_coding:
            return Finding(
                "VERIFY-03", "verify", "manual",
                "no CI, and this repo has no build",
                "Optional. If the documented check is cheap, one job is worth it.",
                strict=True,
            )
        return Finding(
            "VERIFY-03", "verify", "missing", "no .github/workflows/*.yml",
            "Add one job that runs the same commands as local.", strict=True,
        )
    body = _workflow_body(wf)
    # The whole command, at a command boundary. Comparing `c.split()[0]` meant
    # a workflow mentioning `bun` once satisfied every row starting with `bun`:
    # `bun run build` passed on a CI that only ran `bun install`. A plain
    # substring inherits the same class of false pass at the other end.
    missing = [c for _, c in documented_commands(ctx) if not _runs(c, body)]
    if missing:
        return Finding(
            "VERIFY-03", "verify", "drift", f"CI never runs: {', '.join(missing[:4])}",
            "Make CI call the same scripts; a different command set finds different bugs.",
            strict=True,
        )
    return Finding("VERIFY-03", "verify", "ok", f"{len(wf)} workflow(s) cover the table", strict=True)

