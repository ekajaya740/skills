#!/usr/bin/env python3
"""Generate ATTRIBUTION.md from skills.json, and check it has not drifted.

Every third-party skill on this machine belongs to someone else. `skills.json`
already records the repository, author and licence for each one; this renders
that record as a document a human can read, so a licence question has an answer
without opening a JSON file.

Two modes:

    python3 scripts/attribution.py            # write ATTRIBUTION.md
    python3 scripts/attribution.py --check    # exit 1 if it is stale

The check is what keeps the file honest. A hand-maintained credits list goes
stale the first time a source is added, and a credits list that is wrong is
worse than none: it names the wrong author for someone's work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "ATTRIBUTION.md"

HEADER = """\
# Attribution

Everything this repository publishes is in [LICENSE](./LICENSE) — MIT, my own work.
Everything it *installs* belongs to someone else, and this file says who.

**This file is generated.** Edit [`skills.json`](./skills.json) and run
`python3 scripts/attribution.py`. `python3 scripts/attribution.py --check` fails CI when
the two disagree, so a new source cannot land without its credit.

Third-party skills are not vendored in this repository. They are fetched from upstream into
the live skill store (`~/skills`, via `~/.agents/skills`) by
[`install-skills.sh`](./install-skills.sh).

"""

FOOTER = """\

## What this file does not cover

A skill's licence governs the skill. Any dependency it pulls in carries its own terms, and
those come from the upstream repository — check there before redistributing anything.

Nothing under a source's licence may be copied into this repository's own skills. If a
snippet from someone else's skill is worth reusing, the source is cited and the licence is
checked first, or the idea is rewritten.
"""


def load() -> dict:
    return json.loads((REPO / "skills.json").read_text())


def cell(text: str) -> str:
    """A Markdown table cell that cannot break the table."""
    return str(text).replace("|", "\\|").strip() or "—"


def licence(value: str | None) -> str:
    """A licence column that never hides a missing licence.

    "none" and empty are not a licence — they mean all rights reserved, and the
    reader of a credits table needs to see that rather than a blank cell.
    """
    text = (value or "").strip()
    if text.lower() in ("", "none", "noassertion", "unknown"):
        return "**none — all rights reserved**"
    return cell(text)


def render(data: dict) -> str:
    sources = data.get("sources", [])
    tools = data.get("tools", [])

    out = [HEADER.rstrip(), "", "## Skills installed from upstream", ""]
    out.append("| Source | Author | Licence | Skills |")
    out.append("| --- | --- | --- | --- |")

    for source in sorted(sources, key=lambda s: s["repo"].lower()):
        repo = source["repo"]
        names = source.get("skills") or []
        count = len(names)
        if count:
            listed = ", ".join(f"`{n}`" for n in names)
            if count > 6:
                listed = f"{count} skills — {', '.join(f'`{n}`' for n in names[:6])}, …"
        else:
            listed = "_nothing installable upstream_"
        out.append(
            "| [{}](https://github.com/{}) | {} | {} | {} |".format(
                repo, repo, cell(source.get("author")),
                licence(source.get("license")), listed,
            )
        )

    if tools:
        out += ["", "## Tools these skills depend on", ""]
        out.append("| Tool | Author | Licence | Used by |")
        out.append("| --- | --- | --- | --- |")
        for tool in sorted(tools, key=lambda t: t["name"].lower()):
            name = tool["name"]
            url = tool.get("url", "")
            label = f"[`{name}`]({url})" if url else f"`{name}`"
            out.append(
                "| {} | {} | {} | {} |".format(
                    label, cell(tool.get("author")),
                    licence(tool.get("license")), cell(tool.get("usedBy")),
                )
            )

    notes = [
        (s["repo"], (s.get("notes") or "").strip())
        for s in sources
        if (s.get("notes") or "").strip()
    ]
    if notes:
        out += ["", "## Notes", ""]
        for repo, note in notes:
            out += [f"**`{repo}`** — {note}", ""]

    out.append(FOOTER.rstrip())
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if ATTRIBUTION.md is out of date")
    args = parser.parse_args()

    data = load()
    rendered = render(data)

    if args.check:
        if not TARGET.exists():
            print("ATTRIBUTION.md missing; run python3 scripts/attribution.py",
                  file=sys.stderr)
            return 1
        if TARGET.read_text() != rendered:
            print(
                "ATTRIBUTION.md is out of date with skills.json; "
                "run python3 scripts/attribution.py",
                file=sys.stderr,
            )
            return 1
        print(f"  ok    ATTRIBUTION.md matches {len(data.get('sources', []))} sources")
        return 0

    TARGET.write_text(rendered)
    print(f"wrote {TARGET.name}: {len(data.get('sources', []))} sources, "
          f"{len(data.get('tools', []))} tools")
    return 0


if __name__ == "__main__":
    sys.exit(main())
