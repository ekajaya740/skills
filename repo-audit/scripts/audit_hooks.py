"""Commit hooks and branch topology — the repo's own wiring.

A `pre-commit` that runs the full suite gets bypassed, and a bypassed hook
protects nothing. A hook that is not executable, or not committed, or ignored by
a deny-by-default `.gitignore`, is the same failure wearing a different mask.
And a repo with more than one branch has to say which one production is.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from audit_model import Context, Finding

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
