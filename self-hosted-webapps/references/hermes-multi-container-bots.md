# Hermes Multi-Container Project Bots

Run multiple Hermes Docker containers, each as an independent project-specific bot with its own config, SOUL, gateway targets (Discord, GitHub webhooks), and codebase access.

> ⚠️ **Stale-path warning.** The worked example below is the **app** bot, which
> lives under its own OS user `/home/user` (separate from the primary box user
> `/home/user`). Any `/home/user/app-*` path, `User=ubuntu` or
> `/home/user/start-app-dashboard.sh` in this file is **historical** — the
> `ubuntu` OS user no longer exists. Substitute your own bot user's home when
> adapting the recipe; the Hermes venv paths (`/home/user/.hermes/hermes-agent/venv`)
> are the primary box's and are current.

## When to Use a Separate Container vs a Profile

| | Hermes Profile (`~/.hermes/profiles/<name>/`) | Separate Docker Container |
|---|---|---|
| **Isolation** | Shares the same Hermes binary, same process | Fully independent process, separate container |
| **Gateway** | Same gateway process handles all profiles | Each container runs its own gateway |
| **Codebase access** | Same filesystem | Can mount different volumes per container |
| **Resource usage** | Low (shared process) | Higher (separate container) |
| **Use case** | Different roles for the same user | Public-facing bots, project-specific agents |

**Use a separate container when:**
- The bot needs its own Discord/Gateway presence (different bot token)
- The bot should have read-only access to a codebase (mount as `:ro`)
- You want independent restart/update lifecycle
- The bot serves a different audience (team members, not just you)

## Directory Layout

```
~/app-hermes/              # Project bot root
├── docker-compose.yml         # Container definition
├── config.yaml                # Hermes config (Discord + GitHub focused)
├── .env                       # Secrets (DISCORD_BOT_TOKEN, GITHUB_TOKEN, OLLAMA_API_KEY)
├── .env.template              # Template for .env (committed to git)
├── .gitignore                 # Secrets, runtime state
├── SOUL.md                    # Bot personality
├── AGENTS.md                  # Bot instructions
├── CLAUDE.md                  # Pointer → AGENTS.md
├── install-skills.sh          # External skill installer
├── skills.txt                 # External skill manifest
├── cron/output/               # Cron job output
├── gws/                       # GWS tokens (if needed)
├── memories/                  # Persistent memory
├── scripts/                   # Custom scripts
└── skills/                    # Custom skills
```

## Docker Compose Template

```yaml
services:
  app-hermes:
    image: nousresearch/hermes-agent:latest
    container_name: app-hermes
    restart: unless-stopped
    network_mode: host
    volumes:
      - ~/app-hermes:/opt/data
      - ~/workspace/app/app-monorepo:/workspace/app-monorepo:ro
      - ~/.ssh:/opt/data/home/.ssh:ro
    environment:
      - HERMES_UID=${HERMES_UID:-1000}
      - HERMES_GID=${HERMES_GID:-1000}
    command: ["gateway", "run"]
```

### Key Design Decisions

- **`network_mode: host`** — the container shares the host's network stack. The Discord gateway connects directly, and webhooks reach the container without port mapping.
- **Read-only codebase mount** (`:ro`) — the bot can inspect, search, and build but never modify code. This is intentional for monitoring/assistant bots.
- **SSH key mount** (`~/.ssh:ro`) — needed if the bot pushes config changes to git (e.g. cron job output).
- **`HERMES_UID`/`HERMES_GID`** — must match the host user's uid:gid to avoid permission errors on mounted volumes. Verify with `stat -c '%u:%g' <path>`.

## Config Differences from Personal Instance

A project bot's `config.yaml` should differ from your personal Hermes in these ways:

| Setting | Personal Instance | Project Bot |
|---------|-----------------|-------------|
| `terminal.cwd` | `~` or unset | `/workspace/app-monorepo` |
| `discord.require_mention` | `false` (optional) | `true` (responds only when @mentioned) |
| `dashboard` | Configured with auth | Optional — see "Adding a Dashboard" below |
| `timezone` | `''` or UTC | Set to team's timezone (e.g. `Asia/Jakarta`) |

## Adding a Dashboard to a Project Bot

A project bot can have its own dashboard web UI, just like the personal instance. There are two approaches:

### Approach A: Dashboard inside Docker (via HERMES_DASHBOARD=1) ★ PREFERRED

**This is the preferred approach when the bot runs in Docker.** The dashboard runs as part of the gateway process inside the container — no host-side systemd service or startup script needed. Docker's `restart: unless-stopped` handles persistence.

1. **Dashboard config** in the bot's `config.yaml`
2. **`HERMES_DASHBOARD=1`** env var in docker-compose.yml
3. **Password via `.env`** — add `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=your-password` to the bot's `.env` file, and reference it in docker-compose.yml with `env_file: .env`
4. **A separate nginx config** with its own subdomain and SSL cert
5. **No host systemd service needed** — Docker handles restart

### Step 1: Add dashboard config to config.yaml

```yaml
dashboard:
  theme: default
  show_token_analytics: false
  basic_auth:
    username: app
    password_hash: scrypt$16384$8$1$...  # generated hash (fallback)
    password: ''                          # plaintext goes in .env, not here
    secret: ''
    session_ttl_seconds: 0
  public_url: https://hermes.example.com
```

**Password in `.env` (not config.yaml):** The basic auth provider reads `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` from the environment, which takes precedence over `config.yaml`'s `password` field. Store the password in `.env` (gitignored) and let the container pick it up via `env_file:`.

### Step 2: Add HERMES_DASHBOARD=1 and env_file to docker-compose.yml

```yaml
services:
  app-hermes:
    # ... existing config ...
    environment:
      - HERMES_UID=${HERMES_UID:-1000}
      - HERMES_GID=${HERMES_GID:-1000}
      - HERMES_DASHBOARD=1
    env_file:
      - .env
    command: ["gateway", "run"]
```

The `HERMES_DASHBOARD=1` env var tells the gateway to also start the dashboard web server. Without it, only the messaging gateway runs. The `env_file: .env` line loads all variables from `.env` into the container's environment, including `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`.

### Step 3: Determine the dashboard port

The dashboard defaults to port **9119**. With `network_mode: host`, this conflicts with the personal dashboard if it's also running on 9119.

**Port conflict resolution — use `HERMES_DASHBOARD_PORT`:** Override the port via an env var in docker-compose.yml:

```yaml
    environment:
      - HERMES_UID=${HERMES_UID:-1000}
      - HERMES_GID=${HERMES_GID:-1000}
      - HERMES_DASHBOARD=1
      - HERMES_DASHBOARD_PORT=9120
    env_file:
      - .env
```

The dashboard's s6 run script reads `HERMES_DASHBOARD_PORT` (default 9119). Set it to any free port. Then update the nginx proxy_pass to match.

To verify the port after starting:
```bash
docker exec app-hermes ss -tlnp | grep python
docker logs app-hermes 2>&1 | grep -i "dashboard\\|port\\|listening\\|ready"
```

### Step 4: Create nginx config

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name hermes.example.com;

    ssl_certificate /etc/ssl/certs/hermes.example.com.pem;
    ssl_certificate_key /etc/ssl/private/hermes.example.com.key;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:9120;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_send_timeout 30s;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name hermes.example.com;
    return 301 https://$host$request_uri;
}
```

### Step 5: Create systemd service

Since the dashboard runs inside the Docker container (not as a native process), the systemd service should manage the container itself, or you can rely on Docker's `restart: unless-stopped` policy.

If you need a systemd wrapper to ensure the container starts on boot:

```ini
[Unit]
Description=app Hermes Bot (Docker)
After=docker.service network-online.target
Wants=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker compose -f /home/user/app-hermes/docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f /home/user/app-hermes/docker-compose.yml down
WorkingDirectory=/home/user/app-hermes
User=ubuntu
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

### Step 6: DNS and SSL

1. Create an A record: `hermes.example.com` → your server's public IP
2. Generate SSL (Cloudflare Origin Certificate or Let's Encrypt)
3. Enable the nginx site and reload

### Approach B: Native dashboard with HERMES_HOME override

When the bot runs in Docker but you want the dashboard as a native process (lower overhead, direct filesystem access, easier debugging), run the dashboard natively with `HERMES_HOME` pointing to the bot's config directory.

This is useful when:
- The Docker container runs only the gateway (no `HERMES_DASHBOARD=1`)
- You want the dashboard on a different port than the personal instance
- You want independent restart lifecycle for the dashboard vs the gateway

**Step-by-step:**

1. **Add dashboard config** to the bot's `config.yaml`:
   ```yaml
   dashboard:
     theme: default
     show_token_analytics: false
     basic_auth:
       username: app-bot
       password_hash: scrypt$16384$8$1$...  # generated hash
       password: ''
       secret: ''
       session_ttl_seconds: 0
     public_url: https://hermes.example.com
   ```

2. **Generate password hash** (from the Hermes venv):
   ```bash
   cd /home/user/.hermes/hermes-agent
   python3 -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('your-password'))"
   ```

3. **Create a startup script** at `/home/user/start-app-dashboard.sh`:
   ```bash
   #!/bin/bash
   set -a
   source /home/user/app-hermes/.env
   set +a
   export HERMES_HOME=/home/user/app-hermes
   export PATH=/home/user/.hermes/hermes-agent/venv/bin:...
   export VIRTUAL_ENV=/home/user/.hermes/hermes-agent/venv
   exec /home/user/.hermes/hermes-agent/venv/bin/python \
     -m hermes_cli.main dashboard --port 9120 --host 0.0.0.0 --no-open
   ```

   **Why `source .env`:** The dashboard's basic auth provider reads `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` from the environment. If the password is stored in `.env` (not config.yaml), the startup script must source it. The `set -a` / `set +a` wrapper exports all variables so the child process inherits them.

4. **Create a system-level systemd service** (`/etc/systemd/system/hermes-app-dashboard.service`):
   ```ini
   [Unit]
   Description=app Hermes Dashboard - Web UI
   After=network-online.target
   Wants=network-online.target
   StartLimitIntervalSec=0

   [Service]
   Type=simple
   User=ubuntu
   Group=ubuntu
   ExecStart=/home/user/start-app-dashboard.sh
   WorkingDirectory=/home/user/app-hermes
   Restart=always
   RestartSec=5
   KillMode=mixed
   KillSignal=SIGTERM
   TimeoutStopSec=30
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

   **Why system-level, not user-level:** `systemctl --user` commands are blocked when running inside a Hermes session (the gateway propagates SIGTERM to child processes). A system-level service avoids this entirely and also doesn't need `XDG_RUNTIME_DIR` to be set.

5. **Create nginx config** for the subdomain, pointing to the dashboard port.

6. **Get SSL** via certbot:
   ```bash
   sudo certbot certonly --nginx -d hermes.example.com
   ```

7. **Enable and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable hermes-app-dashboard
   sudo systemctl start hermes-app-dashboard
   ```

8. **Verify:**
   ```bash
   ss -tlnp | grep 9120
   curl -sL -u username:password https://hermes.example.com/ | head -5
   ```

### Pitfalls

- **Port conflict:** If the personal dashboard is on 9119, the project bot's dashboard will fail to bind to the same port. The container uses `network_mode: host`, so ports are shared. Either use a different port or ensure the personal dashboard isn't running when the bot starts.
- **`HERMES_DASHBOARD=1` is required:** Without this env var, the gateway process won't start the dashboard server. The container will run the messaging gateway only.
- **Auth gate engages on non-loopback:** If the dashboard binds to `0.0.0.0` (which happens with `network_mode: host`), the auth gate engages automatically. You MUST configure `dashboard.basic_auth` or another auth provider, or the dashboard will refuse to start with no auth providers registered.
- **Dashboard port discovery:** The dashboard port may not be predictable. Check logs after starting the container to find the actual port, then update the nginx config accordingly.
- **Approach B: first-time build delay:** The first `hermes dashboard` invocation compiles the web UI (TypeScript + Vite build), which takes 30-60 seconds. The process produces no output until the build completes. Use a longer timeout (60s+) or check `ss -tlnp` after waiting.
- **Approach B: systemctl --user blocked by gateway:** Running `systemctl --user start/stop/restart` from inside a Hermes session is blocked because the gateway propagates SIGTERM to child processes. Use a system-level service (`/etc/systemd/system/`) instead of user-level, or run the command from a separate shell. The system-level service also avoids the `XDG_RUNTIME_DIR` issue.
- **Approach B: password hash generation:** Use the dashboard's built-in hasher: `python3 -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('your-password'))"` — run from the Hermes agent venv directory. Set `dashboard.basic_auth.password_hash` and clear `dashboard.basic_auth.password` in config.yaml.

## .env Template Pattern

Never commit `.env` to git. Instead, commit a `.env.template` with placeholder values:

```env
# app Hermes Bot — Environment Configuration
# Copy this file to .env and fill in your actual tokens.
# NEVER commit this file to git.

# ── LLM Provider ──
OLLAMA_API_KEY=your_o...n

# ── Discord Bot ──
DISCORD_BOT_TOKEN=your_d...n

# ── GitHub Bot ──
GITHUB_TOKEN=your_g...e
GITHUB_REPO=app-link/app-monorepo

# ── Webhook Secret ──
WEBHOOK_SECRET=your_w...n
```

## .gitignore for Project Bots

```gitignore
# ── Secrets (never commit) ──
.env
auth.json
auth.lock
gws/
credentials.json
token_cache.json

# ── Runtime state ──
sessions/
state.db*
logs/
cache/
gateway/
gateway_state.json
channel_directory.json

# ── Hermes install artifacts ──
hermes-agent/
plugins/
lsp/
sandboxes/

# ── Skill artifacts ──
skills/.archive/

# ── OS files ──
.DS_Store
__pycache__/
*.pyc
*.pyo

# ── Lock files ──
*.lock
```

## SOUL.md for a Project Bot

The SOUL should define the bot's role, personality, and domain knowledge. Example structure:

1. **Identity** — "You are the app Bot — a dedicated AI assistant for the app project."
2. **Personality** — helpful, precise, proactive, technical but approachable
3. **Communication Style** — scannable GitHub event formatting, code blocks for commands
4. **Work Ethic** — follow through, ask when ambiguous, prefer doing over describing
5. **Boundaries** — no sharing private info, no irreversible actions without confirmation
6. **Vibe** — senior engineer who's also the team's DevOps person

## AGENTS.md for a Project Bot

The AGENTS.md is the operating manual. It should cover:

- **What the bot does** — Discord responses, GitHub monitoring, codebase inspection
- **Key paths** — where config, skills, and the codebase live
- **Discord setup** — required intents, auth gates, config reference
- **GitHub integration** — webhook setup, CLI commands, CI status checks
- **Codebase access** — what the bot can read, search, build (and what it can't modify)
- **Cron jobs** — scheduled tasks the bot runs
- **Bot rules** — never commit secrets, Discord-first responses, codebase search before answering
- **Troubleshooting** — common issues and fixes

## Starting the Bot

```bash
# First time: copy template and fill in secrets
cp ~/app-hermes/.env.template ~/app-hermes/.env
# Edit ~/app-hermes/.env with your tokens

# Start the container
cd ~/app-hermes && docker compose up -d

# Check logs
docker logs app-hermes --tail 20

# Verify gateway is running
docker exec app-hermes hermes gateway status
```

## Git Tracking

Optionally track the bot's config in its own git repo:

```bash
cd ~/app-hermes
git init
git add -A
git commit -m "init: project bot scaffold"
git remote add origin git@github.com:your-org/app-hermes.git
git push -u origin main
```

The `.gitignore` ensures secrets and runtime state are never committed.

## Pitfalls

- **Permission denied on mounted volumes** — always set `HERMES_UID`/`HERMES_GID` to match the host user. Verify with `stat -c '%u:%g' <path>`.
- **Discord bot silent** — the #1 cause is **Message Content Intent** not enabled in Discord Developer Portal. The bot handshake succeeds but it can't read messages.
- **Webhook not firing** — check that `WEBHOOK_SECRET` matches between `.env` and GitHub webhook config. Also verify the gateway is running: `docker exec <container> hermes gateway status`.
- **Read-only codebase** — the bot can't fix code, only report issues. If a build fails, run `bun run build` to reproduce the exact error and report it with file paths.
- **Git worktree path** — inside the container, the data dir is `/opt/data`, not `~/.hermes`. Fix git worktree config: `git --git-dir=/opt/data/.git config core.worktree /opt/data`.
- **SSH key for git push** — mount `~/.ssh:ro` and use explicit `GIT_SSH_COMMAND` in scripts (SSH agent may not be running in the container).
