# openwa — Docker Deployment Reference

openwa (https://github.com/rmyndharis/openwa) is a self-hosted **WhatsApp API Gateway**: Node 22 / NestJS API + React dashboard, single port (default `2785`), drives WhatsApp via `whatsapp-web.js` (bundled Chromium) or the lighter `baileys` engine. It ships a ready image `ghcr.io/rmyndharis/openwa:latest` and its own production `Dockerfile`.

Deploy it as a **standalone compose service** on the app's shared network (do NOT try to merge it into a PHP/Apache Dockerfile — different runtime). The PHP Dockerfile stays untouched.

## Three boot-crash env traps (the reason it boot-loops)

openwa validates env at startup (NestJS `validateEnv`). A generic `Error: Invalid environment configuration:` with no detail is thrown — read the raw container log (see below) to see which rule fired. Three pitfalls:

1. **`DATABASE_NAME` must be UNSET for SQLite.** A bare name is parsed as a **Postgres** DB name. Setting `DATABASE_NAME=openwa` with `DATABASE_TYPE=sqlite` crashes at boot:
   > `DATABASE_NAME must be a file path under the data volume for SQLite (e.g. ./data/openwa.sqlite); got "openwa". A bare name is the PostgreSQL DB name — leave DATABASE_NAME unset for SQLite to use the default ./data/openwa.sqlite.`
   **Fix:** just don't set `DATABASE_NAME` when `DATABASE_TYPE=sqlite`. Use Postgres only if you set all of `DATABASE_HOST/PORT/NAME/USERNAME/PASSWORD`.

2. **`CORS_ORIGINS=*` is REFUSED in production.** With `NODE_ENV=production`, a wildcard CORS origin fails validation. **Fix:** list explicit comma-separated origins, no spaces, e.g. `https://app.example.com,https://wa.example.com,http://localhost:2785`.

3. **`SYS_ADMIN` capability needed for the default engine.** `whatsapp-web.js` launches a sandboxed Chromium; its namespace setup needs `cap_add: [SYS_ADMIN]` (+ `security_opt: [apparmor:unconfined]`). Without it the browser hard-crashes. The `baileys` engine (WebSocket, no Chromium) does NOT need this — switch `ENGINE_TYPE=baileys` if you want to drop the cap.

## Working compose service block (verified healthy)

```yaml
  openwa:
    image: ghcr.io/rmyndharis/openwa:latest
    container_name: myshop_openwa
    restart: unless-stopped
    cap_add:
      - SYS_ADMIN
    security_opt:
      - apparmor:unconfined
    environment:
      NODE_ENV: ${OPENWA_NODE_ENV:-production}
      PORT: 2785
      HOME: /app/data
      XDG_CONFIG_HOME: /tmp/.config
      XDG_CACHE_HOME: /tmp/.cache
      LOG_LEVEL: ${OPENWA_LOG_LEVEL:-info}
      ENGINE_TYPE: ${OPENWA_ENGINE_TYPE:-whatsapp-web.js}
      PUPPETEER_HEADLESS: "true"
      PUPPETEER_ARGS: "--no-sandbox,--disable-setuid-sandbox,--disable-dev-shm-usage,--disable-gpu"
      DATABASE_TYPE: ${OPENWA_DATABASE_TYPE:-sqlite}   # DO NOT also set DATABASE_NAME
      CORS_ORIGINS: ${OPENWA_CORS_ORIGINS:-https://app.example.com,https://wa.example.com,http://localhost:2785}
      WEBHOOK_URL: ${OPENWA_WEBHOOK_URL:-}
    ports:
      - "${OPENWA_PORT:-2785}:2785"
    volumes:
      - openwa_data:/app/data      # persists sessions, media, sqlite db
    depends_on:
      - mysql
    networks:
      - myshop_network
volumes:
  openwa_data:
    driver: local
```

Notes:
- openwa serves **dashboard + REST API + Swagger on the same port**: dashboard `/`, API base `/api`, Swagger `/api/docs`.
- Health endpoint: `GET /api/health/ready` → `{"status":"ok",...}`.
- Auth: generate an API key in the dashboard (Infrastructure → API Keys), then send `Authorization: Bearer <key>` on API calls. First boot with no key logs a harmless `API_KEY_PEPPER is not set` warning (keys stored as plain SHA-256 until you set a pepper).
- `WEBHOOK_URL` lets openwa push events (message.received, etc.) to your app.

## Nginx reverse proxy

Mirror the host's Cloudflare **Flexible SSL** + self-signed origin cert pattern (see main skill §6/§7). Proxy `:80` and `:443` → `127.0.0.1:2785`. **WebSocket upgrade headers are required** — openwa streams QR / session events over WS:

```nginx
location / {
    proxy_pass http://127.0.0.1:2785;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

Origin cert: `sudo openssl req -x509 -nodes -newkey rsa:2048 -sha256 -keyout /etc/ssl/private/<domain>.key -out /etc/ssl/certs/<domain>.pem -days 3650 -subj "/CN=<domain>"`. (Browsers trust Cloudflare's edge cert; the origin cert only satisfies nginx's 443 handshake.)

## Diagnosing the truncated boot error

`docker logs` / `docker compose logs` **truncate** long lines (the compose log driver summarizes + caps line length — the real error showed as `ExceptionHandler] E...`). To get the FULL message, read the container's raw json-file log:

```bash
LOGF=$(docker inspect --format='{{.LogPath}}' <container>)
sudo python3 - "$LOGF" <<'PY'
import sys,json
f=sys.argv[1]
with open(f,errors='replace') as fh:
    for line in fh:
        try: o=json.loads(line)
        except: continue
        m=o.get('log','')
        if 'ERROR' in m or 'Invalid' in m:
            print(m.replace('\\n','\n').replace('\\"','"')[:1200])
PY
```

## First-boot API key

openwa **auto-generates an API key on first boot** and logs it in the container output. Look for:

```
🔑 API Key (newly created):
   owa_k1_045bb2fd4a26722762bdc33bcb1791b5f3da44e01147158f5c49e3af1bfa292f
```

Copy this key and set it in the **app's `.env`** (not openwa's env — the app needs it to call openwa's API):

```bash
OPENWA_API_KEY=owa_k1_...
```

**Important — which container to restart:** The API key is consumed by the **app container** (e.g. PHP), not openwa itself. After setting the key in `.env`, restart only the app container:

```bash
docker compose restart php       # or whatever your app service is named
```

Do NOT restart openwa — its key is already generated and valid.

### How the PHP app reads the key

The PHP app reads `.env` directly via its own `env()` function (defined in `bootstrap.php`), **not** through Docker Compose's `environment:` block. This means:

- The `.env` file must be present in the app directory (mounted as a volume or copied in the Dockerfile)
- Docker Compose `environment:` vars do NOT override `.env` for this app — they're separate systems
- If you see `OPENWA_API_KEY` in both `.env` and `docker-compose.yml`'s `environment:`, the `.env` value wins because the PHP code reads it directly

## Verification (ad-hoc, after deploy)

```bash
# container healthy + port published
docker inspect -f '{{.State.Health.Status}}' <container>   # -> healthy
docker port <container> 2785                               # -> 0.0.0.0:2785

# direct health
curl -s http://localhost:2785/api/health/ready            # -> {"status":"ok",...}

# through nginx (Host header, pre-DNS)
curl -s -H "Host: wa.example.com" http://127.0.0.1:80/api/health/ready
curl -sk -H "Host: wa.example.com" https://127.0.0.1:443/   # dashboard 200 text/html
```
