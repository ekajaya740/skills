---
name: project-code-review
description: Systematic code review and project analysis — explore a codebase, analyze git history, identify issues, and write structured takeaways as second brain (Notion) Notes rows.
version: 1.0.0
license: MIT
author: ekajaya740
trigger: user asks to review, analyze, audit, or summarize a project
---

# Project Code Review

Systematic approach to exploring a codebase, analyzing contributions, identifying issues, and writing structured documentation into the second brain — **Notion** (page `<notion-page-id>`), via the `ntn` CLI. There is no vault file: the outputs below are **Notes** rows under the owning **Project** row, not markdown files.

## Workflow

### Phase 1: Gather Context

Read these files first to understand the project:

1. **`package.json` / `composer.json` / `Cargo.toml` / `go.mod`** — Dependencies, framework, project name
2. **`README.md`** — Project description (if it's the default scaffold, note that)
3. **`routes/web.php` or equivalent** — Route structure, controllers, middleware
4. **Key controllers** — The main controllers (home, CRUD, auth) to understand architecture
5. **Key models** — Core models to understand the domain
6. **Database migrations** — Schema design, table relationships
7. **`.env.example`** — Required services, integrations
8. **`vite.config.js` / `webpack.mix.js` / `next.config.js`** — Build setup

Batch independent reads together. Don't read every file — read enough to understand the architecture.

### Phase 2: Analyze Git History

```bash
# Who contributed and how much
git shortlog -sn --all

# Your commits (replace with actual author name)
git log --all --author="<name>" --format="%h %ai %s" --reverse

# All commits chronologically
git log --all --format="%h %ai %an %s" | head -80

# Files changed in your commits
git log --all --author="<name>" --format="%h %s" --name-only | head -200
```

Look for:
- **Commit volume** — How many commits per contributor
- **Commit quality** — Clear messages? One concern per commit? `fix:` vs `hotfix:` vs `feat:` discipline?
- **Scope** — Do commits touch 20+ unrelated files?
- **Merge patterns** — Clean merges or messy conflict resolutions?

### Phase 3: Scan for Common Issues

Use `search_files` to find:

| Pattern | What to look for |
|---------|-----------------|
| `dd\(` / `dump\(` / `var_dump` / `error_log` | Debug artifacts left in production |
| `// Route` / `// \$` / commented code | Dead code |
| `->validate(` | Inline validation (should be Form Requests) |
| `public function \w+\(` in controllers | Count method sizes — 200+ lines is a red flag |
| `::all()` | N+1 query risk |
| `sleep\(` | Hacky timing workarounds |
| `try {` without `catch` | Silent failures |

### Phase 4: Write Structured Output

Create **three separate Notes rows** in the second brain, each related to the owning **Projects** row
(`Project = <ProjectName>`), with `Tags` like `project/<name>` and `type/code-review`:

#### Row 1: `<Project> — Overview (<YYYY-MM-DD>)`
- Purpose, URL, repo path
- Tech stack table
- Architecture summary (routes, key controllers, database)
- Key features
- Recent work from git log

#### Row 2: `<Project> — Issues (<YYYY-MM-DD>)`
Project-level issues (independent of who wrote what). Organize by category:

| Category | What goes here |
|----------|---------------|
| Architecture & Code Organization | God controllers, no service layer, inconsistent patterns |
| Code Quality | Dead code, no tests, bugs, validation issues |
| Performance | N+1 queries, slow pages, external deps |
| Security & Maintenance | Hardcoded secrets, no CI/CD, naming conventions |

Each issue needs:
- **What's wrong** — Specific file:line references
- **Why it matters** — Impact (hard to test, will crash, slow)
- **Fix** — Concrete suggestion

End with a priority table (🔴 high / 🟡 medium / 🟢 low).

#### Row 3: `<Project> — Personal Takeaways (<YYYY-MM-DD>)`
Personal review of the user's contributions. Sections:
- **What was done well** — Specific achievements
- **What was done wrongly** — Specific mistakes with file:line references
- **What to improve** — Actionable advice

Body limits: 2,000 chars per rich-text value and 100 blocks per request — split a long row across
several `ntn pages update` calls rather than truncating, and **search before create** so a re-run
updates the existing row instead of duplicating it (see `notion-second-brain`).

### Phase 5: Cross-link

1. Relate the new Notes rows to the owning **Projects** row (and the **Areas** row if the project sits
   under an area) with **relations**, not `[[wikilinks]]`.
2. If the review produced durable decisions, write a **Decisions** row (`Rationale` in the body).
3. Do not hand-write the backlink — Notion relations are bidirectional by construction.

## Output Formatting Rules

- Use tables for structured data (tech stack, routes, issues priority)
- Use file:line references for specific issues (e.g., `ProductController.php:408`)
- Use emoji priority markers (🔴 🟡 🟢)
- Keep descriptions concise — one paragraph per issue
- Always include a "Fix" or "Recommendation" for every issue
- Row properties: `Name` = the title above, `Type = Reference`, `Status = Active`, `Tags =
  [project/<name>, type/code-review]`, `Project`/`Area` relations set, `Confidential` when the code
  is private

## Pitfalls

- Don't read every file — read enough to understand architecture, then search for patterns
- Don't fabricate issues — if you haven't seen the code, don't guess
- Don't mix personal and project issues in the same file — keep them separate
- Don't skip the git history analysis — it reveals contribution patterns and code quality habits
- Don't suggest fixes you're not confident about — say "investigate" if unsure
- Don't write more than ~20 issues per project — prioritize the most impactful
