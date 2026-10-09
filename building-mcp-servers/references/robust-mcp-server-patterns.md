# Robust MCP Server Patterns

**Session:** Solo Leveling v7.1 (May 2026). Full implementation at `ekajaya740/example-app`.

## @safe_handler — Catch-All Error Wrapper

Every MCP tool handler should be wrapped so exceptions don't crash the server or leave the client hanging:

```python
import logging
import traceback

logger = logging.getLogger("example-app")

def safe_handler(fn):
    async def wrapper(args):
        try:
            return await fn(args)
        except Exception as e:
            logger.error(f"Error in {fn.__name__}: {e}\n{traceback.format_exc()}")
            return [TextContent(type="text", text=f"❌ Internal error: {str(e)}")]
    wrapper.__name__ = fn.__name__
    return wrapper

@safe_handler
async def h_complete_habit(args):
    ...
```

**Why this matters:** MCP stdio transport is fragile. An unhandled exception in a tool handler can corrupt the JSON-RPC stream, causing the client to see "Connection closed" with no explanation. The wrapper ensures every error path returns a valid `TextContent` list.

## Split Domain Tools (Habits vs Quests)

When a system has two distinct entity types, give each its own tool names. Don't overload a single `complete_quest` for both:

| Entity | Tools |
|---|---|
| Habits (recurring) | `list_habits`, `create_habit`, `complete_habit`, `toggle_habit`, `check_pending_habits` |
| Quests (one-time) | `list_quests`, `create_quest`, `complete_quest`, `list_all_quests` |

**Why:** The LLM client (Hermes) routes tool calls based on description matching. If one tool handles both, the LLM will confuse them — calling `complete_quest` for a habit ID or vice versa. Separate names make the routing unambiguous.

## Unified Completions Log with Dual FKs

Track all completions in one table, but enforce exactly one target per row:

```sql
CREATE TABLE completions (
    id SERIAL PRIMARY KEY,
    habit_id INT REFERENCES habits(id) ON DELETE CASCADE,
    quest_id INT REFERENCES quests(id) ON DELETE CASCADE,
    completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exp_gained INT NOT NULL DEFAULT 0,
    gold_gained INT NOT NULL DEFAULT 0,
    mana_spent INT NOT NULL DEFAULT 0,
    CONSTRAINT one_target CHECK (
        (habit_id IS NOT NULL AND quest_id IS NULL) OR
        (habit_id IS NULL AND quest_id IS NOT NULL)
    )
);
```

**Query across both:**
```sql
SELECT COALESCE(h.name, q.name) as name, c.exp_gained, c.gold_gained
FROM completions c
LEFT JOIN habits h ON c.habit_id = h.id
LEFT JOIN quests q ON c.quest_id = q.id
WHERE DATE(c.completed_at) = CURRENT_DATE;
```

## SQL Migrations Over init_db.py

Remove `scripts/init_db.py` seed logic. Instead:
1. Write pure SQL migrations in `migrations/NNN_description.sql`
2. Apply with `psql -f migrations/NNN_description.sql`
3. Track schema version in `schema_migrations` table

**Benefits:**
- Schema is reviewable in plain SQL
- DBA can run migrations manually
- No Python dependency for schema changes
- Easy rollback (keep migration files)

**Example migration:**
```sql
CREATE TABLE schema_migrations (
    version INT PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT
);

-- v1
CREATE TABLE habits (...);
CREATE TABLE quests (...);
CREATE TABLE completions (...);

INSERT INTO schema_migrations (version, name) VALUES (1, 'create_tables');
```

## DB Connection Context Manager

Always use `@asynccontextmanager` with cleanup in `finally`:

```python
@asynccontextmanager
async def db():
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        yield conn
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        raise
    finally:
        if conn:
            await conn.close()
```

**Pattern:** Use `async with db() as conn:` in every handler. This ensures connections are returned to the pool even if the handler raises.

## Deadline Enforcement

For quests with deadlines, check on completion attempt — don't rely on a cron:

```python
if quest["deadline"] and quest["deadline"] < datetime.date.today():
    await conn.execute("UPDATE quests SET status='expired' WHERE id=$1", quest_id)
    return [TextContent(type="text", text="❌ Quest deadline has passed. Status: expired.")]
```

## Tool Input Schema — Recurrence Example

When adding new fields like recurrence, update the `inputSchema` with enums and descriptions:

```json
{
  "recurrence": {
    "type": "string",
    "enum": ["daily", "weekly", "custom"],
    "description": "How often this recurs"
  },
  "weekly_target": {
    "type": "integer",
    "minimum": 1,
    "maximum": 7,
    "description": "For 'custom': completions per week"
  }
}
```

**Validation:** Do server-side validation too — `if recurrence == "custom" and not weekly_target: return error`.

## Pitfalls

- **Unwrapped handlers** — Unhandled exceptions crash the MCP stdio stream
- **Overlapping patches** — Multiple `patch` calls on the same function can duplicate code. Read the file back between patches, or batch into one `write_file`
- **Tool name ambiguity** — `complete_quest` that handles both habits and quests confuses the LLM
- **Migration drift** — `init_db.py` with embedded `CREATE TABLE` strings diverges from production schema. Use SQL files.
- **Missing `finally` on DB close** — Leaked connections exhaust the asyncpg pool
- **Quest/habit ID collision** — If both tables use SERIAL starting at 1, a naive query might match the wrong type. Always include the table name in the JOIN.
