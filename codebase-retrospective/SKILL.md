---
name: codebase-retrospective
description: "Analyze a project's commit history, architecture, and code quality to give structured, honest feedback on what was done well, what was done wrong, and what to improve."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, retrospective, audit, improvement, architecture-analysis]
    related_skills: [requesting-code-review, github-code-review, codebase-inspection]
---

# Codebase Retrospective

Analyze a project's commit history, architecture, code quality, and development patterns to produce structured, honest feedback. The user wants the bad news as much as the good news — direct, actionable, and organized.

## When to Use

- User asks "what did I do wrong" or "what should I improve" on a project
- User asks for a project retrospective or post-mortem
- User wants an honest assessment of their own work on a codebase
- Before planning a major refactor — understand what patterns to fix
- Onboarding to a new project — understand its health before contributing

**Do NOT use for:** pre-commit verification (use `requesting-code-review`), reviewing other people's PRs (use `github-code-review`), or LOC counting (use `codebase-inspection`).

## Workflow

### Step 1 — Gather commit history

Identify the user's commits by author name. The user's name is typically known from memory or the repo's git log.

```bash
# See all authors and their commit counts
git shortlog -sn --all

# Get the user's commits chronologically
git log --all --author="<username>" --format="%h %ai %s" --reverse

# Get full commit log for context (all authors)
git log --all --format="%h %ai %an %s" | head -80
```

### Step 2 — Analyze contribution patterns

Look for these signals in the user's commits:

**Positive signals:**
- Building core architecture from scratch (controllers, traits, components)
- Implementing complex features (booking engine, image processing, i18n)
- Creating reusable infrastructure (traits, seeders, build tooling)
- Responsive design and frontend architecture
- Consistent commit message format

**Red flags:**
- Mixing `feat` and `fix` in the same commit (e.g., `mix:` prefix)
- `hotfix:` prefix used for routine fixes (dilutes the meaning)
- Commits touching 20+ unrelated files (should be multiple commits)
- Commented-out code left in production
- Debug artifacts (`error_log()`, `dd()`, `var_dump()`) in committed code
- Dead code blocks and commented routes in production files
- Monolithic controller methods doing too many things
- No test coverage for new features

### Step 3 — Read key files for architecture assessment

Read the most architecturally significant files to understand patterns:

```bash
# Controllers (look for size and responsibility)
# Models (look for relationships and casts)
# Routes (look for organization and dead code)
# Traits/Services (look for reuse patterns)
# Migrations (look for schema design quality)
```

Key things to evaluate:
- **Controller size** — methods over 100 lines or files over 300 lines are red flags
- **Mixed concerns** — does the controller handle validation, business logic, AND view rendering?
- **N+1 queries** — look for loops making DB queries without eager loading
- **Error handling** — are external API calls wrapped in try/catch?
- **Dead code** — commented routes, unused imports, debug statements
- **Validation** — inline `$request->validate()` vs extracted Form Requests
- **Commit hygiene** — one concern per commit, meaningful messages

### Step 4 — Structure the feedback

Organize into three clear sections. Be direct — the user asked for honest feedback.

**1. What You Did (Your Contributions)**
List the user's actual achievements. Be specific about what they built, not generic praise. Group by area (frontend, backend, infrastructure).

**2. What You Did Wrongly**
Be direct but not personal. Each item should be a specific, observable pattern — not a vague criticism. Include:
- The specific file/line where the problem manifests
- Why it's a problem (maintainability, testability, performance, safety)
- The concrete symptom (e.g., "this would crash if X happens")

**3. What to Improve**
For each "wrong" item, give a concrete, actionable alternative:
- Extract service classes (not just "refactor" — say what to extract)
- Use Form Requests (name the specific validation to move)
- Write tests (name the critical flow to cover)
- Clean dead code before merging (specific workflow step)
- Improve commit discipline (specific rule to follow)

### Step 5 — Tone rules

- **Direct, not harsh.** Say "this is a bug" not "this is terrible code."
- **Specific, not vague.** Say "ProductController::save() is 649 lines" not "controllers are too big."
- **Balanced.** Lead with what they did well, then address problems. The user wants the truth, not a pep talk or a roast.
- **Actionable.** Every criticism must pair with a concrete fix or alternative approach.
- **No sugar-coating.** Skip "Great question!" or "That's a good point!" — just give the analysis.

## Pitfalls

- **Don't guess the user's name** — check `git log` output for the actual author string
- **Don't review only the last few commits** — the full history shows patterns
- **Don't skip positive signals** — the user needs to know what to keep doing
- **Don't make up bugs** — verify by reading the actual code, not just commit messages
- **Don't suggest framework migrations** — focus on code quality within the existing stack
- **Don't be vague about file locations** — always reference specific files and line numbers
- **Don't recommend tests without specifying what to test** — name the critical flows

## Reference

See `references/analysis-patterns.md` for common code quality patterns to look for during a retrospective.
