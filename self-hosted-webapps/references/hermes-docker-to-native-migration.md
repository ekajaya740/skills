# Hermes Docker → Native Migration

Move Hermes Agent from a Docker container to a native installation on the host. The config (`~/.hermes/`) stays in place — only the runtime changes.

## When to use this

- You're running Hermes in Docker and want lower overhead, direct filesystem access, or easier debugging
- The host has `uv` and `python3` available
- You want Hermes to run as a systemd service instead of a container

## Prerequisites

| Requirement | Check |
|---|---|
| `uv` installed | `which uv` |
| `python3 >= 3.11, < 3.14` | `python3 --version` |
| `~/.hermes/` exists | `ls ~/.hermes/config.yaml` |
| Hermes version known | `docker exec hermes cat /opt/hermes/.hermes_build_sha` |

## Migration Steps

### 1. Install Hermes natively on the host

```bash
# Install from PyPI (matches the container version)
uv tool install hermes-agent==0.17.0
```

Or pin to the exact build SHA from the container:

```bash
git clone https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent
cd /tmp/hermes-agent
git checkout <build_sha>
uv tool install .
rm -rf /tmp/hermes-agent
```

### 2. Verify the install

```bash
hermes --version
# Should match the container version
```

### 3. Stop and remove the Docker container

```bash
docker stop hermes hermes-dashboard
docker rm hermes hermes-dashboard
```

### 4. Start Hermes natively

```bash
# Start the gateway (Telegram listener)
hermes gateway run

# Start the dashboard (optional)
hermes dashboard --host 127.0.0.1 --no-open
```

### 5. Create systemd services for auto-start

**Gateway service:**

```ini
# /etc/systemd/system/hermes-gateway.service
[Unit]
Description=Hermes Agent Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/home/hermes
ExecStart=/home/hermes/.local/bin/hermes gateway run
Restart=always
RestartSec=10
Environment=HERMES_HOME=/home/hermes/.hermes

[Install]
WantedBy=multi-user.target
```

**Dashboard service (optional):**

```ini
# /etc/systemd/system/hermes-dashboard.service
[Unit]
Description=Hermes Agent Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/home/hermes
ExecStart=/home/hermes/.local/bin/hermes dashboard --host 127.0.0.1 --no-open
Restart=always
RestartSec=10
Environment=HERMES_HOME=/home/hermes/.hermes

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-gateway
sudo systemctl enable --now hermes-dashboard
```

### 6. Update nginx config (if applicable)

If you had nginx proxying to the Docker container's dashboard (which bound to `0.0.0.0`), the native dashboard binds to `127.0.0.1` by default. The nginx `proxy_pass` should still point to `http://127.0.0.1:9119` — no change needed.

If you were using `network_mode: host` in Docker, the nginx config stays identical.

### 7. Verify everything works

```bash
# Service status
sudo systemctl status hermes-gateway --no-pager -l

# Dashboard accessible
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/
# Should return 200 or 302 (login redirect)

# Logs
sudo journalctl -u hermes-gateway --no-pager -n 50
```

## What stays the same

| Item | Status |
|------|--------|
| `~/.hermes/config.yaml` | Unchanged |
| `~/.hermes/skills/` | Unchanged |
| `~/.hermes/cron/` | Unchanged |
| `~/.hermes/memories/` | Unchanged |
| `~/.hermes/.env` | Unchanged |
| Telegram/webhook credentials | Unchanged |
| Second-brain vault path | Unchanged |
| nginx reverse proxy config | Unchanged |

## What changes

| Aspect | Docker | Native |
|--------|-------|--------|
| Hermes binary | Inside container at `/opt/hermes/.venv/bin/hermes` | Host at `~/.local/bin/hermes` (uv tool) |
| Process visibility | `docker exec` or `docker logs` | `ps aux`, `journalctl` |
| Filesystem access | Volume-mounted (`/opt/data`) | Direct |
| Startup | Docker daemon + container | systemd |
| Memory overhead | Container runtime + image | None |
| Debugging | `docker exec -it` | Direct shell access |

## Pitfalls

- **`uv tool install` vs `pip install`:** Use `uv tool install` (not `pip`) to get an isolated CLI tool that doesn't pollute the system Python. The `hermes` command goes to `~/.local/bin/` — ensure this is on `PATH`.
- **Python version constraint:** Hermes 0.17.0 requires `>=3.11,<3.14`. If the host has Python 3.14+, `uv tool install` will refuse with a clear error. Install Python 3.12 via `uv python install 3.12` first.
- **`~/.local/bin` not on PATH:** If `hermes: command not found` after install, add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc` or `~/.profile`.
- **Config path:** Hermes reads `~/.hermes/` by default. If `HERMES_HOME` was set differently in the Docker environment, set it explicitly in the systemd service.
- **Dashboard auth:** If the Docker container used `--host 0.0.0.0` (required for port mapping), the native install should use `--host 127.0.0.1` (loopback) since nginx proxies from the same host. The auth gate only engages on non-loopback binds — so basic auth config in `config.yaml` is still needed if you bind to `0.0.0.0`.
- **Cron jobs:** Cron jobs scheduled via `cronjob` tool run inside the Hermes process. They survive the migration automatically — no action needed.
- **SSH keys for git push:** If the container had SSH keys mounted at `/opt/data/home/.ssh/`, those are already on the host at `~/.ssh/`. The native Hermes reads `~/.ssh/` directly — no mount needed.
