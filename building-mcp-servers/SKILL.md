---
name: building-mcp-servers
description: "Build custom MCP (Model Context Protocol) servers in Python with stdio transport, PostgreSQL, and domain-specific tools."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, python, server, stdio, postgres, fastapi]
    related_skills: [native-mcp]
---

# Building Custom MCP Servers

Build domain-specific MCP servers in Python that expose tools to Hermes Agent (or any MCP client) via stdio transport. Covers schema design, async PostgreSQL, tool registration, and local-only deployment.

## When to Use

Use this when you need to:
- Build a custom MCP server with domain-specific tools (not generic filesystem/GitHub)
- Store data in PostgreSQL and expose CRUD + business-logic operations as MCP tools
- Run the server locally via stdio (Hermes native MCP client) or HTTP
- Combine an MCP API layer with an optional FastAPI web UI

## Prerequisites

- Python 3.11+
- `mcp` Python SDK: `pip install mcp`
- `asyncpg` for Postgres: `pip install asyncpg`
- PostgreSQL running locally

## Quick Start

```bash
mkdir my_mcp_server && cd my_mcp_server
python -m venv .venv
source .venv/bin/activate
pip install mcp asyncpg
```

### Minimal Server Skeleton

```python
#!/usr/bin/env python3
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

app = Server("my_server")

@app.list_tools()
async def list_tools():
    return [
        Tool(name="hello", description="Say hello", inputSchema={"type": "object", "properties": {}}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "hello":
        return [TextContent(type="text", text="Hello!")]
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### Hermes Config (stdio)

```yaml
mcp_servers:
  my_server:
    command: "python"
    args: ["/home/user/my_mcp_server/server.py"]
```

Restart Hermes (`/reset`). Tools appear as `mcp_my_server_*`.

## Database Layer Pattern

### Schema Initialization — SQL Migrations (Preferred)

Store schema in versioned `.sql` files, not Python strings. This keeps schema reviewable, DBA-runnable, and free of Python dependency.

```
migrations/
├── 001_create_tables.sql
└── 002_add_indices.sql
```

**Apply:**
```bash
psql -h 127.0.0.1 -p 5433 -U ubuntu -d mydb -f migrations/001_create_tables.sql
```

**Migration file structure:**
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INT PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT
);

-- actual DDL here
CREATE TABLE habits (...);
CREATE TABLE quests (...);
CREATE TABLE completions (...);

INSERT INTO schema_migrations (version, name) VALUES (1, 'create_tables');
```

**Why SQL over `init_db.py`:**
- Schema diverges from embedded Python strings over time (migration drift)
- SQL files can be reviewed in PRs without reading Python
- DBA / ops can run them directly
- No asyncpg dependency for schema changes

See `references/robust-mcp-server-patterns.md` for the full split-tables pattern and `@safe_handler` wrapper.

### Postgres Role + Grants

If connecting as a non-superuser, create the role first:

```bash
sudo -u postgres psql -c "CREATE ROLE ubuntu WITH LOGIN PASSWORD 'yourpass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE yourdb TO ubuntu;"
sudo -u postgres psql -d yourdb -c "GRANT ALL ON SCHEMA public TO ubuntu;"
sudo -u postgres psql -d yourdb -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ubuntu;"
```

## Tool Design Conventions

1. **Tool names** use snake_case: `complete_quest`, `get_hunter_status`
2. **Descriptions** are the prompt — the LLM reads them to decide when to call the tool. Make them explicit.
3. **inputSchema** must be valid JSON Schema with `type`, `properties`, and `required` arrays.
4. **Return** a list of `TextContent` objects. Keep responses concise but formatted.

### Example: CRUD + Business Logic Tool

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if name == "create_quest":
            row = await conn.fetchrow(
                "INSERT INTO habits (name, difficulty) VALUES ($1, $2) RETURNING id",
                arguments["name"], arguments.get("difficulty", 1)
            )
            return [TextContent(type="text", text=f"Created quest ID {row['id']}")]
        # ... more tools
    finally:
        await conn.close()
```

## Project Structure

```
my_mcp_server/
├── mcp_server/
│   └── server.py          # MCP server entry point
├── api/
│   └── main.py            # Optional FastAPI web UI
├── scripts/
│   └── init_db.py         # Database schema init
├── static/                # Web assets
├── templates/             # Jinja2 templates
├── requirements.txt
└── README.md
```

## Pitfalls

- **.venv in git:** The virtual environment must be in `.gitignore`. If accidentally committed, remove with `git rm -r --cached .venv` and recommit.
- **Password auth fails:** `asyncpg` requires password auth even for local connections if the Postgres role has a password set. Use the full `postgresql://user:pass@host/db` URL.
- **Missing grants:** Creating a database isn't enough — the user needs `GRANT ALL ON SCHEMA public` and `ALTER DEFAULT PRIVILEGES` to create/modify tables.
- **Stdio transport blocks:** The MCP server must run continuously on stdio. Don't add interactive prompts or `input()` calls.
- **Tool prefix collision:** Hermes registers tools as `mcp_{server_name}_{tool_name}`. Keep server names unique across configs.
- **No hot reload:** Adding or removing MCP servers requires restarting Hermes Agent (`/reset`).
- **Sequential patches overlapping on the same function:** When editing a large file via multiple `patch` calls, later patches may match text that earlier patches already modified, creating duplicate code blocks (e.g., duplicate `INSERT` statements). If a function was already patched once, a second patch to the same function should operate on the *already-modified* text, not the original. After any patch, verify the file with `git diff` or read it back before applying the next patch. When possible, batch edits into a single `patch` or a full `write_file` rewrite to avoid drift between the file's actual state and the patch's expected state.

### Stdio Transport: Newline-Delimited JSON (NOT Content-Length)

The `mcp` Python SDK v1.27+ uses **newline-delimited JSON** over stdio — each message is one JSON object terminated by `\n`. Do NOT use HTTP-style `Content-Length` framing. The `stdio_server()` reads line-by-line and validates each line as `JSONRPCMessage`.

```python
# WRONG — Content-Length framing causes "Invalid JSON" errors
msg = json.dumps(req)
proc.stdin.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}".encode())

# CORRECT — newline-delimited JSON
msg = json.dumps(req)
proc.stdin.write(f"{msg}\n".encode())
```

See `references/stdio-transport-debug.md` for a full reproduction and test harness.

### State-Comparison Bugs: Snapshot Before Mutation

When detecting changes (e.g., "rank up" after gaining mana), **snapshot the old value before the UPDATE**, not after. Comparing post-mutation state always yields false negatives because the DB already holds the new value.

```python
# WRONG — new_rank == current_rank always after UPDATE
new_rank = await check_rank_up(conn, new_mana)
if new_rank != await conn.fetchval("SELECT rank FROM hunter"):  # always False
    msg += "Rank up!"

# CORRECT — snapshot before mutation
old_rank = await conn.fetchval("SELECT rank FROM hunter")
await conn.execute("UPDATE hunter SET mana = mana + $1", mana_gain)
new_rank = await check_rank_up(conn, new_mana)
if new_rank != old_rank:
    msg += "Rank up!"
```

## Verification

After wiring into Hermes config and restarting:

```bash
# Check if tools are discovered
hermes tools | grep mcp_my_server
```

Or just ask Hermes: "List my MCP tools."

## References

- `references/mcp-tool-response-format.md` — Formatting patterns for TextContent responses
- `references/postgres-mcp-auth.md` — Postgres role creation and grant recipes
- `references/hermes-stdio-config.md` — Hermes `mcp_servers` YAML config patterns
- `references/stdio-transport-debug.md` — Newline-delimited JSON stdio transport protocol details and test harness
- `references/schema-migration-patterns.md` — Safe DDL migration scripts, PostgreSQL `ADD CONSTRAINT` gotchas, and asyncpg fallback when CLI is blocked
