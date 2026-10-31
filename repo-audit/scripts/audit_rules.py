"""Section `rules` — is the agent layer present, bounded, and non-duplicated?

AGENTS.md exists, is short enough to be read, holds no more bolded hard rules
than its stated budget, keeps every rule at the tier that binds it, and does not
restate a rule that lives in a detail file. The harness shims (`CLAUDE.md`,
`.cursor/rules/*.mdc`) must point at AGENTS.md rather than copy it.
"""

from __future__ import annotations

import re

from audit_model import (
    BULLET_RULE,
    FENCE,
    MAX_AGENTS_LINES,
    MAX_HARD_RULES,
    NOOP_PHRASES,
    RULES_BUDGET,
    RULE_VERB,
    SHIM_POINTER,
    STOPWORDS,
    TIER_TEST_QUESTION,
    TIER_TEST_TABLE,
    Context,
    Finding,
)

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

