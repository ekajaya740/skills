---
name: self-hosted-webapps
description: "Deploy web apps (Python systemd services OR Docker containers) behind nginx reverse proxy with custom domains and SSL."
version: 1.4.0
author: ekajaya740
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [nginx, systemd, reverse-proxy, ssl, certbot, web-deployment, devops]
    related_skills: [hermes-agent]
---

# Self-Hosted Web Apps

Deploy web applications (Python systemd services OR Docker containers) behind an nginx reverse proxy with custom domain, password auth, and Let's Encrypt SSL.

Target pattern: web app listens on `127.0.0.1:<port>`, nginx proxies `<your.domain>:443` → `127.0.0.1:<port>`. The web app never binds to a public interface directly.

## Communication Style (User Preference)

The user is technical (self-hosts Hermes, uses Docker, nginx, Cloudflare). When working on server-side tasks:
- **Do it yourself** — read files directly, write configs straight to disk, check things with curl/ss/etc. Don't ask the user to run commands and paste output.
- **Be concise** — don't over-explain steps or provide verbose guides. Give the essential info and execute.

**Two deployment styles:**
- **Baremetal / systemd** (Python apps, Node.js, etc.) — see sections 1-9 below
- **Docker Compose** (PHP, LAMP stacks, etc.) — see [`references/docker-web-apps.md`](references/docker-web-apps.md)

---

## 1. Anatomy of a deployment

```
/var/www/yourapp/        # App source (alternative: ~/yourapp/)
/etc/nginx/sites-available/yourapp   # nginx config
/etc/nginx/sites-enabled/yourapp     # symlink
/etc/systemd/system/yourapp.service  # systemd unit
~/.config/yourapp.env                # Environment variables (secrets, port, host)
/var/log/yourapp/        # Logs (optional)
```

---

## 2. Setup checklist

| Step | What | Command |
|------|------|---------|
| 1 | Install nginx | `sudo apt-get install -y nginx` |
| 2 | Install certbot | `sudo apt-get install -y certbot python3-certbot-nginx` |
| 3 | Create app directory | `git clone <repo> ~/myapp` |
| 4 | Create env config | `touch ~/.config/myapp.env` (chmod 600 if it has secrets) |
| 5 | Create systemd unit | `/etc/systemd/system/myapp.service` |
| 6 | Enable + start service | `sudo systemctl enable --now myapp` |
| 7 | Create nginx config | `/etc/nginx/sites-available/myapp` |
| 8 | Enable site | `sudo ln -sf ... && sudo nginx -t && sudo systemctl reload nginx` |
| 9 | Set DNS A record | point `myapp.yourdomain.com` → server IP |
| 10 | Get SSL | `sudo certbot --nginx -d myapp.yourdomain.com` |

---

## 3. Environment file (`~/.config/myapp.env`)

```bash
# Key=value pairs — loaded by systemd via EnvironmentFile=
# Comments with # are supported
APP_HOST=127.0.0.1
APP_PORT=8787
APP_PASSWORD=change-me
# SECRET_KEY=...
```

**Important:** If the app reads env vars from a file directly (not via systemd), create a `.env` in the app directory instead.

---

## 4. Systemd service unit

```ini
[Unit]
Description=My Web App
After=network.target nginx.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/user/myapp

# Load secrets (one per line, KEY=VALUE format)
EnvironmentFile=/home/user/.config/myapp.env

# The app's startup command
ExecStart=/home/user/myapp/venv/bin/python /home/user/myapp/server.py

# Restart behavior
Restart=on-failure
RestartSec=5

# Security
NoNewPrivileges=true
ProtectHome=read-only
ReadWritePaths=/home/user/.config /home/user/myapp/data

[Install]
WantedBy=multi-user.target
```

**Key notes:**
- `Type=simple` — the main process is the app itself
- `EnvironmentFile=` — systemd parses this as KEY=VALUE lines (supports # comments)
- `Restart=on-failure` catches crashes; `RestartSec=5` prevents tight restart loops
- If the app needs to write files (sessions, DB, uploads), add those paths to `ReadWritePaths=`
- `ProtectHome=read-only` by default — good security, but the app can't write to `~/` unless you carve out `ReadWritePaths`

**For apps with a foreground-launch flag** (like Hermes WebUI's `bootstrap.py --foreground`):
```ini
ExecStart=/usr/bin/python3 /home/user/myapp/bootstrap.py --foreground --no-browser
```
The `--foreground` flag makes the bootstrap `os.execv()` into the server, so systemd's PID tracking still sees the live process. Without it, the bootstrap would fork a child and exit — systemd would think the service died.

---

## 5. Nginx reverse proxy config

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name myapp.yourdomain.com;

    # Large uploads for file attachments
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8787;
        proxy_http_version 1.1;

        # WebSocket support (required for SSE / streaming)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Forward real client info
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Long timeouts for AI/big responses
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        # Disable buffering for streaming
        proxy_buffering off;
        proxy_cache off;
    }
}
```

**Create and enable:**
```bash
sudo cp /tmp/nginx-config /etc/nginx/sites-available/myapp
sudo ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo nginx -t           # Validate config
sudo systemctl reload nginx  # Apply
```

---

## 6. DNS

### Standard A record

Add an A record at your domain registrar:

| Type | Name | Value |
|------|------|-------|
| A | `myapp` | `<server-public-ip>` |

### Cloudflare proxy (orange cloud)

If using Cloudflare as DNS provider, two modes are available:

| Mode | Cloudflare icon | How it works | SSL needed on origin? |
|------|----------------|--------------|-----------------------|
| **Proxied + Flexible** | ☁️ Orange cloud | Cloudflare terminates HTTPS at edge, connects to origin over HTTP | **No** — but traffic between Cloudflare and origin is unencrypted |
| **Proxied + Full (Strict)** | ☁️ Orange cloud | Cloudflare terminates HTTPS at edge, connects to origin over HTTPS | **Yes** — use a Cloudflare Origin Certificate (see below) |
| **DNS-only** | ⚫ Grey cloud | Cloudflare only resolves DNS; client connects directly to your server | **Yes** — run `sudo certbot --nginx -d myapp.yourdomain.com` |

**Proxied + Flexible SSL is the quickest path** — no certbot needed. Cloudflare handles certificates for browsers; your server only needs port 80 open.

**Proxied + Full (Strict) + Cloudflare Origin Certificate** is the most secure — encrypted end-to-end with a cert that's free and valid for 15 years. See the Cloudflare Origin Certificate section below.

**Before DNS propagates — test locally:**
```bash
curl -s -H "Host: myapp.yourdomain.com" http://127.0.0.1/health
curl -s -H "Host: myapp.yourdomain.com" http://<public-ip>/health
```

---

## 7. SSL with Let's Encrypt

```bash
# Only after DNS resolves to this server
sudo certbot --nginx -d myapp.yourdomain.com
```

Certbot auto-edits your nginx config to add the `listen 443 ssl;` block. No manual SSL config needed.

**Verify SSL setup:**
```bash
# Test HTTP→HTTPS redirect
curl -s -o /dev/null -w "HTTP redirect: %{http_code} → %{redirect_url}\n" http://127.0.0.1/ -H "Host: myapp.yourdomain.com"

# Test HTTPS directly
curl -sk -o /dev/null -w "HTTPS: %{http_code}\n" https://127.0.0.1/ -H "Host: myapp.yourdomain.com"

# Test through Cloudflare (if proxied)
curl -s -o /dev/null -w "CF HTTPS: %{http_code}\n" https://myapp.yourdomain.com/
```

**SITE_URL update:** If the app uses environment variables for its base URL (e.g. PHP apps), update `SITE_URL` from `http://` to `https://` after SSL is live and restart the app container.

**Renewal is automatic** — certbot installs a systemd timer (`systemctl list-timers | grep certbot`).

### Cloudflare Origin Certificate (for Proxied + Full Strict)

When using Cloudflare proxy (orange cloud) with SSL/TLS mode set to **Full (Strict)**, Cloudflare needs a valid cert on your origin server. Cloudflare Origin Certificates are free and valid for 15 years.

**Generate in Cloudflare Dashboard:**
1. SSL/TLS → Origin Server → Create Certificate
2. Hostnames: `myapp.yourdomain.com` (or `*.yourdomain.com`)
3. Validity: 15 years
4. Download: copy both the **certificate** (`.pem`) and **private key** (`.key`)

**Install on server:**
```bash
# Place cert and key in standard locations
sudo cp myapp.pem /etc/ssl/certs/myapp.pem
sudo cp myapp.key /etc/ssl/private/myapp.key
sudo chmod 644 /etc/ssl/certs/myapp.pem
sudo chmod 600 /etc/ssl/private/myapp.key
```

**⚠️ PEM blank line pitfall:** When pasting PEM content via vim or other editors, extra blank lines may be inserted inside the base64 body. This breaks OpenSSL parsing — nginx will fail to start with `PEM_read_bio_PrivateKey() failed`. Fix by stripping blank lines from PEM files:

```bash
sudo python3 -c "
for f in /etc/ssl/private/myapp.key /etc/ssl/certs/myapp.pem:
    with open(f) as fh: content = fh.read()
    lines = [l for l in content.splitlines() if l.strip()]
    with open(f, 'w') as fh: fh.write('\n'.join(lines) + '\n')
"
```

Then verify: `sudo openssl x509 -in /etc/ssl/certs/myapp.pem -noout -subject` and `sudo openssl rsa -in /etc/ssl/private/myapp.key -check -noout`.

**Nginx SSL config for origin cert:**
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name myapp.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name myapp.yourdomain.com;

    ssl_certificate /etc/ssl/certs/myapp.pem;
    ssl_certificate_key /etc/ssl/private/myapp.key;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:<port>;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

**Pitfall: typo in config paths.** The `ssl_certificate` and `ssl_certificate_key` paths must exactly match the actual file locations. A single typo (e.g. `mysite.com` vs `mysitee.com`) causes nginx test to fail with misleading errors. Always run `sudo nginx -t` before reloading — and double-check that the paths in the config actually match the filenames on disk, especially when dealing with long domain names susceptible to typos.

**Pre-DNS workaround:** If you need HTTPS before DNS propagates, generate a self-signed cert:
```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/myapp-selfsigned.key \
  -out /etc/ssl/certs/myapp-selfsigned.crt \
  -subj "/CN=myapp.yourdomain.com"
```
Then add a manual SSL server block in nginx. Replace with certbot when DNS is ready.

---

## 8. Testing & verification

```bash
# Service status
sudo systemctl status myapp --no-pager -l

# Check app health endpoint
curl -s http://127.0.0.1:<port>/health

# Check through nginx
curl -s -H "Host: myapp.yourdomain.com" http://127.0.0.1/health

# Check from public IP
curl -s -H "Host: myapp.yourdomain.com" http://<public-ip>/health

# Logs
sudo journalctl -u myapp --no-pager -n 50
sudo journalctl -u myapp -f   # Follow live
```

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `systemctl start` hangs | App started in background/daemon mode | Use `--foreground` or `Type=forking` with PIDFile |
| 502 Bad Gateway from nginx | App isn't running on the proxy_pass port | `ss -tlnp \| grep <port>` to check |
| 502 Bad Gateway — Hermes Dashboard specifically | Dashboard process died (no systemd service) | Start dashboard: `hermes dashboard --port 9119 --host 127.0.0.1 --no-open`. For persistence, install systemd service — see `references/hermes-dashboard-systemd.md` |
| `systemctl --user start/stop/restart` blocked with "cannot restart or stop the gateway" | Running systemctl from inside a Hermes session — the gateway propagates SIGTERM to child processes | Run systemctl from a separate shell (SSH, tmux pane, or delegate to a subagent). Or use D-Bus directly: `busctl call --user org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager StartUnit ss "syncthing.service" "replace"`. Or just `enable` the service (it starts on next boot). **Better yet: use system-level services** (`/etc/systemd/system/`) instead of user-level — they're not blocked by the gateway and don't need `XDG_RUNTIME_DIR`. |
| 504 Gateway Timeout | App response too slow | Increase `proxy_read_timeout` |
| `Permission denied` on writes | ProtectHome blocks write to home dir | Add paths to `ReadWritePaths=` |
| `port 80: Address already in use` | Another process (Apache?) on port 80 | `sudo lsof -i :80` to find it |
| DNS resolves but HTTPS fails | Port 443 blocked by firewall | Check cloud security group / ufw / iptables |
| Cloudflare 521 (web server down) — HTTPS only | Cloudflare SSL/TLS mode is Full/Full Strict but origin has no SSL | Set Cloudflare SSL/TLS to **Flexible** (Cloudflare terminates HTTPS at edge, connects via HTTP to origin) |
| **Cloudflare proxied domain shows wrong app (e.g. Hermes login instead of myshop)** | Cloudflare sends HTTPS requests to origin port 443, but the nginx site config only listens on port 80. The request hits the **default server** on port 443 (which might be a different app). | Add a `listen 443 ssl` block to the nginx site config with a self-signed cert (or certbot cert). Cloudflare Flexible SSL means the origin cert doesn't need to be trusted by browsers — only nginx needs to accept the TLS handshake. Generate: `sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/ssl/private/<domain>.key -out /etc/ssl/certs/<domain>.pem -subj "/CN=<domain>"` |
| Docker app assets load from `localhost` instead of domain | docker-compose `environment:` block overrides `.env` file value | Remove the conflicting env var from docker-compose's `environment:` and let `.env` handle it — see `references/docker-web-apps.md`. After removing, use `docker compose up -d --force-recreate <service>` — `restart` does NOT clear old env vars from a running container. |
| **`PDOException: Unknown database 'db_name'`** — app can't connect to MySQL | The database was never created (init scripts only run on first container startup) | Check with `docker exec <container> mysql -u root -p<pass> -e "SHOW DATABASES;"`. If missing, create it manually and run schema/seed SQL — see `references/docker-web-apps.md` section "docker-entrypoint-initdb.d — First-Run-Only Trap" for the full recovery recipe. |
| App crashes with `PostgresError: column "X" does not exist` after DB migration | Docker image contains old app code from before the schema change | Rebuild and redeploy: `docker compose up -d --build`; stale code in old images is the #1 cause of 500s after DB changes. See `references/docker-stale-image-after-migration.md` |
| **PHP app doesn't see new `.env` vars after setting them** | The app reads `.env` directly (via its own `env()` function in `bootstrap.php`), NOT through Docker Compose's `environment:` block. Docker Compose `environment:` and `.env` are **separate systems** — one doesn't override the other. | Restart the PHP container: `docker compose restart php` (NOT `docker compose up -d` — that only re-reads Compose-level env, not the app's own `.env` file). If the `.env` file changed, a simple `restart` is sufficient — the file is already mounted inside the container. |
| certbot can't validate domain | DNS hasn't propagated yet | Use `dig +short myapp.yourdomain.com @8.8.8.8` to check |
| CouchDB container fails to start with permission errors | Host directories not owned by uid 5984 | Let Docker handle volume ownership automatically; don't pre-chown host dirs |
| `docker compose up -d` blocked by tool | Terminal tool detects long-lived process | Use `background=true` parameter or run directly |
| **Dashboard auth fails with env var password** | Dashboard started without sourcing `.env` — `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` not in environment | Startup script must `source .env` before launching the dashboard. Use `set -a` / `set +a` to export all vars. For systemd services, use `EnvironmentFile=` or source in the wrapper script. |
| **Project bot dashboard: prefer Docker-native over host systemd** | Setting up a host systemd service + startup script for a bot that already runs in Docker adds unnecessary complexity | Use `HERMES_DASHBOARD=1` + `env_file: .env` in docker-compose.yml instead. Docker's `restart: unless-stopped` handles persistence. See `references/hermes-multi-container-bots.md` for the full pattern. |

---

## Adding password auth to an SSR web app

When deploying a web app that should only be accessible to you, add a simple password guard. This applies to any SSR framework with middleware support (Astro, Next.js, SvelteKit, etc.).

**Two components:**
1. **`src/middleware.ts`** -- runs on every request, checks a `session` cookie against a `DASHBOARD_PASSWORD` env var
2. **`src/pages/login.astro`** -- login form that validates password and sets the cookie

**The CSRF trap (Astro 5 specific):**
Astro 5's `@astrojs/node` adapter enables **automatic CSRF protection** for server-rendered pages. It blocks POST requests with form-like content types unless the `Origin` header matches `url.origin`.

**Workaround: Use GET-based login forms.** Submit the password as a query parameter instead of POST body. The Astro page reads `Astro.url.searchParams.get('password')`, validates it, sets the cookie via `Astro.cookies.set()`, and redirects. This avoids the CSRF check entirely since it's a GET request.

**See `references/astro-ssr-auth-guard.md` for full login page code with error handling, redirect restoration, and the GET-based form pattern.**

**Pass the password as an environment variable:**
- For **systemd services**: add `DASHBOARD_PASSWORD=yourpassword` to `~/.config/myapp.env`.
- For **Docker Compose**: add to a `.env` file at the project root, then reference in `docker-compose.yml`:
  ```yaml
  environment:
    DASHBOARD_PASSWORD: ${DASHBOARD_PASSWORD:-changeme}
  ```
  The `.env` file is not committed to git -- add it to `.gitignore`.

## Hosting embedded diagrams (draw.io)

You can host interactive ERDs, architecture diagrams, or flowcharts alongside your web app using draw.io:

1. **Create a `.drawio` file** and place it in the web app's `public/` directory (served as a static asset)
2. **Embed via iframe** to the draw.io viewer:
   ```html
   <iframe src="https://viewer.diagrams.net/?embed=1&ui=min&nav=1&highlight=0000ff#Uhttps%3A%2F%2Fyour.domain.com%2Ferd%2Fer.drawio" style="width:100%;height:800px;border:none;" allowfullscreen></iframe>
   ```
3. **Add an edit link** for direct editing:
   ```html
   <a href="https://app.diagrams.net/#Uyour.domain.com%2Ferd%2Fer.drawio">Edit →</a>
   ```

### Schema Discovery (PostgreSQL)

Query the live database schema to discover all tables, columns, and foreign keys:

```sql
-- All tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;

-- All columns with types, nullability, defaults
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- Foreign keys
SELECT tc.table_name, kcu.column_name,
       ccu.table_name AS foreign_table_name,
       ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
```

**Run via Docker:**
```bash
sudo docker exec <container> psql -U <user> -d <db> -c "<query>"
```

### Table (entity) vertex pattern (draw.io XML)

The draw.io format (`.drawio`) uses `mxGraphModel` XML. Key structures:

**File skeleton:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram name="ERD" id="erd-1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" background="#0a0a1a">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        <!-- Table cells and edge cells go here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

**Table header:**
```xml
<mxCell id="table-1" value="table_name" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#12122a;strokeColor=#f59e0b;strokeWidth=2;fontColor=#f59e0b;fontSize=12;" parent="1" vertex="1">
  <mxGeometry x="50" y="170" width="280" height="200" as="geometry"/>
</mxCell>
```

**Column rows:**
```xml
<mxCell id="col-1" value="🔑 id (INT PK)" style="text;html=1;strokeColor=none;fillColor=none;fontColor=#e2e8f0;fontSize=10;" parent="1" vertex="1">
  <mxGeometry x="60" y="195" width="260" height="18" as="geometry"/>
</mxCell>
```

**FK column:** use both 🔑 and 🔗 markers. Color conventions: Core=#f59e0b (gold), Habits=#10b981 (green), Logs=#3b82f6 (blue), Join=#8b5cf6 (violet), System=#94a3b8 (slate), Misses=#ef4444 (red).

**Relationship (edge) pattern:**
```xml
<mxCell id="rel-1" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;strokeColor=#3b82f6;" parent="1" edge="1" source="completions" target="habits">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**Layout guidelines:**
- Column spacing: `y = header_y + 25 + (row * 18)`, offset `x` by 10px from table edge
- Group tables by domain, gaps of at least 60px between groups
- Background `#0a0a1a`, table fill `#12122a`

### ERD Pitfalls

- **Coordinate collision:** Plan layout before writing XML. Core/Habits on left, Streaks/Shop on right.
- **Missing FK vs composite PK:** Some tables use `(habit_id, date)` as composite PK — mark both rows with 🔑
- **Edge anchor math:** `exitX/Y` and `entryX/Y` are 0-1 ratios (0=left/top, 1=right/bottom)
- **URL encoding:** The `#U` parameter must be URL-encoded (`%3A` for `:`, `%2F` for `/`)
- **CSRF on update:** The draw.io viewer saves via HTTP — if the web app has CSRF/CORS restrictions, save-to-URL may fail. Point users to the Edit link instead.
- **Large schemas:** For 20+ tables, split into multiple `.drawio` files by domain.

## Hermes Dashboard — Auth Gate

For running Hermes Agent itself in Docker (multi-container, multi-profile), see [`references/hermes-docker-migration.md`](references/hermes-docker-migration.md).

The Hermes Dashboard has a built-in auth framework with three bundled provider plugins (`basic`, `nous`, `self-hosted`). The auth gate engages automatically when the dashboard binds to a non-loopback host (`0.0.0.0`) without `--insecure`.

**Quick basic auth setup:**
```yaml
# config.yaml
dashboard:
  basic_auth:
    username: admin
    password: your-password
```

Then change the systemd service from `--host 127.0.0.1` to `--host 0.0.0.0` and restart. The login page serves at `/login` with no JS dependency.

**Important — bind address for nginx proxy:**
- **`--host 127.0.0.1`** (loopback) — the embedded chat WebSocket is rejected with `origin_mismatch` when accessed through nginx from a public domain. The dashboard's security check sees the origin doesn't match the bound address.
- **`--host 0.0.0.0`** (all interfaces) — the auth gate engages, the embedded chat WebSocket works correctly through nginx. **This is the correct bind for nginx proxy setups.**
- **`--insecure` is deprecated** (June 2026) — no longer bypasses auth. A non-loopback bind always requires a configured auth provider.

Also set `dashboard.public_url` to your public domain (e.g. `https://hermes.example.com`) so the auth gate constructs correct redirect URLs behind the reverse proxy.

Full reference: [`references/hermes-dashboard-auth.md`](references/hermes-dashboard-auth.md)

**Systemd service for persistence:** The dashboard has no built-in auto-restart. Create a systemd service so it survives crashes and reboots — see [`references/hermes-dashboard-systemd.md`](references/hermes-dashboard-systemd.md).

## Obsidian LiveSync — CouchDB Backend

For deploying CouchDB as the sync backend for Obsidian's Self-hosted LiveSync plugin — including the `obsidian-git-livesync` git-to-CouchDB bridge — see [`references/obsidian-livesync.md`](references/obsidian-livesync.md).

## Hermes Multi-Container Project Bots

Run multiple Hermes Docker containers as independent project-specific bots — each with its own Discord gateway, GitHub webhook integration, SOUL, and read-only codebase mount. See [`references/hermes-multi-container-bots.md`](references/hermes-multi-container-bots.md) for the full scaffold pattern, config differences from a personal instance, .env template pattern, and pitfalls.

**Adding a dashboard to a project bot:** The multi-container bots reference now includes a full "Adding a Dashboard" section covering: dashboard config in config.yaml, the `HERMES_DASHBOARD=1` env var, port conflict handling with `network_mode: host`, separate nginx config + SSL, and systemd wrapper service. See the reference for step-by-step setup.

## Hermes Docker → Native Migration

If you're running Hermes Agent in a Docker container and want to move it to a native installation on the host (lower overhead, direct filesystem access, easier debugging), see [`references/hermes-docker-to-native-migration.md`](references/hermes-docker-to-native-migration.md).

The migration covers: installing Hermes via `uv tool install`, stopping the Docker container, creating systemd services for auto-start, and updating nginx config if needed. All config, skills, memories, and cron jobs in `~/.hermes/` survive the migration untouched.

## Google OAuth Token Management (Docker)

When running Hermes in Docker, Google OAuth tokens need periodic refresh. See [`references/gws-token-management.md`](references/gws-token-management.md) for the cron job setup, SSH key configuration, and git sync pattern used to keep tokens fresh and config pushed to GitHub.

**Quick credential lookup:** When CouchDB is running in Docker, credentials are in the container's environment variables, NOT in config files on disk. To find them:
```bash
docker exec <container-name> sh -c 'echo $COUCHDB_USER; echo $COUCHDB_PASSWORD'
```
Config files at `/etc/couchdb/` or `/opt/couchdb/etc/` may not exist or may be empty — the Docker image uses env vars exclusively.

## Pitfalls

For nginx cleanup, reset to defaults, and removing stale sites, see
[`references/nginx-cleanup-reset.md`](references/nginx-cleanup-reset.md).

## Syncthing Web UI — Nginx Reverse Proxy

Proxying Syncthing's Web UI (port 8384) behind nginx requires setting the `Host` header to `127.0.0.1:8384` instead of `$host` — Syncthing validates the Host header against its bound address and returns 403 otherwise. Full config, setup steps, and pitfalls in [`references/syncthing-nginx-proxy.md`](references/syncthing-nginx-proxy.md).

- **Don't bind the app to `0.0.0.0`.** Bind to `127.0.0.1` and let nginx handle external access. This is one less attack surface.
- **Don't put secrets in the ExecStart line** or in the `[Service]` section directly. Use `EnvironmentFile=` so secrets are in a separate chmod-600 file.
- **`Type=simple` vs `Type=forking`:** Most Python apps should use `Type=simple`. Only use `Type=forking` if the app explicitly daemonizes itself (rare).
- **nginx reload vs restart:** Use `reload` for config changes (zero-downtime), `restart` only when the binary itself changed.
- **client_max_body_size:** Default is 1MB -- raise it if your app accepts file uploads.
- **WebSocket:** If the app streams responses (SSE, WebSocket), you MUST set `proxy_set_header Upgrade` and `proxy_set_header Connection "upgrade"` -- otherwise streaming breaks behind nginx.
- Rewrite `docker compose up -d` when .env changes -- Docker Compose reads `.env` at startup. If you change `DASHBOARD_PASSWORD` in `.env`, you must recreate the container: `docker compose --env-file .env up -d <service>`.

## Merging Migration SQL Into Schema

When a PHP app accumulates separate migration SQL files alongside `schema.sql`, merge them into the main schema after they've been applied. See [`references/merge-migration-into-schema.md`](references/merge-migration-into-schema.md) for the full recipe — idempotent post-schema blocks, `information_schema` column checks, and verification steps.

## openwa (WhatsApp API Gateway) — compose service

Standalone `ghcr.io/rmyndharis/openwa:latest` container, shared network, port `2785`. Three env traps will boot-loop it (`Error: Invalid environment configuration:` with a truncated log): **(1)** don't set `DATABASE_NAME` for SQLite (bare name = Postgres DB name); **(2)** production refuses `CORS_ORIGINS=*` — list explicit origins; **(3)** default `whatsapp-web.js` engine needs `cap_add: [SYS_ADMIN]`. Full worked compose block, nginx WS proxy, and the raw-log trick to read the truncated boot error are in [`references/openwa-docker-deployment.md`](references/openwa-docker-deployment.md).

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| openwa boot-loops: `Error: Invalid environment configuration:` | `docker compose logs` truncates the real cause; usually one of: `DATABASE_NAME` set while `DATABASE_TYPE=sqlite`, or `CORS_ORIGINS=*` in production | Read the raw json log (`docker inspect --format='{{.LogPath}}'`, parse with python — see openwa reference) to see which rule fired; apply the matching fix |
