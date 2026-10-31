"""Section `structure` — does the tree say what it is?

No dumping-ground folders, the decision and command homes exist, every required
environment variable is documented, and the skills store is not committed
without the lock that reproduces it.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from audit_model import Context, Finding

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
    # `ls-files` alone counts a submodule as a tracked file. A gitlink is a
    # pin — `.agents/skills` pointing at ekajaya740/skills so a fresh clone
    # gets the standard — and it was the only entry making this check red on
    # a repo that does the right thing. Drop mode-160000, keep the rest: a
    # leaked file inside the store still reports.
    tracked = [
        line.split("\t", 1)[1]
        for line in ctx.git("ls-files", "-s", ".agents").splitlines()
        if "\t" in line and not line.startswith("160000 ")
    ]
    gitlinks = [
        line.split("\t", 1)[1]
        for line in ctx.git("ls-files", "-s", ".agents").splitlines()
        if line.startswith("160000 ")
    ]
    lock_tracked = ctx.git("ls-files", "skills-lock.json").strip()
    lock_ignored = bool(ctx.git("check-ignore", "skills-lock.json").strip())
    problems = []
    if tracked:
        problems.append(f"{len(tracked)} file(s) under .agents/ are tracked")
    if not lock_tracked and not lock_ignored:
        problems.append("skills-lock.json is neither tracked nor ignored")
    if problems:
        return Finding(
            "STRUCT-09", "structure", "drift", "; ".join(problems),
            "Ignore .agents/, then either commit skills-lock.json or ignore it too.",
            strict=True,
        )
    policy = "lock tracked" if lock_tracked else "store and lock machine-local"
    if gitlinks:
        policy += f"; {', '.join(gitlinks)} pinned as a submodule"

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

