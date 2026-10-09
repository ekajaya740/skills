# Docker Web Apps

Deploy web apps via Docker Compose behind nginx reverse proxy with custom domains and SSL.

## Architecture

```
Browser → nginx (443) → Docker Compose stack
                        ├── web container (Node.js/Python/PHP app)
                        └── db container (optional)
```

## nginx Config

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name myapp.yourdomain.com;

    # Large uploads for file attachments
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:4321;
        proxy_http_version 1.1;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Forward real client info
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        proxy_buffering off;
        proxy_cache off;
    }
}
```

## docker-compose.yml

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      POSTGRES_DB: ${DB_NAME:-myapp}
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d
    networks:
      - app-network
    expose:
      - "5432"
    # Optionally: expose to host for external access
    # ports:
    #   - "127.0.0.1:5433:5432"

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    depends_on:
      - db
    environment:
      DATABASE_URL: postgres://${DB_USER:-postgres}:${DB_PASSWORD:-changeme}@db:5432/${DB_NAME:-myapp}
      DASHBOARD_PASSWORD: ${DASHBOARD_PASSWORD:-changeme}
    networks:
      - app-network
    ports:
      - "127.0.0.1:4321:4321"
    restart: unless-stopped

volumes:
  db_data:

networks:
  app-network:
    driver: bridge
```

## Key Networking Principles

### Container-to-Container Communication
Containers in the same Docker network (e.g., `app-network`) can reach each other by **service name** — not `localhost`. The `db` service hostname resolves to the container's internal IP. The host's loopback (`127.0.0.1`) is invisible inside a container.

**WRONG:**
```yaml
environment:
  DATABASE_URL: postgres://postgres:pass@127.0.0.1:5433/myapp
```
Containers cannot see the host's `127.0.0.1` without explicit `network_mode: host`.

**CORRECT:**
```yaml
environment:
  DATABASE_URL: postgres://postgres:pass@db:5432/myapp
```
The `db` hostname is resolved by Docker's internal DNS on the `app-network` bridge.

### Host-to-Container Access
If you need to access the DB from the host (e.g., for migrations, pgAdmin, `psql`):

1. **Map a high port on the host:**
   ```yaml
   ports:
     - "127.0.0.1:5433:5432"
   ```
   Access from host: `psql -h 127.0.0.1 -p 5433`

2. **From inside a container, use the service name**, not the host-mapped port:
   ```yaml
   DATABASE_URL: postgres://postgres:pass@db:5432/myapp
   ```
   The service name is DNS-resolved regardless of host port mappings.

## .env File

```
DB_USER=youruser
DB_PASSWORD=yourpassword
DB_NAME=yourdbname
DASHBOARD_PASSWORD=your-secret-password
```

Docker Compose automatically reads `.env` from the working directory. Do NOT commit credentials to version control.

## Application Inside Container

The web container should bind on `0.0.0.0:<port>` so that nginx (on the host) can connect to it via the host port mapping `127.0.0.1:4321:4321`. Bind 0.0.0.0, not 127.0.0.1 — `127.0.0.1` inside the container is its own loopback, unreachable from the host.

## Stale Image After Schema Change

Application code is **baked into the image** at build time. If you change the source code (e.g., drop a column, add a new table), the running container still uses the old image. See `references/docker-stale-image-after-migration.md` for the full recipe.

**Remediation:**
```bash
docker compose up -d --build
```

## docker-entrypoint-initdb.d — First-Run-Only Trap

MySQL and PostgreSQL Docker images run scripts from `/docker-entrypoint-initdb.d/` **only on first container startup** — when the data volume is empty. If the container restarts (or was started with an existing volume), those init scripts are **never re-executed**.

This means:
- If the container was started **before** you mounted the init scripts, the database never gets created.
- If you add new tables to the init scripts after the container is already running, they won't be applied.
- If the database was somehow dropped or never created (e.g., a volume was replaced), the init scripts won't help — they only fire on a fresh volume.

### Recovery: Create DB and Run Scripts Manually

When the database is missing from a running container:

```bash
# 1. Check what databases exist
docker exec <container> mysql -u root -p<password> -e "SHOW DATABASES;"

# 2. Create the database (if missing)
docker exec <container> mysql -u root -p<password> -e \
  "CREATE DATABASE IF NOT EXISTS \`db_name\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. Run schema and seed SQL into the database
docker exec -i <container> mysql -u root -p<password> db_name < data/schema.sql
docker exec -i <container> mysql -u root -p<password> db_name < data/seed.sql

# 4. Verify tables were created
docker exec <container> mysql -u root -p<password> -e \
  "USE db_name; SHOW TABLES;"
```

**Key points:**
- Use `docker exec -i` (interactive) with stdin redirect (`< file.sql`) — the `-i` flag is required for piping SQL files in.
- The init scripts are **idempotent** (use `CREATE TABLE IF NOT EXISTS`) so re-running them is safe.
- If you need to re-run init scripts on container restart, you must **delete the volume** (`docker compose down -v`) — but this destroys all data. Prefer manual recovery.

### Pitfall: Container Running But DB Missing

If the container shows `Up` and `healthy` but the app gets `Unknown database`:

1. The init scripts may have been mounted **after** the container first started (Docker only reads them on volume creation).
2. The volume may have been pre-populated from a backup or another environment.
3. The `MYSQL_DATABASE` env var in docker-compose only creates the database on **first startup** — same as the init scripts.

**Fix:** Create the database and run the SQL files manually (steps above). No need to restart the container.

## Commands

```bash
# Start or restart with build
docker compose up -d --build

# Stop
docker compose down

# Logs
docker compose logs -f web

# Restart a service
docker compose restart web

# Rebuild from scratch (clear caches)
docker compose build --no-cache
docker compose up -d
```
