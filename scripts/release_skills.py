#!/usr/bin/env python3
"""Release published skills by tagging them from their frontmatter version.

For every skill this repository publishes, compare the `version` field in its
SKILL.md against the tags that already exist. If the version has no tag yet,
the skill has been bumped and is due for a release.

    python3 scripts/release_skills.py --check
        Print what would be released and exit. Writes nothing. Exits 1 if
        anything is due, so a workflow can use it as a gate.

    python3 scripts/release_skills.py --tag
        Create the annotated tags locally (no push; the workflow pushes).

The GitHub Release body is taken from the matching `## [x.y.z]` section of the
skill's CHANGELOG.md. If there is no such section the skill is not released,
because a release with no notes is worse than no release.

Only the tags for skills that are actually due are emitted, so the workflow
never needs to know how many skills exist.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ("git", *args), cwd=REPO, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def tag_identity() -> list[str]:
    """`-c` overrides for tagging, so this works without a configured identity.

    An annotated tag records a tagger, and a CI runner has no user.name or
    user.email set, so `git tag -a` fails with "empty ident name". Supplying
    the identity inline means the release does not depend on the caller having
    configured one. An existing local identity is still honoured.
    """
    name = git("config", "user.name", check=False).strip()
    email = git("config", "user.email", check=False).strip()
    if name and email:
        return []
    return [
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
    ]


def published_skills() -> list[str]:
    files = git("ls-files").splitlines()
    return sorted(
        {p.split("/")[0] for p in files if p.endswith("/SKILL.md") and p.count("/") == 1}
    )


def frontmatter_version(skill: str) -> str | None:
    lines = (REPO / skill / "SKILL.md").read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^version:\s*(\S+)\s*$", line)
        if match:
            value = match.group(1).strip("\"'")
            return value if re.fullmatch(r"\d+\.\d+\.\d+", value) else None
    return None


def changelog_section(skill: str, version: str) -> str | None:
    """The body of the `## [version]` heading, without the heading itself."""
    path = REPO / skill / "CHANGELOG.md"
    if not path.exists():
        return None
    lines = path.read_text().splitlines()
    out: list[str] = []
    capturing = False
    heading = re.compile(rf"^##\s+\[?{re.escape(version)}\]?")
    for line in lines:
        if heading.match(line):
            capturing = True
            continue
        if capturing:
            if line.startswith("## "):
                break
            out.append(line)
    body = "\n".join(out).strip()
    return body or None


def existing_tags() -> set[str]:
    return set(git("tag", "--list").splitlines())


def is_annotated_tag(tag: str) -> bool:
    return git("cat-file", "-t", tag).strip() == "tag"


def release_body(skill: str, version: str, notes: str) -> str:
    return (
        f"{skill} {version}\n\n"
        f"{notes}\n\n"
        f"---\n"
        f"Install or update: see the README in "
        f"https://github.com/{repo_slug()}/tree/{tag_name(skill, version)}\n"
    )


def tag_name(skill: str, version: str) -> str:
    return f"{skill}-v{version}"


def repo_slug() -> str:
    remote = git("remote", "get-url", "origin").strip()
    match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
    return match.group(1) if match else "ekajaya740/skills"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report pending releases")
    mode.add_argument("--tag", action="store_true", help="create pending tags")
    args = parser.parse_args()

    tags = existing_tags()
    due: list[tuple[str, str, str]] = []  # (skill, version, notes)
    problems: list[str] = []

    for skill in published_skills():
        version = frontmatter_version(skill)
        if version is None:
            problems.append(f"{skill}: no valid 'version' in SKILL.md frontmatter")
            continue

        tag = tag_name(skill, version)
        if tag in tags:
            print(f"  tagged  {tag}")
            continue

        notes = changelog_section(skill, version)
        if notes is None:
            problems.append(
                f"{skill}: version {version} is not tagged and CHANGELOG.md has no "
                f"'## [{version}]' section, so there are no release notes to publish"
            )
            continue

        due.append((skill, version, notes))
        print(f"  DUE     {tag}")

    if problems:
        print()
        for problem in problems:
            print(f"  FAIL  {problem}", file=sys.stderr)

    if not due:
        print("\nNothing to release." + (" See problems above." if problems else ""))
        return 1 if problems else 0

    print(f"\n{len(due)} release(s) due:")
    for skill, version, _ in due:
        print(f"  {tag_name(skill, version)}")

    if args.check:
        if problems:
            return 1
        return 0

    identity = tag_identity()
    for skill, version, notes in due:
        tag = tag_name(skill, version)
        git(
            *identity,
            "tag",
            "-a",
            tag,
            "-m",
            release_body(skill, version, notes),
            check=True,
        )
        print(f"  created {tag}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
