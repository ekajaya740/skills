# Local Dev Database via Docker

When the local Postgres install has auth issues, port conflicts, or you just want an isolated throwaway DB, run Postgres in Docker on a non-standard port.

## Quick Start

```bash
sudo docker run -d --name solo-db --rm \
  -e POSTGRES_USER=ubuntu \
  -e POSTGRES_PASSWORD=levelup123 \
  -e POSTGRES_DB=solo_leveling \
  -p 127.0.0.1:5433:5432 \
  postgres:16-alpine
```

## Connection URL

```
postgresql://ubuntu:levelup123@127.0.0.1:5433/solo_leveling
```

## Reset Database

```bash
sudo docker rm -f solo-db
# Then re-run docker run command above
```

## Why This Pattern

- Avoids `sudo -u postgres psql` auth wrestling
- Isolated from system Postgres (if any)
- Non-standard port avoids conflicts with existing services
- `--rm` auto-cleans when stopped
- Works on fresh VMs where system Postgres isn't configured

## Docker for MCP Server Dev

When building MCP servers that need a DB:
1. Start container
2. Run `scripts/init_db.py` pointing at Docker URL
3. Connect MCP server using same `DATABASE_URL`
4. No system-level Postgres config needed
