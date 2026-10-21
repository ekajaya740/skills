# Skills

My own agent skills, published for use across machines and agents.

This directory is also the live skill store on my machine (`~/.agents/skills`
points here), so it holds skills written by other people too. Those are **not**
published here — see [Third-party skills](#third-party-skills) — and the
`.gitignore` is written as an allowlist so that a newly downloaded skill can
never be committed by accident.

## Published skills

| Skill | Version | Description |
|-------|---------|-------------|
| [second-brain-weekly-review](./second-brain-weekly-review) | 1.0.0 | Generate a weekly review from the migrated Notion second brain. Use when the user wants a summary of the current or past week's activities, projects, decisions, and tasks. Triggers on: 'weekly review', 'review this week', 'weekly recap', 'what did I do this week', 'summarize this week', 'weekly summary', 'my week in review'. NOT for: single-entity summaries (use second-brain-summary skill), cross-note synthesis (use second-brain-synthesis skill), or extracting action items from pasted notes (use second-brain-action-items skill). |
| [second-brain-synthesis](./second-brain-synthesis) | 1.0.0 | Synthesis and gap analysis layer over the migrated second brain in Notion. Use when the user asks a question that requires pulling together information from multiple notes, wants a cited summary, or wants to know what's missing from their knowledge. Triggers on: 'what do I know about X', 'synthesize my notes on', 'what have I written about', 'am I missing anything about', 'gap analysis', 'meeting prep', 'what is the state of', 'summarize my thinking on'. NOT for: reading a single known page (use second-brain-summary skill), inbox curation (use second-brain-inbox-curation skill), or internet research (use web search). |
| [second-brain-summary](./second-brain-summary) | 1.0.0 | Summarize content from the migrated second brain in Notion. Use when the user wants a summary of a specific note, project, area, topic, or date range. Triggers on: 'summarize', 'give me a summary of', 'recap', 'what's in my notes about', 'summarize my project', 'summarize my area', 'summarize today', 'summarize this week', 'what did I write about'. NOT for: cross-note synthesis with gap analysis (use second-brain-synthesis skill), inbox curation (use second-brain-inbox-curation skill), or internet research (use web search). |
| [second-brain-skills-autofix](./second-brain-skills-autofix) | 1.0.0 | Auto-improve second-brain skills on demand - create new skills from the Notion contract, patch outdated skills, fix bugs found during use, and keep all second-brain skills consistent. Use when the user says 'improve this skill', 'update the X skill', 'this skill is wrong', 'add a skill for Y', 'the skill missed a step', 'fix the skill'. NOT for: running a second-brain operation (use second-brain-operations), or general skill authoring (use writing-skills). |
| [second-brain-project-area-creator](./second-brain-project-area-creator) | 1.0.0 | Create new projects and areas in the migrated Notion second brain with the right structure, properties, template bodies and Google Tasks integration. Use when the user says 'create a new project', 'new area', 'start a project called X', 'add a new area for Y'. NOT for: creating notes within an existing project/area (use second-brain-inbox-curation or second-brain-clipping-processor), or curating inbox content (use second-brain-inbox-curation). |
| [second-brain-operations](./second-brain-operations) | 1.0.0 | General second brain operation - orchestrates the full PARA workflow in Notion: daily inbox curation, clipping processing, daily note curation, weekly review, on-demand summary/synthesis/action-items. Use when the user asks about how the second brain works, what the system does, what skills are available, or wants to run a full cycle. Triggers on: 'how does the second brain work', 'run second brain', 'second brain operations', 'what skills do you have for my second brain', 'explain the system', 'full cycle'. NOT for: running a specific single skill (use that skill directly), or content questions (use second-brain-synthesis or second-brain-summary). |
| [second-brain-inbox-curation](./second-brain-inbox-curation) | 1.0.0 | Inbox curation for the migrated Notion second brain - scan the Inbox data source, classify each note into its best home (Projects, Areas, Notes, Decisions, Archive), and send a Telegram notification after each run. Triggers on: 'curate inbox', 'inbox curation', 'process my inbox', 'triage the inbox'. NOT for: web clippings only (use second-brain-clipping-processor), task extraction (use second-brain-action-items), or weekly recaps (use second-brain-weekly-review). |
| [second-brain-decision-manager](./second-brain-decision-manager) | 1.0.0 | Manage decisions in the migrated Notion second brain - create, supersede, and review decisions with full rationale. Use when the user is deliberating ('should I', 'help me decide', 'I'm torn between'), wants to record a decision, or review past decisions. NOT for: general note-taking (use second-brain-inbox-curation), or extracting decisions from raw notes (use second-brain-action-items). |
| [second-brain-daily-note-curation](./second-brain-daily-note-curation) | 1.0.0 | Weekly daily note curation in the migrated Notion second brain - extract project/area summaries and decisions from Daily Notes rows, then archive the originals. Dedicated weekly cron. Triggers on: 'curate daily notes', 'process daily notes', 'daily note curation'. NOT for: inbox triage (use second-brain-inbox-curation), clipping processing (use second-brain-clipping-processor), or weekly recap (use second-brain-weekly-review). |
| [second-brain-cross-linker](./second-brain-cross-linker) | 1.0.0 | Cross-link pages in the migrated second brain in Notion - find orphaned notes, add bidirectional relations, and maintain connectivity. Use when the user says 'find orphans', 'cross-link my notes', 'connect related notes', 'link audit', 'check for orphaned notes'. NOT for: creating new content (use second-brain-inbox-curation or second-brain-clipping-processor), or summarizing content (use second-brain-summary). |
| [second-brain-clipping-processor](./second-brain-clipping-processor) | 1.0.0 | Process web clippings from the Notion inbox: add metadata, link to related projects/areas, and file them as Notes rows. Use when the user wants to process clippings or as a daily cron task. Triggers on: 'process clippings', 'process web clippings', 'organize clippings', 'clip processor'. NOT for: general inbox curation (use second-brain-inbox-curation skill), extracting action items (use second-brain-action-items skill), or weekly review (use second-brain-weekly-review skill). |
| [second-brain-action-items](./second-brain-action-items) | 1.0.0 | Convert raw notes into a structured list of action items and file them in Notion. Use when the user pastes notes and wants to extract tasks, decisions, and information. Triggers on: 'extract action items', 'what are the action items', 'turn these notes into tasks', 'parse tasks from', 'action items from these notes', 'buat action items', 'ambil task dari catatan'. NOT for: summarizing content (use second-brain-summary skill), cross-note synthesis (use second-brain-synthesis skill), or inbox curation (use second-brain-inbox-curation skill). |
| [notion-second-brain](./notion-second-brain) | 1.0.0 | Single source of truth for the migrated second brain in Notion: the nine data sources, how to look up their ids, how to create a note/task/decision, how to link pages (relations plus inline mentions), how to search, the markdown dialect, the rate limit and where the token lives. Triggers on: 'notion', 'second brain', 'add a note', 'add a task', 'link these notes', 'query the notes', 'what do I know about X', 'create a decision'. NOT for: web clippings (use second-brain-clipping-processor), inbox triage (use second-brain-inbox-curation), weekly recap (use second-brain-weekly-review), or pulling documents out of email (use email-to-vault-resource). |
| [design-system](./design-system) | 1.0.1 | The design system for workofekajaya.com — an Astro 6 + React 19 + Tailwind v4 dark portfolio. Use when building, editing or reviewing any UI on that site. |
| [conversation-distillation](./conversation-distillation) | 1.0.0 | Review a finished conversation to extract durable lessons into a reusable skill — and decide whether a lesson is worth saving at all. Covers the reflection pass, memory-vs-skill, create-vs-update, ownership rules, and failure modes. Use after work is done, or when a session produced a correction the user had to repeat. |
| [anti-bot-scraping](./anti-bot-scraping) | 1.0.0 | Bypass Cloudflare WAF with cloudscraper. |
| [apple-apps](./apple-apps) | 1.0.0 | Manage Apple Notes, Reminders, and iMessage/SMS on macOS via CLI tools (memo, remindctl, imsg). |
| [arxiv](./arxiv) | 1.0.0 | Search arXiv papers by keyword, author, category, or ID. |
| [arxiv-mcp](./arxiv-mcp) | 1.0.0 | Use when searching or reading arXiv papers via MCP. |
| [building-mcp-servers](./building-mcp-servers) | 1.0.0 | Build custom MCP (Model Context Protocol) servers in Python with stdio transport, PostgreSQL, and domain-specific tools. |
| [cloudflare-fullstack](./cloudflare-fullstack) | 1.0.0 | Build full-stack apps on Cloudflare: Astro SSR + Hono API on Workers, R2 storage, Neon Postgres via Hyperdrive, Drizzle ORM, shadcn/ui. |
| [cloudflare-worker-mcp](./cloudflare-worker-mcp) | 1.0.0 | Host MCP servers on Cloudflare Workers (D1, KV, R2, DO). |
| [codebase-retrospective](./codebase-retrospective) | 1.0.0 | Analyze a project's commit history, architecture, and code quality to give structured, honest feedback on what was done well, what was done wrong, and what to improve. |
| [coding-agents](./coding-agents) | 1.0.0 | Delegate coding tasks to AI coding agent CLIs: Claude Code, Codex, or OpenCode — orchestrate via Hermes terminal/process tools. |
| [daily-global-news-briefing](./daily-global-news-briefing) | 1.1.0 | Use when compiling or automating a multi-source daily global news briefing. |
| [design-md](./design-md) | 1.0.0 | Author/validate/export Google's DESIGN.md token spec files. |
| [email-to-vault-resource](./email-to-vault-resource) | 3.0.0 | Pull a document-bearing email (ticket, policy, receipt, contract) from Gmail and file it into the second brain as a Notion Notes row (Type=Reference) with a Drive link, related to the owning Project/Area - or deliver its attachments straight to chat ('pull all X invoices and send it here'). Use when the user says 'pull the latest email from X and put it on the resources / reference it in area Y', or wants an emailed PDF saved into a project/area. Covers Gmail retrieval (incl. when himalaya/gws is unavailable), attachment download, Notion Notes authoring, and bidirectional relations. NOT for: general web clippings (use second-brain-clipping-processor), or sending/replying to email (not supported by this skill). |
| [excalidraw](./excalidraw) | 1.0.0 | Hand-drawn Excalidraw JSON diagrams (arch, flow, seq). |
| [gif-search](./gif-search) | 1.1.0 | Search/download GIFs from Tenor via curl + jq. |
| [gitea](./gitea) | 1.0.0 | Gitea API access — read-only interface to Gitea instances via the REST API. |
| [github-workflow](./github-workflow) | 1.0.0 | Full GitHub CLI workflow: auth, repo management, PR lifecycle, code review, issues, and codebase inspection via gh and git+curl. |
| [godmode](./godmode) | 1.0.0 | Jailbreak LLMs: Parseltongue, GODMODE, ULTRAPLINIAN. |
| [idx-company-profile-scraper](./idx-company-profile-scraper) | 1.0.0 | Scrape IDX company profiles via ai-cloudscraper. |
| [japan-transit](./japan-transit) | 1.0.0 | Use for Japanese train schedule lookups (jadwal kereta). |
| [jupyter-live-kernel](./jupyter-live-kernel) | 1.0.0 | Iterative Python via live Jupyter kernel (hamelnb). |
| [kanban-operations](./kanban-operations) | 1.0.0 | Use for ALL Kanban work: creating, routing, assigning, blocking, unblocking, reviewing or completing a task; choosing a board; decomposing work into a graph; handling handoffs and evidence; and any question about how Hermes kanban operates. |
| [linear](./linear) | 1.0.0 | Linear: manage issues, projects, teams via GraphQL + curl. |
| [llm-wiki](./llm-wiki) | 2.1.0 | Karpathy's LLM Wiki: build/query interlinked markdown KB. |
| [native-mcp](./native-mcp) | 1.0.0 | MCP client: connect servers, register tools (stdio/HTTP). |
| [ocr-and-documents](./ocr-and-documents) | 2.3.0 | Extract text from PDFs, scans, and standalone images (photos/receipts/screenshots) — pymupdf, marker-pdf, tesseract. |
| [polymarket](./polymarket) | 1.0.0 | Query Polymarket: markets, prices, orderbooks, history. |
| [pretext](./pretext) | 1.0.0 | Use when building creative browser demos with @chenglou/pretext — DOM-free text layout for ASCII art, typographic flow around obstacles, text-as-geometry games, kinetic typography, and text-powered generative art. |
| [project-code-review](./project-code-review) | 1.0.0 | Systematic code review and project analysis — explore a codebase, analyze git history, identify issues, and write structured takeaways as second brain (Notion) Notes rows. |
| [self-hosted-webapps](./self-hosted-webapps) | 1.4.0 | Deploy web apps (Python systemd services OR Docker containers) behind nginx reverse proxy with custom domains and SSL. |
| [spa-data-extraction](./spa-data-extraction) | 1.0.0 | Extract structured data from modern JS-heavy SPAs (Inertia.js, Next.js, Nuxt) by discovering hidden API endpoints in server-rendered HTML state, then paginating and enriching from detail pages. |
| [split-bill](./split-bill) | 1.1.0 | Split bills with friends/roommates/groups — unequal splits, partial payments, multi-currency with auto rates, image receipt scanning, JSON backend. |
| [spotify](./spotify) | 1.0.0 | Spotify: play, search, queue, manage playlists and devices. |
| [youtube-playlist-management](./youtube-playlist-management) | 1.0.0 | Reorder or list YouTube playlists via the Data API v3. |

## Third-party skills

Around eighty skills in this directory were written by other people and
installed from their upstream repositories. They stay on disk for local use but
are deliberately excluded from this repository: the copyright is theirs, and
copying them here would mean maintaining stale forks instead of tracking
upstream.

[`skills.json`](./skills.json) records where each one comes from, who wrote it
and under which licence. [`install-skills.sh`](./install-skills.sh) installs
them:

```sh
./install-skills.sh            # install anything missing
./install-skills.sh --update   # update everything already installed
./install-skills.sh --dry-run  # print the commands, run nothing
```

Some skills I have locally are no longer published upstream (renamed, bundled
into a larger skill, or withdrawn). Those are listed under
`notAvailableUpstream` in `skills.json`; the installer skips them.

Some of these ship with a system package rather than a Git repository. The
Omarchy desktop's skills (`omarchy`, `diagnose-crash`, `omarchy-app`) are
recorded under [`omacom/omarchy`](./skills.json): on an Omarchy machine the
first two are symlinked from `/usr/share/omarchy/default/agents/skills`, so
`omarchy update` keeps them current, while the installer installs all three
from upstream on any other machine.

## Adding a skill

A skill is a directory containing a `SKILL.md`. To publish a new one of my own,
create the directory and then un-ignore it in `.gitignore`:

```gitignore
# Your own skills
!/design-system/
!/my-new-skill/
```

Nothing else needs changing: everything not explicitly allowed stays untracked.

## Versioning

Each published skill carries a `version` field in the frontmatter of its
`SKILL.md`, and follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — a change that invalidates how the skill was previously used
  (renamed files, removed sections, changed required inputs).
- **MINOR** — new guidance, references or capabilities that are additive.
- **PATCH** — corrections, clarifications and typo fixes.

Releases are tagged `‹skill›-v‹version›`, for example `design-system-v1.0.0`.
The tag and the frontmatter `version` are kept in step, so a consumer such as
the `ekajaya740.github.io` submodule can pin an exact revision:

```sh
git -C .agents/skills fetch --tags
git -C .agents/skills checkout design-system-v1.0.0
```

Each skill keeps its own `CHANGELOG.md`, newest first, with the released version
and date as headings.

## Releasing

Releases are automated. To ship a new version of a skill, bump the `version`
field in its `SKILL.md` and add a matching section to its `CHANGELOG.md`:

```md
## [1.1.0] - 2026-10-06

### Added

- What changed.
```

Pushing that to `main` is the whole procedure. The Release workflow in
`.github/workflows/release.yml` compares each skill's version against the tags
that already exist; anything untagged is released as `‹skill›-v‹version›`, with
the release notes taken from the CHANGELOG section and a GitHub Release created.
Skills whose version has not changed are left alone, so several skills can be
released in one push.

The Validate workflow in `.github/workflows/validate.yml` runs on every push and
pull request. Its most important job is the leak check: it fails if anything
outside the `.gitignore` allowlist is tracked, which is what stops a downloaded
skill from reaching this public repository. It also checks that every published
skill has valid frontmatter and a CHANGELOG entry for its version, that
`skills.json` is valid JSON, and that the installer still parses.

Both scripts run locally:

```sh
python3 scripts/validate_skills.py          # checks; exits non-zero on problems
python3 scripts/release_skills.py --check   # what would be released
```

`release_skills.py --tag` creates the tags without pushing, if you ever need to
release by hand.

## Notes

- [`AGENTS.md`](./AGENTS.md) documents how to install, update and re-link the
  third-party skills, and what agents working in this repository must not do.
- `~/.agents/skills` is a symlink to this directory, so editing files here
  changes the skills every agent on the machine sees. `~/.claude/skills` and
  `~/.codex/skills` hold one symlink per skill pointing back here; a skill with
  no link in a harness is invisible to it.
- `ekajaya740.github.io` consumes this repository as a git submodule at
  `.agents/skills`. Changes to `design-system/` therefore need a submodule
  pointer bump in that repository to take effect.

## Licence

My own skills are MIT licensed — see [LICENSE](./LICENSE). Third-party skills
are covered by their own licences, recorded in [`skills.json`](./skills.json).
