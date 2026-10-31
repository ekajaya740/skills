#!/usr/bin/env python3
"""Audit a repo against the standard, mechanically.

This is the deterministic half of skill `repo-align`. `CHECKLIST.md` holds ~40
checks; about a third of them are decidable by a shell command and a comparison,
and those live here. The rest need judgement ("would an agent break this rule
without opening a detail file?") and are printed as `manual` so a clean run is
never mistaken for full alignment.

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
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

SECTIONS = ("rules", "structure", "verify", "design")
MAX_AGENTS_LINES = 150
MAX_HARD_RULES = 7
# A repo that documents its own tier test may declare its own budget, in AGENTS.md:
#   rules-budget: 12   (inline or on its own line, anywhere in AGENTS.md)
# The cap is a heuristic, not a law: a repo whose rules each pass a stated binding
# test knows better than this script does. Without a declaration the default holds.
RULES_BUDGET = re.compile(r"rules-budget:\s*(\d+)")
# Evidence that a repo stated the admission test, which is what makes a budget a
# judgement rather than a silencer. Either the decisive question, or a table that
# names a binding tier and a detail/on-demand tier.
TIER_TEST_QUESTION = re.compile(r"would an agent that never opened|never opened the detail file")
TIER_TEST_TABLE = re.compile(
    r"\|\s*\**binding\**\s*\|[^\n]*\n[^\n]*\|\s*\**detail\**\s*\|"
    r"|\|\s*\**detail\**\s*\|[^\n]*\n[^\n]*\|\s*\**binding\**\s*\|"
)
SHIM_POINTER = "@AGENTS.md"

# Commands that must never be executed by --run, however they got into a doc.
DANGEROUS = (
    "rm -rf",
    "rm -fr",
    "drop table",
    "drop database",
    "truncate ",
    "git push --force",
    "git push -f",
    "git reset --hard",
    "| sh",
    "| bash",
    "mkfs",
    "dd if=",
)

STOPWORDS = frozenset(
    """a an the and or but if then than that this these those is are was were be been
    being to of in on at by for with from into over under again further once here there
    when where why how all any both each few more most other some such no nor not only
    own same so too very can will just should now it its it's we you your they them
    their he she his her do does did doing have has had having would could may might
    must shall""".split()
)

NOOP_PHRASES = (
    "write clean code",
    "be thorough",
    "follow best practices",
    "use best practices",
    "be careful",
    "think before you code",
    "use good judgment",
    "use good judgement",
    "keep it simple",
    "avoid bugs",
    "write quality code",
    "be consistent",
    "don't break things",
    "do your best",
)

RULE_VERB = re.compile(
    r"\b(never|always|must|must not|do not|don't|forbidden|required|only)\b", re.I
)
FENCE = re.compile(r"^```")
BULLET_RULE = re.compile(r"^-\s+\*\*")
TABLE_COMMAND = re.compile(r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|")

# Either phrasing is a real green-check table. A non-coding repo naturally says
# "passes when"; rejecting that would fail a repo for describing itself honestly.
GREEN_WHEN = re.compile(r"\b(green when|passes when|green if|passes if)\b", re.I)

# The honest row for a repo with nothing mechanical to check.
NO_CHECK_ROW = re.compile(r"^\|\s*none( yet)?\s*\|", re.I | re.M)

# A repo may state what it is instead of making the audit guess. Declared beats
# detected: the filesystem cannot tell a docs-heavy code repo from a vault.
KIND_DECL = re.compile(
    # Tolerate the markdown around it: `- **Kind:** `code``, `Kind: knowledge`, bare.
    r"^\s*(?:[-*]\s+)?\*{0,2}kind\b[^\w\n]{0,6}(code|knowledge)\b", re.I | re.M
)


@dataclass
class Finding:
    id: str
    section: str
    status: str  # ok | drift | missing | n/a | manual
    detail: str
    fix: str = ""
    strict: bool = False

    @property
    def bad(self) -> bool:
        return self.status in ("drift", "missing")


@dataclass
class Context:
    root: Path
    agents: str | None = None
    git_files: list[str] = field(default_factory=list)

    def path(self, rel: str) -> Path:
        return self.root / rel

    @property
    def is_empty(self) -> bool:
        """Nothing but .git. Distinct from a repo that simply has no manifest."""
        try:
            return not any(e.name != ".git" for e in self.root.iterdir())
        except OSError:
            return False

    @property
    def declared_kind(self) -> str | None:
        """`Kind: code` / `Kind: knowledge` from AGENTS.md, when stated.

        A repo knows what it is; the filesystem only hints. Guessing alone
        misreads a docs-heavy code repo and a code repo before its first
        manifest, and both would silently lose checks they should run.
        """
        if not self.agents:
            return None
        m = KIND_DECL.search(self.agents)
        return m.group(1).strip().lower() if m else None

    @property
    def kind(self) -> str:
        """`code`, `knowledge`, or `empty` — declared when stated, else guessed."""
        if self.is_empty:
            return "empty"
        declared = self.declared_kind
        if declared in ("code", "knowledge"):
            return declared
        manifests = (
            "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
            "Makefile", "justfile", "build.gradle", "pom.xml", "deno.json",
        )
        if any(self.path(m).is_file() for m in manifests):
            return "code"
        return "code" if self.path(".github/workflows").is_dir() else "knowledge"

    @property
    def is_non_coding(self) -> bool:
        """Content exists, but nothing declares a build.

        A docs vault, a research corpus or a writing repo has no package.json and
        no Makefile, yet is a real repo with real conventions. Treating it as an
        empty folder, or demanding it compile, is wrong in both directions.
        """
        return self.kind == "knowledge"

    def read(self, rel: str) -> str | None:
        p = self.path(rel)
        if not p.is_file():
            return None
        try:
            return p.read_text(errors="replace")
        except OSError:
            return None

    def md_files(self, limit: int = 60) -> list[Path]:
        out = [
            p
            for p in sorted(self.root.rglob("*.md"))
            if not any(
                part in {".git", "node_modules", ".agents", "dist", "build", ".venv"}
                for part in p.relative_to(self.root).parts
            )
        ]
        return out[:limit]

    def git(self, *args: str) -> str:
        try:
            r = subprocess.run(
                ("git",) + args, cwd=self.root, capture_output=True, text=True, timeout=30
            )
            return r.stdout if r.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""


# ── rules ────────────────────────────────────────────────────────────────────


def check_agents_present(ctx: Context) -> Finding:
    if ctx.agents is None:
        return Finding(
            "AGENTS-01", "rules", "missing", "no AGENTS.md at the repo root",
            "Run skill `repo-init`; a fresh agent has nothing to land in.", strict=True,
        )
    return Finding("AGENTS-01", "rules", "ok", "AGENTS.md present", strict=True)


def check_agents_length(ctx: Context) -> Finding:
    if ctx.agents is None:
        return Finding("AGENTS-02", "rules", "n/a", "no AGENTS.md", strict=True)
    n = len(ctx.agents.splitlines())
    if n > MAX_AGENTS_LINES:
        return Finding(
            "AGENTS-02", "rules", "drift", f"{n} lines (cap ~{MAX_AGENTS_LINES})",
            "Move the excess to docs/agents/<area>.md and leave one pointer line.",
            strict=True,
        )
    return Finding("AGENTS-02", "rules", "ok", f"{n} lines", strict=True)


def check_rule_cap(ctx: Context) -> Finding:
    if ctx.agents is None:
        return Finding("RULE-CAP-01", "rules", "n/a", "no AGENTS.md", strict=True)
    n = sum(1 for line in ctx.agents.splitlines() if BULLET_RULE.match(line))
    declared = RULES_BUDGET.search(ctx.agents)
    cap = MAX_HARD_RULES
    where: str | None = None
    if declared:
        # A budget is a claim about the repo's own admission test, so it is only
        # honoured when that test is written down elsewhere. Otherwise any agent
        # could bump the number to silence this check -- the failure mode the cap
        # exists to prevent.
        where = _tier_test_source(ctx)
        if where is None:
            return Finding(
                "RULE-CAP-01", "rules", "drift",
                f"{n} bolded hard rules; declared `rules-budget: {declared.group(1)}` "
                f"but no tier test is documented outside AGENTS.md",
                "State the admission test in a detail doc -- which rules must be read every "
                "session, and which bind only in their situation -- or drop the declaration and "
                "use the default cap of 7. A budget with no test behind it is a mute button.",
                strict=True,
            )
        cap = int(declared.group(1))
    if n > cap:
        origin = f"declared `rules-budget`, test in {where}" if where else "default cap"
        return Finding(
            "RULE-CAP-01", "rules", "drift",
            f"{n} bolded hard rules ({origin} ~{cap})",
            "Demote the weakest to a detail file; a rule list nobody finishes is not read.",
            strict=True,
        )
    note = f"{n} hard rules (budget {cap}, test in {where})" if where else f"{n} hard rules"
    return Finding("RULE-CAP-01", "rules", "ok", note, strict=True)


def _tier_test_source(ctx: Context) -> str | None:
    """A doc, other than AGENTS.md, that states the rule-admission test.

    A declared budget is only meaningful next to a stated test, and the test must
    live outside the file that declares the budget: otherwise the declaration is
    its own justification, and any agent can raise the number by adding a
    sentence. The repo has to say, somewhere a reader lands when asking why a rule
    is binding, how a rule earns that place.
    """
    preferred = ("docs/agents/rules.md", "docs/agents/README.md", "RULES.md", "docs/rules.md")
    candidates: list[tuple[str, str | None]] = [(rel, ctx.read(rel)) for rel in preferred]
    seen = {rel for rel, _ in candidates} | {"AGENTS.md"}
    for p in ctx.md_files():
        rel = str(p.relative_to(ctx.root))
        if rel in seen:
            continue
        candidates.append((rel, ctx.read(rel)))
    for rel, text in candidates:
        if not text:
            continue
        low = text.lower()
        if TIER_TEST_QUESTION.search(low) or TIER_TEST_TABLE.search(low):
            return rel
    return None


def _is_pointer(text: str) -> bool:
    stripped = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return len(stripped) <= 3 and SHIM_POINTER in text and "## " not in text


def check_shim_claude(ctx: Context) -> Finding:
    text = ctx.read("CLAUDE.md")
    if text is None:
        return Finding(
            "SHIM-01", "rules", "n/a", "no CLAUDE.md",
            f"Add one line, `{SHIM_POINTER}`, if Claude Code is used here.", strict=True,
        )
    if _is_pointer(text):
        return Finding("SHIM-01", "rules", "ok", "CLAUDE.md points at AGENTS.md", strict=True)
    return Finding(
        "SHIM-01", "rules", "drift", f"CLAUDE.md restates content ({len(text.splitlines())} lines)",
        "Extract its rules into AGENTS.md or docs/agents/ (RULE-SHIM-01), then replace the file "
        f"with the single line `{SHIM_POINTER}`.",
        strict=True,
    )


def check_shim_cursor(ctx: Context) -> Finding:
    rules = sorted(ctx.path(".cursor/rules").glob("*.mdc"))
    if not rules:
        return Finding("SHIM-02", "rules", "n/a", "no .cursor/rules/*.mdc", strict=True)
    offenders = []
    for p in rules:
        body = p.read_text(errors="replace")
        if SHIM_POINTER not in body and ("## " in body or body.count("\n- ") >= 3):
            offenders.append(p.name)
    if offenders:
        return Finding(
            "SHIM-02", "rules", "drift", f"restates rules instead of pointing: {', '.join(offenders)}",
            "Keep `alwaysApply: true`; extract the rules into AGENTS.md or docs/agents/ "
            "(RULE-SHIM-01), then replace the body with `See AGENTS.md`.",
            strict=True,
        )
    return Finding("SHIM-02", "rules", "ok", f"{len(rules)} cursor rule file(s)", strict=True)


def _rule_lines(text: str) -> list[str]:
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or not RULE_VERB.search(line):
            continue
        cleaned = re.sub(r"[`*_#>|]", " ", line.lower())
        words = [w for w in re.findall(r"[a-z0-9'-]{3,}", cleaned)]
        if words:
            out.append(" ".join(words))
    return out


def _shingles(line: str, n: int = 5) -> set[str]:
    words = line.split()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def _substantial(shingle: str) -> bool:
    """A phrase worth reporting: three or more content words, not filler."""
    return sum(1 for w in shingle.split() if w not in STOPWORDS) >= 3


LINK = re.compile(r"\]\(([^)]+)\)")


def _linked_targets(line: str) -> set[str]:
    """Repo-relative paths a rule line points at — its detail docs."""
    out = set()
    for target in LINK.findall(line):
        if target.startswith(("http://", "https://", "#")):
            continue
        out.add(target.split("#", 1)[0].lstrip("./"))
    return out


def _rule_blocks(text: str) -> list[tuple[str, set[str]]]:
    """A rule as an agent reads it: the whole bullet, plus the docs it links.

    AGENTS.md wraps rules across lines, and the pointer usually lands on the
    last one. Reading line-by-line loses the link and invents a duplicate.
    """
    blocks: list[tuple[list[str], set[str]]] = []
    current: list[str] | None = None
    for raw in text.splitlines():
        starts = raw.startswith(("- ", "* ", "| "))
        if starts:
            if current:
                blocks.append((current, set()))
            current = [raw]
        elif current is not None and raw.startswith((" ", "\t")) and raw.strip():
            current.append(raw)
        elif raw.strip() and not raw.startswith(" "):
            if current:
                blocks.append((current, set()))
            current = None
        elif current:
            blocks.append((current, set()))
            current = None
    if current:
        blocks.append((current, set()))

    out = []
    for lines, _ in blocks:
        body = " ".join(lines)
        if not RULE_VERB.search(body):
            continue
        out.append((body, _linked_targets(body)))
    return out


def check_rule_dup(ctx: Context) -> Finding:
    """A rule restated in a doc it links to is the owner+pointer pattern, not drift.

    Only an unlinked restatement is a second source of truth: nothing ties the
    two together, so they drift and the weaker copy wins.
    """
    if ctx.agents is None:
        return Finding("RULE-DUP-01", "rules", "n/a", "no AGENTS.md")

    mine: dict[str, set[str]] = {}
    for body, linked in _rule_blocks(ctx.agents):
        for line in _rule_lines(body):
            for sh in _shingles(line):
                if _substantial(sh):
                    mine.setdefault(sh, set()).update(linked)

    hits: list[str] = []
    seen: set[str] = set()
    for md in ctx.md_files():
        if md.name == "AGENTS.md":
            continue
        rel = str(md.relative_to(ctx.root))
        if rel.startswith((".plans/", ".agents/")) or "CHANGELOG" in rel:
            continue
        here = md.parent.relative_to(ctx.root)
        for body, linked in _rule_blocks(md.read_text(errors="replace")):
            match = next(
                (sh for sh in _shingles(body) if sh in mine and _substantial(sh)), None
            )
            if match is None:
                continue
            if any(rel == t or rel.endswith("/" + t) for t in mine[match]):
                break  # AGENTS.md owns it and links here; that is the pattern
            # Links are written relative to the doc holding them; compare repo-relative.
            resolved = {str((here / t).as_posix()) for t in linked}
            if resolved & mine[match]:
                break  # both sites point at the same detail doc: one owner
            if rel not in seen:
                seen.add(rel)
                hits.append(f'{rel}: "{match}"')
            break
        if len(hits) >= 5:
            break

    if hits:
        return Finding(
            "RULE-DUP-01", "rules", "drift",
            f"{len(hits)} rule phrase(s) also stated elsewhere: " + "; ".join(hits),
            "Keep AGENTS.md as owner; make the other site a pointer.",
        )
    return Finding("RULE-DUP-01", "rules", "ok", "no duplicated rule phrasing found")


def check_rule_noop(ctx: Context) -> Finding:
    if ctx.agents is None:
        return Finding("RULE-NOOP-01", "rules", "n/a", "no AGENTS.md")
    low = ctx.agents.lower()
    found = [p for p in NOOP_PHRASES if p in low]
    if found:
        return Finding(
            "RULE-NOOP-01", "rules", "drift", "no-op rule(s): " + ", ".join(f'"{p}"' for p in found),
            "Delete. A competent agent already does this; the line costs every session.",
        )
    return Finding("RULE-NOOP-01", "rules", "ok", "no known no-op phrasing")


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
    body = "\n".join(p.read_text(errors="replace") for p in wf)
    missing = [c for _, c in documented_commands(ctx) if c.split()[0] not in body]
    if missing:
        return Finding(
            "VERIFY-03", "verify", "drift", f"CI never runs: {', '.join(missing[:4])}",
            "Make CI call the same scripts; a different command set finds different bugs.",
            strict=True,
        )
    return Finding("VERIFY-03", "verify", "ok", f"{len(wf)} workflow(s) cover the table", strict=True)


# ── commit hook ──────────────────────────────────────────────────────────────


# A hook that runs these has become the full suite, which is the thing
# `--no-verify` exists to escape. Matched against the hook body, case-insensitively.
FULL_SUITE_IN_HOOK = (
    "run build", "run test", "bun test", "npm test", "pnpm test", "yarn test",
    "pytest", "audit.py", "tsc --noEmit", "vitest run", "jest",
)


def _hook_candidates(ctx: Context) -> list[Path]:
    """Hook files that would actually run: no `.sample` stubs, no `_` helpers."""
    out: list[Path] = []
    for d in (".githooks", ".husky", ".git/hooks"):
        base = ctx.path(d)
        if not base.is_dir():
            continue
        for p in sorted(base.iterdir()):
            if not p.is_file() or p.suffix == ".sample" or p.name in {"h", "_"}:
                continue
            if p.name in {"pre-commit", "pre-push", "commit-msg"}:
                out.append(p)
    return out


def _git_status(ctx: Context, *args: str) -> tuple[int, str]:
    """Exit code plus stdout. `Context.git` drops the code, which these need."""
    try:
        r = subprocess.run(
            ("git",) + args, cwd=ctx.root, capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return 127, ""
    return r.returncode, r.stdout


def _hook_executable(ctx: Context, p: Path) -> bool:
    """Whether git will actually run this hook.

    For a tracked hook the mode bit that matters is the one in the index: a
    checkout with `core.fileMode=false`, or a umask that dropped the bit, can
    disagree with it on disk, and git decides from the index for tracked files.
    An untracked hook — everything under `.git/hooks/` — falls back to the
    filesystem, which is the only record it has.
    """
    try:
        rel = str(p.resolve().relative_to(ctx.root.resolve()))
    except ValueError:
        return os.access(p, os.X_OK)
    rc, out = _git_status(ctx, "ls-files", "-s", "--", rel)
    if rc == 0 and out.strip():
        return out.split()[0] == "100755"
    return os.access(p, os.X_OK)


def check_hook_scope(ctx: Context) -> Finding:
    """HOOK-01 — a commit gate must stay cheap; the full suite belongs in CI.

    Only commit-time hooks are judged. A suite in `pre-push` is legitimate: the
    developer is already waiting on a network round trip, so the calculus that
    makes a slow `pre-commit` a bypass magnet does not apply.

    Comment lines are stripped before matching, because a hook that *explains*
    why it avoids the suite must not be read as running one — this repository's
    own hook names `audit.py` in a comment for exactly that reason.
    """
    hooks = [p for p in _hook_candidates(ctx) if p.name in {"pre-commit", "commit-msg"}]
    if not hooks:
        return Finding(
            "HOOK-01", "verify", "ok",
            "no commit-time hook (optional, and cheap to skip)",
        )
    problems: list[str] = []
    for p in hooks:
        code = "\n".join(
            line
            for line in p.read_text(errors="replace").splitlines()
            if not line.lstrip().startswith("#")
        ).lower()
        hit = [c for c in FULL_SUITE_IN_HOOK if c.lower() in code]
        if hit:
            problems.append(f"{p.name} runs {hit[0]!r}")
        elif not _hook_executable(ctx, p):
            # Git silently skips a non-executable hook: the file looks present
            # and nothing runs, which is worse than having no hook at all.
            problems.append(f"{p.name} is not executable")
    if problems:
        return Finding(
            "HOOK-01", "verify", "drift", "; ".join(problems[:3]),
            "Keep lint, format and the repo's one cheap gate in the commit hook; move the suite to "
            "CI and `chmod +x` the file. A hook that runs everything is bypassed with --no-verify, "
            "and then it protects nothing. See skill `verify-change` § The commit hook.",
            strict=True,
        )
    return Finding(
        "HOOK-01", "verify", "ok", f"{len(hooks)} commit hook(s), none runs the suite", strict=True
    )


def check_hook_wiring(ctx: Context) -> Finding:
    """HOOK-02 — shipped wiring is a fact, local wiring is a judgement.

    `core.hooksPath` is per-clone config: it is never in a fresh checkout, so a
    missing local value is not drift — a strict check here would fail CI for a
    repo that correctly ships the hook and leaves enabling it to the developer.
    What *is* drift is the hook being uncommittable (ignored by a deny-by-default
    `.gitignore`) or unshipped, because then no clone can ever enable it.
    """
    hooks = _hook_candidates(ctx)
    pre = [p for p in hooks if p.name == "pre-commit"]
    if not pre:
        return Finding("HOOK-02", "verify", "ok", "no pre-commit hook to wire", strict=True)
    rel = str(pre[0].relative_to(ctx.root))

    rc, _ = _git_status(ctx, "ls-files", "--error-unmatch", rel)
    if rc != 0:
        if _git_status(ctx, "check-ignore", "-q", rel)[0] == 0:
            return Finding(
                "HOOK-02", "verify", "drift",
                f"{rel} is ignored by .gitignore, so it can never be committed",
                f"Add `!/{rel.split('/')[0]}/` to the allowlist. In a deny-by-default "
                "`.gitignore` the hook is silently left out of every clone.",
                strict=True,
            )
        return Finding(
            "HOOK-02", "verify", "manual",
            f"{rel} exists but is not committed",
            "Commit it. A hook that only lives on one machine is not wiring.",
            strict=True,
        )

    rc, configured = _git_status(ctx, "config", "--get", "core.hooksPath")
    wanted = rel.split("/")[0]
    # Compare resolved paths, not strings: `.githooks`, `.githooks/` and the
    # absolute form git may store are the same answer, and stripping "./" would
    # eat the leading dot of a dotted directory name.
    wired = False
    if rc == 0 and configured.strip():
        got = Path(configured.strip()).expanduser()
        if not got.is_absolute():
            got = ctx.root / got
        got = got.resolve()
        # Husky points core.hooksPath at its shim dir (`.husky/_`), whose
        # `pre-commit` sources `../pre-commit`. That is correct wiring, not a
        # miss: accept the directory or a shim dir directly inside it.
        wired = got == (ctx.root / wanted).resolve() or (
            got.parent == (ctx.root / wanted).resolve() and got.name == "_"
        )
    if wired:
        return Finding(
            "HOOK-02", "verify", "ok", f"{rel} committed, wired to {wanted}/", strict=True
        )
    return Finding(
        "HOOK-02", "verify", "manual",
        f"{rel} is committed but this clone does not run it",
        f"Enable it: `git config core.hooksPath {wanted}`. Confirm the repo documents that "
        "command in AGENTS.md or the README — local config is never cloned, so the command "
        "is the only thing that can ship. See skill `verify-change` § The commit hook.",
        strict=True,
    )



BRANCH_HEADER = re.compile(r"^\|\s*`?branch\b.*\|\s*$", re.I | re.M)


def check_branch_topology(ctx: Context) -> Finding:
    """BRANCH-01: a repo with more than one branch states what each one is for.

    The interesting failure is not a missing table in a repo with one branch.
    It is a repo with staging, docs and a stale `master` alongside `main`,
    where nobody recorded which mirrors production: tags point at the wrong
    ref, a docs edit triggers a migration, and every session re-derives the
    answer differently. That is drift even though no file is syntactically
    wrong.

    Only the *declaration* is checked. Which branch is production cannot be
    read from files - see skill `workflow` § BRANCHES.md.

    Local branches only: a remote-tracking `origin/main` is a copy of a branch
    the docs already name, so counting it would demand a row per remote.
    """
    rc, out = _git_status(ctx, "branch", "--format=%(refname:short)")
    if rc != 0:
        return Finding("BRANCH-01", "structure", "manual", "not a git repository", strict=True)
    local = sorted(b.strip() for b in out.splitlines() if b.strip())
    if len(local) <= 1:
        return Finding(
            "BRANCH-01", "structure", "ok",
            "one branch, so no topology to state", strict=True,
        )
    # Any area doc may own it: PROFILL keeps the table in `merge-policy.md`,
    # and a second copy in `version-control.md` would be the drift the repo
    # forbids. Look everywhere the standard allows and accept the first hit.
    docs = [ctx.path("AGENTS.md")]
    if ctx.path("docs/agents").is_dir():
        docs += sorted(ctx.path("docs/agents").glob("*.md"))
    for p in docs:
        if not p.is_file():
            continue
        text = p.read_text(errors="replace")
        if BRANCH_HEADER.search(text):
            return Finding(
                "BRANCH-01", "structure", "ok",
                f"topology stated in {p.relative_to(ctx.root)} ({len(local)} local branches)",
                strict=True,
            )
    return Finding(
        "BRANCH-01", "structure", "missing",
        f"{len(local)} branches and no stated topology",
        "Ask the user which branch is production, which (if any) is staging, and which carry "
        "content only; record it as a `| Branch |` table. Deployments fire per target branch, so "
        "an unstated topology means a merge ships somewhere nobody chose. See skill `workflow` § "
        "BRANCHES.md, and `repo-init` § 1b for the questions.",
        strict=True,
    )

# ── structure ────────────────────────────────────────────────────────────────


SKIP_DIRS = frozenset(
    {
        ".git", "node_modules", ".venv", "venv", "dist", "build", ".next", ".turbo",
        ".cache", "__pycache__", ".pytest_cache", "target", "coverage", ".agents",
        # Bundler and framework output: vendored third-party code, never ours.
        ".wrangler", "storybook-static", ".astro", ".svelte-kit", ".nuxt", ".output",
        ".vercel", ".netlify", ".parcel-cache", ".esbuild",
    }
)


def walk_files(ctx: Context, suffixes: set[str] | None = None, max_depth: int = 8):
    """Yield files, pruning skipped directories before descending into them.

    Filtering after `rglob("*")` still walks node_modules; on a real repo that
    is the difference between one second and forty.
    """
    for dirpath, dirnames, filenames in os.walk(ctx.root):
        rel = Path(dirpath).relative_to(ctx.root)
        if len(rel.parts) >= max_depth:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if suffixes is None or p.suffix in suffixes:
                yield p


def check_dump_folders(ctx: Context) -> Finding:
    bad = []
    for dirpath, dirnames, _ in os.walk(ctx.root):
        rel = Path(dirpath).relative_to(ctx.root)
        if len(rel.parts) > 3:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in dirnames:
            if name in {"utils", "helpers", "shared", "misc", "common"}:
                bad.append(str(rel / name if rel.parts else name))
    if bad:
        return Finding(
            "STRUCT-02", "structure", "drift", "dumping-ground folder(s): " + ", ".join(bad[:5]),
            "Name the concept; split or delete.",
        )
    return Finding("STRUCT-02", "structure", "ok", "no utils/helpers/shared folders")


def check_docs_scripts(ctx: Context) -> Finding:
    missing = [d for d in ("docs", "scripts") if not ctx.path(d).is_dir()]
    if missing:
        return Finding(
            "STRUCT-03", "structure", "missing", "no " + " or ".join(missing) + "/",
            "Create it with one real file; an empty folder is worse than none.",
        )
    return Finding("STRUCT-03", "structure", "ok", "docs/ and scripts/ present")


ENV_PATTERNS = (
    re.compile(r"process\.env\.([A-Za-z_][A-Za-z0-9_]{2,})"),
    re.compile(r"import\.meta\.env\.([A-Za-z_][A-Za-z0-9_]{2,})"),
    re.compile(r"os\.environ\[[\"']([A-Za-z_][A-Za-z0-9_]{2,})[\"']\]"),
    re.compile(r"os\.getenv\([\"']([A-Za-z_][A-Za-z0-9_]{2,})[\"']"),
    re.compile(r"env::var\([\"']([A-Za-z_][A-Za-z0-9_]{2,})[\"']\)"),
    re.compile(r"os\.Getenv\([\"']([A-Za-z_][A-Za-z0-9_]{2,})[\"']\)"),
)

# Runtime-injected, never a repo secret: the bundler or the platform sets these.
BUILTIN_ENV = frozenset(
    {
        "NODE_ENV", "DEV", "PROD", "MODE", "SSR", "BASE_URL", "TEST", "CI",
        "NODE_DEBUG", "PKG_CONFIG_PATH", "PATH", "HOME", "PWD", "SHELL", "TMPDIR",
    }
)

# Test code reads env to build fixtures, not to run the app.
TEST_PARTS = frozenset({"test", "tests", "__tests__", "e2e", "spec", "specs", "fixtures"})


def _declared_elsewhere(ctx: Context) -> set[str]:
    """Vars a fresh clone can discover without .env.example.

    A var set by a committed script, a wrangler/turbo config, or a compose file
    is not undocumented — the file that provides it is in the repo. Reporting
    those as drift trains the reader to ignore the check.
    """
    names: set[str] = set()
    caps = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")

    for rel in (".env.example", ".env.sample", ".env.dist"):
        text = ctx.read(rel) or ""
        names.update(ln.split("=", 1)[0].strip() for ln in text.splitlines() if "=" in ln)

    for p in walk_files(ctx, suffixes={".jsonc", ".json", ".toml", ".yml", ".yaml"}):
        rel = p.relative_to(ctx.root)
        if any(part in {".github", "node_modules"} for part in rel.parts):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        if not re.search(r"wrangler|turbo|compose|docker", p.name, re.I):
            continue
        names.update(m.group(1) for m in re.finditer(r'"([A-Z][A-Z0-9_]{2,})"\s*:', text))

    for p in walk_files(ctx, suffixes={".sh", ".bash", ".zsh"}):
        rel = p.relative_to(ctx.root)
        if "scripts" not in rel.parts and "bin" not in rel.parts:
            continue
        try:
            names.update(caps.findall(p.read_text(errors="replace")))
        except OSError:
            continue

    return names


OPTIONAL = re.compile(
    r"\|\||\?\?|\.get\(|\bor\s+[\"'0-9]|unwrap_or|default\s*[:=]|\?\?="
)


def check_env_example(ctx: Context) -> Finding:
    example = ctx.read(".env.example")
    if example is None:
        return Finding(
            "STRUCT-04", "structure", "n/a", "no .env.example",
            "Add one if the project reads environment variables.",
        )
    declared = _declared_elsewhere(ctx)
    used: dict[str, bool] = {}
    for p in walk_files(ctx, suffixes={".ts", ".tsx", ".js", ".mjs", ".py", ".go", ".rs"}):
        parts = p.relative_to(ctx.root).parts
        if TEST_PARTS & set(parts):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.lstrip().startswith(("//", "#", "*", "/*", "--")):
                continue  # a var named in a comment is documentation, not a read
            optional = bool(OPTIONAL.search(line))
            for pat in ENV_PATTERNS:
                for name in pat.findall(line):
                    if name in BUILTIN_ENV or not name.isupper():
                        continue
                    used[name] = used.get(name, True) and optional
    missing = sorted(n for n, optional in used.items() if not optional and n not in declared)
    if missing:
        return Finding(
            "STRUCT-04", "structure", "drift",
            f"required, read in code, documented nowhere: {', '.join(missing[:6])}",
            "Add to .env.example with no value, same commit.",
        )
    return Finding(
        "STRUCT-04", "structure", "ok",
        f"{len(used)} var(s); every required one is documented or defaulted",
    )


def check_store_ignored(ctx: Context) -> Finding:
    """Third-party skills are never committed. The lock has two valid policies.

    A repo may commit `skills-lock.json` so a fresh clone reinstalls the exact
    set, or ignore it along with the store and treat the whole layer as
    machine-local. Both are coherent; only a store committed *without* a lock is
    not. A lock that is neither tracked nor ignored is just forgotten.
    """
    if not ctx.git("rev-parse", "--is-inside-work-tree").strip():
        return Finding("STRUCT-09", "structure", "n/a", "not a git repo", strict=True)
    if not ctx.path(".agents").is_dir():
        return Finding("STRUCT-09", "structure", "n/a", "no .agents/ store", strict=True)
    tracked = ctx.git("ls-files", ".agents").strip()
    lock_tracked = ctx.git("ls-files", "skills-lock.json").strip()
    lock_ignored = bool(ctx.git("check-ignore", "skills-lock.json").strip())
    problems = []
    if tracked:
        problems.append(f"{len(tracked.splitlines())} file(s) under .agents/ are tracked")
    if not lock_tracked and not lock_ignored:
        problems.append("skills-lock.json is neither tracked nor ignored")
    if problems:
        return Finding(
            "STRUCT-09", "structure", "drift", "; ".join(problems),
            "Ignore .agents/, then either commit skills-lock.json or ignore it too.",
            strict=True,
        )
    policy = "lock tracked" if lock_tracked else "store and lock machine-local"
    return Finding("STRUCT-09", "structure", "ok", f"store ignored, {policy}", strict=True)


def check_store_matches_lock(ctx: Context) -> Finding:
    lock = ctx.read("skills-lock.json")
    if lock is None:
        return Finding("STORE-01", "structure", "n/a", "no skills-lock.json", strict=True)
    try:
        keys = set(json.loads(lock).get("skills", {}))
    except json.JSONDecodeError as exc:
        return Finding(
            "STORE-01", "structure", "drift", f"skills-lock.json is not valid JSON: {exc}",
            "Fix or regenerate the lock.", strict=True,
        )
    store = ctx.path(".agents/skills")
    on_disk = {p.name for p in store.iterdir() if p.is_dir()} if store.is_dir() else set()
    missing = sorted(keys - on_disk)
    extra = sorted(on_disk - keys)
    if missing:
        return Finding(
            "STORE-01", "structure", "drift", f"pinned but absent: {', '.join(missing[:6])}",
            "Reinstall from the lock, or drop the entries upstream no longer serves.",
            strict=True,
        )
    detail = f"{len(keys)} pinned, all present"
    if extra:
        detail += f"; {len(extra)} unmanaged dir(s): {', '.join(extra[:4])}"
    return Finding("STORE-01", "structure", "ok", detail, strict=True)


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
            fix = f.fix if f.bad else ""
            detail = f.detail.replace("|", "/")
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


def ctx_read(root: Path) -> str | None:
    p = root / "AGENTS.md"
    return p.read_text(errors="replace") if p.is_file() else None


if __name__ == "__main__":
    sys.exit(main())
