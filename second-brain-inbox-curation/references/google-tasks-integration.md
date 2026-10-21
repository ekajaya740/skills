# Google Tasks Integration

Google Tasks is **not** Notion. The second brain keeps tasks in the **Tasks** data source; Google
Tasks is a separate task manager reached through the `gws-core` CLI.

> **Currently blocked on this machine:** the stored OAuth credential has no `tasks` scope, so
> every command below returns `403 Request had insufficient authentication scopes`. Re-consent
> with the `https://www.googleapis.com/auth/tasks` scope, or skip the Google Tasks part of the
> curation and work only in Notion.

## CLI Commands

```bash
# List all task lists
gws-core tasks tasklists list --format json

# Create a new task list
gws-core tasks tasklists insert --json '{"title": "[A] Area Name"}'
gws-core tasks tasklists insert --json '{"title": "[P] Project Name"}'

# Delete a task list
gws-core tasks tasklists delete --params '{"tasklist": "LIST_ID"}'

# List tasks in a list
gws-core tasks tasks list --params '{"tasklist": "LIST_ID"}' --format json

# Create a task
gws-core tasks tasks insert --params '{"tasklist": "LIST_ID"}' --json '{"title": "Task name"}'

# Complete a task (use PATCH, not update)
gws-core tasks tasks patch --params '{"tasklist": "LIST_ID", "task": "TASK_ID"}' --json '{"status": "completed"}'

# Delete a task
gws-core tasks tasks delete --params '{"tasklist": "LIST_ID", "task": "TASK_ID"}'
```

## Moving a Task Between Lists

The Google Tasks API has no native "move" - copy to the new list, then delete from the old:

```bash
gws-core tasks tasks insert --params '{"tasklist": "DEST_ID"}' --json '{"title": "Task title"}'
gws-core tasks tasks delete --params '{"tasklist": "SOURCE_ID", "task": "TASK_ID"}'
```

## Naming Convention

- Areas: `[A] Area Name` (e.g. `[A] Fitness`)
- Projects: `[P] Project Name` (e.g. `[P] Mitsukoshi Isetan`)
- Default `Inbox` list = catch-all

## Exclusion List (second brain only, no Google Tasks)

- `PT-SUM-Digital-Konsultan` (Area)
- `Joki` (Area)
- `ADHD` (Area)
- `dotfiles` (Project)

## Sync Rules

- **Active** Task rows (Status = Todo / In progress) -> create in Google Tasks
- **Ideas** and payment rows -> second brain only (not synced)
- **Done** rows -> second brain only (not synced)
- When completing a task -> update both the Notion Task row and Google Tasks

## Finding List IDs

```bash
gws-core tasks tasklists list --format json | python3 -c "
import sys, json
for item in json.load(sys.stdin).get('items', []):
    print(f\"{item['id']}  {item['title']}\")
"
```

## Auth & Credentials

- The real CLI is `gws-core` (`/home/personal/9router/node/bin/gws-core`). The `gws`
  wrapper is broken: it execs `~/.hermes/node/bin/gws-core`, and `~/.hermes` no longer exists.
- Credentials: `~/.config/gws/credentials.json` (`client_id`, `client_secret`, `refresh_token`).
- Env vars the CLI needs:
  ```bash
  export GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/tmp/gwscfg   # must be writable
  export GOOGLE_WORKSPACE_CLI_CLIENT_CONFIG=/tmp/gwscfg/client_secret.json
  export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=~/.config/gws/credentials.json
  ```
  Without `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` the CLI answers
  `Access denied. No credentials provided`.
- **Scope gap:** the stored credential has no `tasks` scope, so Google Tasks calls return
  `403 Request had insufficient authentication scopes`. A fresh OAuth consent with the
  `https://www.googleapis.com/auth/tasks` scope is required before any of the commands above
  work. Until then, treat the Google Tasks section of the curation skill as unavailable.
- **credentials.json must include `"type": "authorized_user"`** - gws fails with "Bad authorized
  user secret: missing field `type`" without it
- if the refresh token expires (`invalid_grant`), a full OAuth flow is required
- after a manual OAuth, always verify credentials.json has the `type` field

## CLI Flag Reference

| Flag | Purpose |
|------|---------|
| `--json '...'` | Request body (JSON) |
| `--params '...'` | URL/query parameters (JSON) |
| `--format json` | Output format (json/table/yaml/csv) |
| `--page-all` | Auto-paginate results |
