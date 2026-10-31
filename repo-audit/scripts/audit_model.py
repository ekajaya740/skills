"""Types and the regex vocabulary the checks share.

`Finding` is one check's verdict; `Context` is everything a check may read
about the repo. The constants below are the whole vocabulary of the audit —
the rule bullet shape, the green-command table shape, the dangerous-command
list — kept here so a check module never restates one.

Imported by `audit_rules`, `audit_verify`, `audit_hooks` and `audit_structure`.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
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

