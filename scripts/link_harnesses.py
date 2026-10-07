#!/usr/bin/env python3
"""Link every skill in ~/.agents/skills into each agent harness.

`~/.agents/skills` is the single source of truth. Claude Code reads
`~/.claude/skills` and Codex reads `~/.codex/skills`, and neither follows the
other's directory, so each skill needs one symlink per harness. A skill that
exists in the source but has no link is invisible to that harness -- which is
why a freshly installed skill does not appear until this runs.

    python3 scripts/link_harnesses.py --dry-run   # report only
    python3 scripts/link_harnesses.py --apply     # make the changes

Harness directories can be overridden with --source / --harness, which is what
the tests use.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

HOME = Path.home()


def content_hash(directory: Path) -> str | None:
    """Hash a skill directory's files, ignoring .git and .DS_Store."""
    if not directory.is_dir():
        return None
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_dir() or ".git" in path.parts or path.name == ".DS_Store":
            continue
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def is_skill(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").is_file()


def link_target(source: Path, link: Path) -> str:
    """Relative path from the link's directory to the skill in the source.

    Only the link's own directory is resolved, not the link path: a harness
    directory may itself be a symlink (a dotfiles-managed ~/.claude is), and
    resolving it would produce a target that does not resolve. The links are
    written through the source path so that re-pointing the source moves every
    harness at once.
    """
    return os.path.relpath(source / link.name, link.parent.resolve())


def make_link(source: Path, link: Path, apply: bool, log, verb: str) -> None:
    rel = link_target(source, link)
    if apply:
        if link.is_symlink() or link.is_file():
            link.unlink()
        elif link.is_dir():
            shutil.rmtree(link)
        link.symlink_to(rel)
    log(f"  {verb:<8} {link.name} -> {rel}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--source",
        type=Path,
        default=HOME / ".agents" / "skills",
        help="the skill store to link from (default: ~/.agents/skills)",
    )
    parser.add_argument(
        "--harness",
        type=Path,
        action="append",
        default=None,
        help="a harness skills directory; repeatable "
        "(default: ~/.claude/skills and ~/.codex/skills)",
    )
    parser.add_argument(
        "--adopt",
        action="store_true",
        help="when contents differ, keep the harness copy (move it into the source)",
    )
    args = parser.parse_args()
    apply = args.apply
    source = args.source
    harnesses = args.harness or [HOME / ".claude" / "skills", HOME / ".codex" / "skills"]

    def log(msg: str = "") -> None:
        print(msg)

    if not source.is_dir():
        log(f"error: {source} is not a directory")
        return 1

    added = replaced = adopted = 0
    skipped: list[str] = []

    for harness in harnesses:
        if not harness.is_dir():
            log(f"{harness}: not present, skipping")
            continue
        log(f"\n{harness}")

        # Skills that live only in a harness are moved into the source of
        # truth and linked back, so nothing stays harness-local.
        for entry in sorted(harness.iterdir()):
            if entry.name.startswith(".") or entry.is_symlink():
                continue  # harness-internal (Codex keeps .system), or a link
            if is_skill(entry) and not (source / entry.name).exists():
                log(f"  adopt    {entry.name} (harness-only; moving into source)")
                if apply:
                    shutil.move(str(entry), str(source / entry.name))
                make_link(source, harness / entry.name, apply, log, "link")
                adopted += 1

        # Every skill in the source must be visible to this harness.
        for skill in sorted(source.iterdir()):
            if not is_skill(skill):
                continue  # repo files, scripts, .gitignore, ...
            link = harness / skill.name

            if link.is_symlink():
                if link.resolve() == (source / skill.name).resolve():
                    continue  # already correct
                make_link(source, link, apply, log, "relink")
                replaced += 1
            elif not link.exists():
                make_link(source, link, apply, log, "add")
                added += 1
            elif content_hash(link) == content_hash(source / skill.name):
                make_link(source, link, apply, log, "replace")
                replaced += 1
            elif args.adopt:
                log(f"  adopt    {skill.name} (differs; keeping the harness copy)")
                if apply:
                    shutil.rmtree(source / skill.name)
                    shutil.move(str(link), str(source / skill.name))
                make_link(source, link, apply, log, "link")
                adopted += 1
            else:
                log(
                    f"  SKIP     {skill.name} (differs from the source copy; "
                    "--adopt to keep the harness version)"
                )
                skipped.append(f"{harness.parent.name}/{skill.name}")

    log()
    if not apply:
        log("dry run: nothing changed")
    log(
        f"added: {added}  replaced: {replaced}  adopted: {adopted}  "
        f"skipped: {len(skipped)}"
    )
    for name in skipped:
        log(f"  skipped {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
