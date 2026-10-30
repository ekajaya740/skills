# Attribution

Everything this repository publishes is in [LICENSE](./LICENSE) — MIT, my own work.
Everything it *installs* belongs to someone else, and this file says who.

**This file is generated.** Edit [`skills.json`](./skills.json) and run
`python3 scripts/attribution.py`. `python3 scripts/attribution.py --check` fails CI when
the two disagree, so a new source cannot land without its credit.

Third-party skills are not vendored in this repository. They are fetched from upstream into
the live skill store (`~/skills`, via `~/.agents/skills`) by
[`install-skills.sh`](./install-skills.sh).

## Skills installed from upstream

| Source | Author | Licence | Skills |
| --- | --- | --- | --- |
| [alejandrobailo/no-use-effect](https://github.com/alejandrobailo/no-use-effect) | Alejandro Bailo | MIT | `no-use-effect` |
| [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) | Ayoub G. | MIT | `i-have-adhd` |
| [blader/humanizer](https://github.com/blader/humanizer) | Siqi Chen | MIT | `humanizer` |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | Gregor Zunic | MIT | `browser-use` |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | Emil Kowalski | MIT | 15 skills — `animate`, `animate-expo`, `animation-performance`, `animation-vocabulary`, `apple-design`, `ask-sonner`, … |
| [figma/mcp-server-guide](https://github.com/figma/mcp-server-guide) | Figma | **none — all rights reserved** | _nothing installable upstream_ |
| [intellectronica/agent-skills](https://github.com/intellectronica/agent-skills) | intellectronica | CC0-1.0 | `raindrop-api` |
| [jakubkrehel/make-interfaces-feel-better](https://github.com/jakubkrehel/make-interfaces-feel-better) | Jakub Krehel | MIT | `make-interfaces-feel-better` |
| [kerpopule/hermes-jev-skills](https://github.com/kerpopule/hermes-jev-skills) | Steve Darlow | MIT | 9 skills — `jev-browser-use`, `jev-computer-use`, `jev-frontier-work`, `jev-mailbox`, `jev-memory`, `jev-model-routing`, … |
| [makenotion/skills](https://github.com/makenotion/skills) | Notion Labs, Inc. | MIT | `notion-cli` |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock | MIT | 37 skills — `ask-matt`, `chief-of-staff`, `claude-handoff`, `code-review`, `codebase-design`, `diagnosing-bugs`, … |
| [obra/superpowers](https://github.com/obra/superpowers) | Jesse Vincent | MIT | `using-git-worktrees`, `using-superpowers` |
| [omacom/omarchy](https://github.com/omacom/omarchy) | David Heinemeier Hansson | MIT | `omarchy`, `diagnose-crash`, `omarchy-app` |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | Paul Bakaus | Apache-2.0 | `impeccable` |
| [PleasePrompto/notebooklm-skill](https://github.com/PleasePrompto/notebooklm-skill) | Please Prompto! | MIT | `notebooklm` |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | Supabase | MIT | _nothing installable upstream_ |
| [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | Vercel Inc. | Apache-2.0 | `agent-browser` |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | Vercel, Inc. | MIT | `find-skills` |

## Tools these skills depend on

| Tool | Author | Licence | Used by |
| --- | --- | --- | --- |
| [`codebase-memory-mcp`](https://github.com/DeusData/codebase-memory-mcp) | DeusData | MIT | `code-discovery` — the code graph it queries, and `scripts/cbm-here.sh` |
| [`skills`](https://github.com/vercel-labs/skills) | Vercel, Inc. | MIT | `install-skills.sh` (`npx skills@latest add`), and `skills-install` |

## Notes

**`pbakaus/impeccable`** — Upstream ships a single 'impeccable' skill (v4.5.0 locally) that covers these as sub-commands, in reference/*.md. The standalone sibling directories are leftovers from an older layout and are no longer installable by name; impeccable supersedes them.

**`mattpocock/skills`** — All upstream skills are installed except 'prototype', whose name is now owned by emilkowalski/skills (see that entry); install mattpocock's copy only if you intend to displace Emil's. Six local names are outdated because upstream renamed or withdrew them: diagnose -> diagnosing-bugs, to-issues -> to-tickets, to-prd -> to-spec, write-a-skill -> writing-for-agents (via writing-great-skills). caveman and zoom-out were removed outright with no successor; the local copies still work but will not update. Update with 'npx skills@latest update -g -y', then re-link the harnesses. See AGENTS.md.

**`supabase/agent-skills`** — skill-creator was installed from this repo in Jan 2026 but is no longer published there; upstream now offers 'supabase' and 'supabase-postgres-best-practices'.

**`figma/mcp-server-guide`** — No license file in the repository, so treat as all-rights-reserved. implement-design is no longer published; the closest successor is 'figma-design-to-code'.

**`kerpopule/hermes-jev-skills`** — These skills are installed by the repository's own installer (python3 install.py), which targets ~/.claude/skills, ~/.codex/skills and ~/.agents/skills. Prefer that over 'npx skills add'. jev-compaction is skipped by the CLI because its frontmatter has a YAML parse error upstream; install.py copies it fine. 'npx skills add' also skips the whole repo when it hits that file.

**`makenotion/skills`** — Official Notion skills repository. The local copy was an older revision. A same-named but unrelated community repo (CaesiumY/notion-cli-skill) also exists.

**`intellectronica/agent-skills`** — Large multi-skill repo; only raindrop-api is used locally.

**`PleasePrompto/notebooklm-skill`** — The local notebooklm directory is empty.

**`omacom/omarchy`** — Skills that ship with the Omarchy Linux distribution (package: omarchy). Locally they are symlinked from /usr/share/omarchy/default/agents/skills into this store, so `omarchy update` keeps them current; the CLI install below is the portable path for machines without Omarchy. Upstream lives at github.com/basecamp/omarchy (the GitHub owner is omacom).

**`emilkowalski/skills`** — All 14 upstream skills are installed. 'animate' and 'prototype' share their names with skills from other sources and were deliberately overwritten with Emil's versions: the local animate no longer tracks pbakaus/impeccable (which only ever shipped it as a superseded leftover) and prototype no longer tracks mattpocock/skills. Upstream also ships 'animation-performance' (added 2026-10-25): keeps web animations inside the frame budget.

**`alejandrobailo/no-use-effect`** — Enforces a strict no-direct-useEffect rule in React/React Native. A local copy existed in a previous skill store but was not tracked as a source here, so a fresh machine would not get it.

**`ayghri/i-have-adhd`** — Output-style skill: action-first replies, numbered steps, no preamble or closers. The standard's `style` section inlines the rules as a fallback, so this is optional.


## What this file does not cover

A skill's licence governs the skill. Any dependency it pulls in carries its own terms, and
those come from the upstream repository — check there before redistributing anything.

Nothing under a source's licence may be copied into this repository's own skills. If a
snippet from someone else's skill is worth reusing, the source is cited and the licence is
checked first, or the idea is rewritten.
