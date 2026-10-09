# Merge Migration SQL Into Schema

PHP apps that use flat SQL files (schema.sql + seed.sql mounted as `docker-entrypoint-initdb.d/`) often accumulate separate migration files over time. Once a migration has been applied to production, merge it into the main schema so fresh deployments don't need to run it separately.

## When to Do This

- A migration file exists alongside `schema.sql` and `seed.sql`
- The migration has been applied to all running databases
- You want a single `schema.sql` that produces a complete, up-to-date database on fresh deployment

## How to Merge

### 1. Read both files

```bash
docker exec <php-container> cat /var/www/html/data/schema.sql
docker exec <php-container> cat /var/www/html/data/migration-XXX.sql
```

### 2. Identify what the migration adds

Common migration patterns:

| Migration action | How to merge into schema |
|-----------------|--------------------------|
| **New table** | Add the `CREATE TABLE` statement to schema.sql in the correct position (grouped by domain) |
| **New column** | Add the column definition to the existing `CREATE TABLE` in schema.sql |
| **New junction table** (e.g., `order_service`) | Add the `CREATE TABLE` after the parent table's definition |
| **Data migration** (e.g., copy old column to new table) | Add as a post-schema block at the bottom of schema.sql |
| **Drop column** | Add as a post-schema block at the bottom of schema.sql |
| **Rename column/table** | Update the `CREATE TABLE` in schema.sql directly |

### 3. Write the merged schema

**For structural changes** (new tables, columns, indexes): update the `CREATE TABLE` statements directly in schema.sql. These use `IF NOT EXISTS` so they're idempotent.

**For data migration + cleanup** (copy data, drop old columns): append a post-schema block at the bottom of schema.sql. Make it idempotent using `information_schema` checks:

```sql
-- ──────────────────────────────────────────────────────────────────────────────
-- Post-schema migration: <description>
--   - <what it does>
--   - Idempotent: safe on fresh or existing databases
-- ──────────────────────────────────────────────────────────────────────────────
SET @has_old_column = NULL;
SELECT COUNT(*) INTO @has_old_column
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '<table>' AND COLUMN_NAME = '<old_column>';

SET @migrate_sql = IF(@has_old_column > 0,
    'INSERT INTO `<new_table>` (...) SELECT ... FROM `<old_table>` WHERE ...',
    'SELECT 1'
);
PREPARE stmt FROM @migrate_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @drop_sql = IF(@has_old_column > 0,
    'ALTER TABLE `<table>` DROP COLUMN `<old_column>`',
    'SELECT 1'
);
PREPARE stmt FROM @drop_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

### 4. Delete the migration file

```bash
docker exec <php-container> rm /var/www/html/data/migration-XXX.sql
```

### 5. Verify

```bash
# Re-run the merged schema on the existing database (should be no-op)
docker exec <php-container> cat /var/www/html/data/schema.sql | \
  docker exec -i <mysql-container> mysql -u root -p<pass> <db_name>

# Check tables and columns
docker exec <mysql-container> mysql -u root -p<pass> <db_name> -e "SHOW TABLES;"
docker exec <mysql-container> mysql -u root -p<pass> <db_name> -e "DESCRIBE \`<table>\`;"

# Check the app still works
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/
```

## Pitfalls

- **Don't merge migrations that haven't been applied yet.** Only merge after the migration has run on all environments (dev, staging, prod).
- **Post-schema blocks must be idempotent.** Use `IF NOT EXISTS` for tables, `information_schema.COLUMNS` checks for column-level operations. A fresh database should run the entire file without errors.
- **Order matters in post-schema blocks.** If migration A creates a table and migration B inserts into it, the post-schema block must run A's logic before B's.
- **docker-compose.yml doesn't need updating** — it already references `schema.sql` and `seed.sql`. The migration file was an additional mount, not a replacement.
- **Commit the change.** After merging, `git add schema.sql && git rm migration-XXX.sql && git commit` so the repo stays in sync.
