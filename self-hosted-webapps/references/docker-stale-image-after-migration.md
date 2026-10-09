# Stale Docker Images After DB Schema Migrations

After a database schema migration, production containers may crash with errors like `PostgresError: column "mana" does not exist`. This happens when the Docker image still contains application code from before the migration.

## Why it happens

1. `docker build` bakes the current source code into the image at build time.
2. If the source is updated (e.g., a migration drops `mana`, adds `gold_reward`), the **running container** still uses the old image.
3. The old app code queries columns that no longer exist → crashes on every request.

## Symptom checklist

- App worked fine before the migration.
- After migration, every API request returns HTTP 500.
- Logs show `PostgresError: column "X" does not exist` (or similar).
- `docker images` shows the image is older than the migration timestamp.

## Quick fix

```bash
# 1. Rebuild the image with current source
cd /path/to/docker-compose.yml
docker compose up -d --build

# 2. If the old container is still running (and port is in conflict), stop + remove first
docker stop solo-dashboard
docker rm solo-dashboard
# THEN run the up --build command above
```

## Prevention

- Always rebuild images after any schema change that removes columns, renames tables, or changes expected data shapes.
- Use CI/CD pipelines that trigger `docker compose up --build` automatically on pushes to `main`.
- Keep migrations and application code changes in the same PR so they deploy together.

## Debugging steps

```bash
# Check image age
docker images --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" | grep myapp

# Check if the running container has the new code
docker exec <container> cat /app/src/api/index.ts | grep mana
# If the old column name still appears inside the container, the image is stale.
```
