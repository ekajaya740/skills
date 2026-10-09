---
name: github-workflow
description: "Full GitHub CLI workflow: auth, repo management, PR lifecycle, code review, issues, and codebase inspection via gh and git+curl."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, gh-cli, Pull-Requests, Issues, Code-Review, Releases, Repository]
    related_skills: [requesting-code-review, subagent-driven-development]
---

# GitHub Workflow

Complete GitHub CLI workflow covering authentication, repo management, PR lifecycle, code review, issue management, and codebase inspection. Each subsection shows the `gh` CLI way first, then the `git` + `curl` fallback for machines without `gh`.

Shared prerequisite: ** authenticate with GitHub first** (see Authentication section below).

## Table of Contents

1. [Authentication](#authentication)
2. [Repository Management](#repository-management)
3. [Pull Request Workflow](#pull-request-workflow)
4. [Code Review](#code-review)
5. [Issue Management](#issue-management)
6. [Codebase Inspection](#codebase-inspection)

---

## Authentication

Set up auth so the agent can work with GitHub repos, PRs, issues, and CI. Two paths:

- **`git` (always available)** — HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with simpler auth flow

### Detection Flow

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git remote -v  # Check existing GitHub remotes
```

### Auth Method: `gh` CLI (Preferred)

```bash
# Interactive login (browser-based OAuth)
gh auth login

# Non-interactive (token-based)
echo "$GITHUB_TOKEN" | gh auth login --with-token

# Verify
gh auth status
```

**GitHub Copilot 403 note:** `gh auth login` tokens do NOT work for the Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Auth Method: HTTPS Token

```bash
# Store in .gitconfig
git config --global credential.helper store

# Or use token in remote URL
git remote set-url origin https://<TOKEN>@github.com/owner/repo.git

# Or set env var (for curl fallback)
export GITHUB_TOKEN="ghp_..."
```

### Auth Method: SSH Keys

```bash
# Generate key
ssh-keygen -t ed25519 -C "agent@hermes"
cat ~/.ssh/id_ed25519.pub  # Add to GitHub → Settings → SSH keys

# Test
ssh -T git@github.com

# Switch remote to SSH
git remote set-url origin git@github.com:owner/repo.git
```

### Token Scopes

For full workflow access: `repo`, `read:org`, `workflow`, `read:packages`. Token must have `checks:write` for CI status in PRs.

**Full auth setup details and troubleshooting:** See `references/github-auth.md`.

---

## Repository Management

Create, clone, fork, configure, and manage GitHub repositories.

```bash
# Clone
gh repo clone owner/repo
git clone https://github.com/owner/repo.git

# Create new repo
gh repo create myproject --public --clone
mkdir myproject && cd myproject && git init

# Fork
gh repo fork owner/repo --clone

# Manage remotes
git remote -v
git remote add upstream https://github.com/original/repo.git

# Releases
gh release create v1.0.0 --title "Version 1.0" --notes "Release notes"

# Secrets
gh secret set MY_SECRET --body "secret_value"
gh secret list
```

**Full repo management reference:** See `references/github-repo-management.md`.

---

## Pull Request Workflow

Complete PR lifecycle: branch, commit, push, open, CI check, review, merge.

### Quick Path (gh CLI)

```bash
# Create branch + PR in one flow
git checkout -b feature/my-change
git add . && git commit -m "feat: description"
git push -u origin feature/my-change
gh pr create --title "feat: description" --body "What this changes"

# Check CI status
gh pr checks

# Review and merge
gh pr review <PR_NUMBER> --approve --body "LGTM"
gh pr merge <PR_NUMBER> --squash --delete-branch
```

### Fallback Path (git + curl)

When `gh` is not available, use the GitHub REST API via `curl`:

```bash
# Create PR via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/pulls \
  -d '{"title":"feat: description","head":"feature/my-change","base":"main","body":"What this changes"}'
```

### PR Size & Conventions

- **Prefer small, focused PRs** (1 logical change per PR)
- **Title format:** `type: description` (feat, fix, refactor, docs, chore)
- **Draft PRs** for work-in-progress: `gh pr create --draft`
- **Squash merge** for clean history: `gh pr merge --squash`

**Full PR workflow reference:** See `references/github-pr-workflow.md`.

---

## Code Review

Perform code reviews on local changes before pushing, or review open PRs on GitHub.

### Pre-Commit Review (Local Changes)

```bash
# Review staged changes
git diff --staged

# Review all uncommitted changes
git diff

# Review recent commits
git log --oneline -5
git show HEAD
```

### PR Review

```bash
# Get the diff
gh pr diff <PR_NUMBER>

# View changed files with summary
gh pr diff <PR_NUMBER> --name-only

# Leave review
gh pr review <PR_NUMBER> --approve --body "LGTM, clean implementation"
gh pr review <PR_NUMBER> --request-changes --body "Needs X fix before merging"

# Inline comments (via API since gh doesn't support inline directly)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/pulls/<PR_NUMBER>/comments \
  -d '{"body":"Suggestion: use dict.get() here","path":"src/file.py","line":42,"side":"RIGHT"}'
```

**Full code review reference:** See `references/github-code-review.md`.

---

## Issue Management

Create, search, triage, and manage GitHub issues.

```bash
# Create issue
gh issue create --title "Bug: X happens" --body "Steps to reproduce..."

# List/search issues
gh issue list --state open
gh issue list --label bug
gh issue list --search "search terms"

# View issue
gh issue view <NUMBER>

# Close issue
gh issue close <NUMBER>

# Add labels
gh issue edit <NUMBER> --add-label "bug,priority:high"

# Assign
gh issue edit <NUMBER> --add-assignee @me

# Comment
gh issue comment <NUMBER> --body "Update: investigated, root cause is..."
```

**Full issues reference:** See `references/github-issues.md`.

---

## Codebase Inspection

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios using `pygount`.

```bash
# Install
pip install pygount

# Analyze a repo
pygount --format=summary /path/to/repo

# Language breakdown only
pygount --format=summary --summary-by-language /path/to/repo

# Per-file detail
pygount /path/to/repo

# JSON output for scripting
pygount --format=json /path/to/repo | jq .
```

**When to use:** LOC counts, language breakdown, codebase size/composition questions, code-vs-comment ratios.

**Full codebase inspection reference:** See `references/codebase-inspection.md`.

---

## Cross-Cutting Rules

1. **Always authenticate first** — check `gh auth status` before any GitHub operations
2. **Always confirm before destructive actions** — closing issues, merging PRs, deleting branches
3. **Prefer `gh` over `curl`** — simpler, handles auth, pagination, and rate limits
4. **Use the `curl` fallback** when `gh` is not installed or when you need API features `gh` doesn't expose
5. **Prefer squash merges** for clean history unless the project convention says otherwise
6. **Small, focused PRs** — one logical change per PR
7. **Title format:** `type: concise description` (feat, fix, refactor, docs, chore)

## Related Skills

- `requesting-code-review` — Pre-commit verification pipeline (separate from PR review)
- `subagent-driven-development` — Execute implementation plans via subagents