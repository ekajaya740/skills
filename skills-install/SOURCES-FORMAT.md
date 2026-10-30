# Source manifest format

Two files describe where third-party skills come from. Both live at the repo root and both are
published, so a fresh machine reproduces the same set.

## `skills.json` — the record

```json
{
  "version": 1,
  "description": "Third-party skills used locally. Not vendored: each belongs to its author.",
  "installer": {
    "tool": "npx skills add",
    "defaultArgs": ["-g", "-y"],
    "note": "Installs into ~/.agents/skills. Each source lists names via repeated -s flags."
  },
  "sources": [
    {
      "repo": "owner/repo",
      "license": "MIT",
      "author": "Author Name",
      "skills": ["skill-a", "skill-b"],
      "notAvailableUpstream": ["skill-c"],
      "notes": "Why skill-c is local-only: renamed upstream, or withdrawn."
    }
  ]
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `repo` | yes | `owner/repo`, exactly as the installer expects |
| `license` | yes | SPDX id. Empty licence = do not publish anything using it |
| `author` | yes | Attribution, for the README and for a licence question |
| `skills` | yes | Every skill to install from this repo, by name |
| `notAvailableUpstream` | no | Local skills whose upstream name is gone. Kept so the validator does not call them errors |
| `notes` | no | Why the list looks the way it does — the field a future reader needs most |

## `install-skills.sh` — the executor

The `SOURCES` array mirrors `skills.json`. Two files, because one is read by scripts and one by
people; they must not disagree.

```bash
SOURCES=(
  "owner/repo|skill-a,skill-b"
  "another/repo|skill-c"
)
```

A source with an empty skill list after the pipe has nothing installable upstream — it is recorded
for attribution only.

## Why both files

`skills.json` is the machine-readable record with licences and notes. `install-skills.sh` is the
thing a fresh machine actually runs, with `--dry-run` for review and `--update` for refresh. A
repo with only one of them either cannot be read or cannot be reproduced.

## Keeping them in step

| Change | Edit |
| --- | --- |
| New source | Both files, same commit |
| Skill renamed upstream | `skills[]` in `skills.json`, `SOURCES` in the script, and add the old name to `notAvailableUpstream` |
| Source withdrawn | Move its skills to `notAvailableUpstream`, leave the entry |
| Local skill becomes publishable | Remove it from `notAvailableUpstream`, un-ignore its directory |

Then:

```bash
./install-skills.sh --dry-run
python3 scripts/validate_skills.py
```

## Related

- The full install procedure → [`SKILL.md`](SKILL.md)
- The repo layout that holds these files → [`../project-scaffold/targets/agent-only.md`](../project-scaffold/targets/agent-only.md)
