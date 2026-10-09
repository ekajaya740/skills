---
name: gitea-api
description: "Read-only Gitea API access via curl. Supports issues, repos, projects, and users."
metadata:
  version: 0.1.0
---

# Gitea API Skill

Read-only interface to Gitea instances via the REST API.

## Prerequisites

1. A valid Gitea **personal access token** (Settings → Applications → Generate Token).
2. The token and base URL stored in one of these locations (checked in order):
   - File: `~/.hermes/gitea/<instance-name>`  (contents = token)
   - Env: `GITEA_TOKEN_<INSTANCE>`
   - Env: `GITEA_TOKEN`
   - Env: `GITEA_BASE_URL` (default: derived from repo URL or https://code.re-creation.co.jp)

## Quick Reference

| Task | Command Pattern |
|------|---------------|
| List repos in an org | `gitea_api_get <INSTANCE> /orgs/<ORG>/repos` |
| List issues in a repo | `gitea_api_get <INSTANCE> /repos/<OWNER>/<REPO>/issues?state=all&limit=50` |
| Get a single issue | `gitea_api_get <INSTANCE> /repos/<OWNER>/<REPO>/issues/<NUMBER>` |
| Get issue comments | `gitea_api_get <INSTANCE> /repos/<OWNER>/<REPO>/issues/<NUMBER>/comments` |
| List user repos | `gitea_api_get <INSTANCE> /user/repos` |
| Get repo info | `gitea_api_get <INSTANCE> /repos/<OWNER>/<REPO>` |
| Get repo projects (if available) | `gitea_api_get <INSTANCE> /repos/<OWNER>/<REPO>/projects` |
| Get user profile | `gitea_api_get <INSTANCE> /user` |
| Get org profile | `gitea_api_get <INSTANCE> /orgs/<ORG>` |

## Usage

### Define the shell helper (once per terminal, or add to your `.bashrc`)

```bash
source ~/.hermes/skills/devops/gitea-api/scripts/gitea-api.sh
```

Or run inline:
```bash
export PATH="$HOME/.hermes/node/bin:$PATH"
source ~/.hermes/skills/devops/gitea-api/scripts/gitea-api.sh
```
```

### Examples

### Examples

**1. List repos in the MIPS org:**
```bash
gitea_api_get recreation /orgs/MIPS/repos
```

**2. List all issues in `MIPS/work_assignments`:**
```bash
gitea_api_get recreation /repos/MIPS/work_assignments/issues?state=all&limit=50
```

**3. Read issue #364:**
```bash
gitea_api_get recreation /repos/MIPS/work_assignments/issues/364
```

**4. Get issue comments:**
```bash
gitea_api_get recreation /repos/MIPS/work_assignments/issues/364/comments
```

**5. Search issues by keyword:**
```bash
gitea_api_get recreation '/repos/MIPS/work_assignments/issues?state=all&page=1&limit=50&q=CORS'
```

**6. Get current user:**
```bash
gitea_api_get recreation /user
```

### Output Formatting

The helper outputs raw JSON by default. Pipe through `python3` or `jq` for readability:

```bash
# Pretty-print full response
gitea_api_get recreation /repos/MIPS/work_assignments/issues/1 | python3 -m json.tool | head -n50

# Extract specific fields only
gitea_api_get recreation /repos/MIPS/work_assignments/issues?state=all&limit=50 | \
  python3 -c 'import json,sys; [print(i.get("number"), i.get("title")) for i in json.load(sys.stdin)]'
```

## Gotchas

- **Gitea Projects (Kanban boards)** are not exposed via the standard Gitea API v1 as of v1.21+. They are visual collections of issues but don't have their own API endpoints. Always reference issues by repo.
- **Authentication**: Always use the header `Authorization: token <TOKEN>`. Gitea supports this consistently across all endpoints.
- **Rate limits**: Gitea self-hosted does not have strict rate limiting by default, but the instance admin may configure them.
- **Pagination**: Use `?page=N&limit=M`. Default limit is 30.
- **State filtering**: Issues support `state=open`, `state=closed`, or `state=all`.

## Per-Instance Configuration

Create one file per Gitea instance under `~/.hermes/gitea/`:

```bash
# ~/.hermes/gitea/recreation   →  stores token for code.re-creation.co.jp
mkdir -p ~/.hermes/gitea
echo "YOUR_TOKEN_HERE" > ~/.hermes/gitea/recreation
chmod 600 ~/.hermes/gitea/recreation
```

Load the helper and run queries:

```bash
export PATH="$HOME/.hermes/node/bin:$PATH"
source ~/.hermes/skills/devops/gitea-api/scripts/gitea-api.sh

gitea_api_get recreation /repos/MIPS/work_assignments/issues?state=open
```