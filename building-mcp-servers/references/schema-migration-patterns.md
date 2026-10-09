# Schema Migration Patterns for MCP Servers

Evolving a PostgreSQL schema for an MCP server involves live migrations on the production DB. This reference covers safe migration script patterns, PostgreSQL syntax gotchas, and asyncpg-based migration strategies when CLI access is restricted.

## Migration Script Structure

Create standalone `scripts/migrate_<feature>.py` scripts:

```python
import os
import asyncio
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

UPGRADE = """
-- Your DDL here
"""

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(UPGRADE)
    await conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
```

Run with: `python scripts/migrate_feature.py`

## Adding Columns (Safe)

```sql
ALTER TABLE habits ADD COLUMN IF NOT EXISTS quest_type TEXT DEFAULT 'habit';
```

`IF NOT EXISTS` works for columns. Safe to re-run.

## Adding Constraints (Gotcha)

**PostgreSQL does NOT support `ADD CONSTRAINT IF NOT EXISTS`.** This syntax fails:

```sql
-- WRONG — syntax error at or near "NOT"
ALTER TABLE habits ADD CONSTRAINT IF NOT EXISTS my_check CHECK (...);
```

**Correct pattern** — use a `DO $$` anonymous block:

```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'habits_quest_type_check'
    ) THEN
        ALTER TABLE habits ADD CONSTRAINT habits_quest_type_check
            CHECK (quest_type IN ('habit', 'quest'));
    END IF;
END $$;
```

## Seeding Reference Data Idempotently

Use `ON CONFLICT DO NOTHING` so migration scripts are idempotent:

```sql
INSERT INTO rewards (name, unlock_condition, icon, rarity) VALUES
('First Blood', 'complete_any_quest', '🩸', 'common'),
('Week Warrior', 'streak_7', '🔥', 'rare')
ON CONFLICT DO NOTHING;
```

**Note:** This requires a `UNIQUE` constraint on the target column(s). For `rewards`, add `UNIQUE(name)` or use the primary key.

## When psql CLI Is Blocked

In sandboxed environments (e.g., Hermes agent execution), `sudo -u postgres psql` may timeout or be blocked. **Use asyncpg Python scripts instead.**

```python
# Instead of: sudo -u postgres psql -c "ALTER TABLE ..."
# Use:
conn = await asyncpg.connect(DATABASE_URL)
await conn.execute("ALTER TABLE habits ADD COLUMN ...")
```

This pattern was essential for the Solo Leveling habit tracker where CLI commands timed out but asyncpg worked reliably.

## Full Migration Example

```python
import os, asyncio, asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ubuntu:pass@localhost/solo_leveling")

UPGRADE = """
ALTER TABLE habits ADD COLUMN IF NOT EXISTS quest_type TEXT DEFAULT 'habit';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'habits_quest_type_check'
    ) THEN
        ALTER TABLE habits ADD CONSTRAINT habits_quest_type_check
            CHECK (quest_type IN ('habit', 'quest'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS rewards (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    reward_type TEXT DEFAULT 'badge',
    unlock_condition TEXT NOT NULL,
    icon TEXT DEFAULT '🎁',
    rarity TEXT DEFAULT 'common',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

INSERT INTO rewards (name, description, unlock_condition, icon, rarity) VALUES
('First Blood', 'Complete your first quest.', 'complete_any_quest', '🩸', 'common'),
('Week Warrior', '7-day streak', 'streak_7', '🔥', 'rare')
ON CONFLICT (name) DO NOTHING;
"""

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(UPGRADE)
    await conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
```

## Idempotency Checklist

A migration script should be safe to run multiple times:
- [ ] `CREATE TABLE IF NOT EXISTS` for new tables
- [ ] `ADD COLUMN IF NOT EXISTS` for new columns
- [ ] `DO $$` block for constraints (check `pg_constraint` first)
- [ ] `ON CONFLICT DO NOTHING` or `ON CONFLICT DO UPDATE` for seed data
- [ ] No `DROP` statements unless explicitly dropping a removed feature
- [ ] `GRANT` idempotent (PostgreSQL silently ignores duplicate grants)

## Pitfalls

- **Duplicate `DO $$` block executions:** The `pg_constraint` check makes it safe, but verify the constraint name exactly matches `conname` (case-sensitive).
- **Missing `UNIQUE` for `ON CONFLICT`:** Without a unique index or primary key, `ON CONFLICT` raises `there is no unique or exclusion constraint`.
- **Sandbox CLI timeouts:** `sudo` and interactive shells often fail in agent sandboxes. Always have an asyncpg fallback for schema changes.
- **Running `init_db.py` on a live DB:** The `init_db.py` script should use `IF NOT EXISTS` everywhere. Never drop existing tables in `init_db.py`.
- **Forgetting to update `init_db.py` after migration:** After running a migration, merge the new columns/tables into `scripts/init_db.py` so fresh installs match the migrated schema.
