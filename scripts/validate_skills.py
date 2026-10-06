#!/usr/bin/env python3
"""Validate the skills this repository publishes.

This directory is also the live skill store on the author's machine
(~/.agents/skills points here), so roughly fifty skills written by other people
sit alongside the published ones. `.gitignore` denies everything at the root and
allows back only this repository's own files. These checks make that guarantee
explicit instead of relying on the ignore rules staying correct, and keep the
release metadata honest.

Run locally or in CI:

    python3 scripts/validate_skills.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

errors: list[str] = []
validated: list[str] = []


def run(*args: str) -> str:
    return subprocess.run(
        args, cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def tracked_files() -> list[str]:
    return [p for p in run("git", "ls-files").splitlines() if p]


def published_skills(files: list[str]) -> list[str]:
    """Top-level directories that hold a SKILL.md and are tracked by git."""
    return sorted(
        {p.split("/")[0] for p in files if p.endswith("/SKILL.md") and p.count("/") == 1}
    )


def parse_frontmatter(text: str) -> dict[str, str]:
    """Top-level `key: value` pairs from a SKILL.md YAML block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not match:
            continue  # indented (nested) keys are not top-level metadata
        key, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def allowlisted_paths() -> list[str]:
    """The paths .gitignore un-ignores: everything this repo is allowed to publish."""
    out = []
    for raw in (REPO / ".gitignore").read_text().splitlines():
        line = raw.strip()
        if line.startswith("!") and not line.startswith("!#"):
            out.append(line[1:].lstrip("/").rstrip("/"))
    return out


def is_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == entry or path.startswith(entry + "/") for entry in allowed)


def third_party_names() -> set[str]:
    """Skill names this repo records as belonging to someone else."""
    data = json.loads((REPO / "skills.json").read_text())
    names: set[str] = set()
    for source in data.get("sources", []):
        names.update(source.get("skills", []))
        names.update(source.get("notAvailableUpstream", []))
    return names


def changelog_versions(path: Path) -> list[str]:
    if not path.exists():
        return []
    return re.findall(r"^##\s+\[?(\d+\.\d+\.\d+)\]?", path.read_text(), re.M)


def readme_versions(text: str) -> dict[str, str]:
    """Map skill name -> version from the README's published skills table.

    Rows look like `| [name](./name) | 1.2.3 | Description |`.
    """
    found: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(
            r"^\|\s*\[([^\]]+)\]\([^)]*\)\s*\|\s*(\d+\.\d+\.\d+)\s*\|", line
        )
        if match:
            found[match.group(1)] = match.group(2)
    return found


def main() -> int:
    files = tracked_files()

    # 1. Nothing outside the allowlist may be tracked. This is the check that
    #    stops a downloaded skill from ever reaching the public repository.
    allowed = allowlisted_paths()
    if not allowed:
        errors.append(".gitignore has no allowlist entries; refusing to guess")
    else:
        for path in files:
            if not is_allowed(path, allowed):
                errors.append(f"tracked but not allowlisted in .gitignore: {path}")

    # 2. Every published skill must have valid frontmatter and a matching
    #    CHANGELOG entry, and must not be a third-party skill by name.
    third_party = third_party_names()
    skills = published_skills(files)
    if not skills:
        errors.append("no published skills found (no tracked <skill>/SKILL.md)")

    for name in skills:
        skill_dir = REPO / name
        if name in third_party:
            errors.append(
                f"{name} is recorded in skills.json as a third-party skill, "
                "so it must not be published here"
            )

        front = parse_frontmatter((skill_dir / "SKILL.md").read_text())

        declared = front.get("name")
        if not declared:
            errors.append(f"{name}/SKILL.md: missing 'name' in frontmatter")
        elif declared != name:
            errors.append(
                f"{name}/SKILL.md: name is '{declared}' but the directory is '{name}'"
            )

        if not front.get("description"):
            errors.append(f"{name}/SKILL.md: missing 'description' in frontmatter")

        version = front.get("version", "")
        if not version:
            errors.append(f"{name}/SKILL.md: missing 'version' in frontmatter")
        elif not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"{name}/SKILL.md: version '{version}' is not SemVer (x.y.z)")
        else:
            versions = changelog_versions(skill_dir / "CHANGELOG.md")
            if not versions:
                errors.append(
                    f"{name}: no CHANGELOG.md, or it has no '## [x.y.z]' heading"
                )
            elif version not in versions:
                errors.append(
                    f"{name}: version {version} has no matching heading in "
                    f"CHANGELOG.md (found: {', '.join(versions) or 'none'})"
                )
            validated.append(f"{name} {version}")

    # 3. The README's version table must agree with the frontmatter, so the
    #    published table cannot quietly go stale after a release.
    readme = REPO / "README.md"
    if readme.exists():
        documented = readme_versions(readme.read_text())
        for name in skills:
            declared = parse_frontmatter((REPO / name / "SKILL.md").read_text()).get(
                "version"
            )
            if name not in documented:
                errors.append(
                    f"{name}: not listed in the README's published skills table"
                )
            elif declared and documented[name] != declared:
                errors.append(
                    f"{name}: README says version {documented[name]} but SKILL.md "
                    f"says {declared}"
                )

    for entry in validated:
        print(f"  ok    {entry}")
    if errors:
        print()
        for err in errors:
            print(f"  FAIL  {err}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s) found", file=sys.stderr)
        return 1

    print(
        f"\n{len(skills)} published skill(s) validated; "
        f"{len(third_party)} third-party name(s) excluded from publishing"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
