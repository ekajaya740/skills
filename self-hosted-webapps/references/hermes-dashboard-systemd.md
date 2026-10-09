# Hermes Dashboard — Systemd Service Setup

The Hermes Dashboard (`hermes dashboard`) has **no built-in systemd service** — it's started via the CLI and dies when the process exits or the server reboots. This reference covers making it persistent.

## Service Unit (user-level, recommended)

For a user-level service (no sudo needed):

```ini
[Unit]
Description=Hermes Agent Dashboard — Web UI
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/home/user/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main dashboard --port 9119 --host 0.0.0.0 --no-open
WorkingDirectory=/home/user/.hermes
Environment="PATH=/home/user/.hermes/hermes-agent/venv/bin:/home/user/.hermes/hermes-agent/node_modules/.bin:/home/user/.hermes/node/bin:/home/user/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/user/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/user/.hermes"
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Key points:**
- **`--host 0.0.0.0`** — required for nginx proxy setups. The auth gate engages automatically (basic auth or OAuth must be configured in config.yaml). `--host 127.0.0.1` causes `origin_mismatch` on the embedded chat WebSocket when accessed through nginx.
- **`--no-open`** — prevents the dashboard from trying to open a browser (no display available on servers).
- **`WorkingDirectory=/home/user/.hermes`** — ensures config.yaml and .env are found.
- **`Restart=always`** — survives crashes and reboots.

## Alternative: system-level service (sudo)

```ini
[Unit]
Description=Hermes Agent Dashboard — Web UI
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
ExecStart=/home/user/.hermes/scripts/start-dashboard.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/home/user/.hermes
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

With startup script at `/home/user/.hermes/scripts/start-dashboard.sh`:

```bash
#!/bin/bash
# Source .env if the password is stored there (HERMES_DASHBOARD_BASIC_AUTH_PASSWORD)
set -a
source /home/user/.hermes/.env 2>/dev/null || true
set +a
cd /home/user/.hermes
hermes dashboard --port 9119 --host 0.0.0.0 --no-open
```

Make it executable: `chmod +x /home/user/.hermes/scripts/start-dashboard.sh`

## Install & Enable

```bash
# For user-level service:
systemctl --user daemon-reload
systemctl --user enable hermes-dashboard.service
systemctl --user start hermes-dashboard.service

# For system-level service (sudo):
sudo systemctl daemon-reload
sudo systemctl enable hermes-dashboard.service
sudo systemctl start hermes-dashboard.service
```

## Verification

```bash
# Check service status
systemctl --user status hermes-dashboard --no-pager -l

# Check port is listening
ss -tlnp | grep 9119

# Check through nginx
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/

# Check through public domain
curl -s -o /dev/null -w "%{http_code}" https://hermes.yourdomain.com/
```

## Pitfalls

- **`systemctl --user start/stop/restart` blocked by gateway process** — if you're running this from inside a Hermes session, systemctl may be blocked because the gateway propagates SIGTERM to child processes. Run from a separate shell (SSH, tmux pane), or just `enable` the service (it starts on next boot). Alternatively, delegate to a subagent.
- **`hermes dashboard --status` is not a health check** — it shows running processes but doesn't tell you if a systemd service exists. Always check `systemctl --user status hermes-dashboard` and `ss -tlnp | grep 9119` independently.
- **No auto-restart without systemd** — if you start the dashboard via CLI or background terminal, a crash or reboot kills it silently. The 502 Bad Gateway is the only symptom.
- **User mismatch** — the service runs as the user who owns `~/.hermes/`. If you change the user, ensure paths are accessible.
- **Auth gate requires a configured provider** — `--host 0.0.0.0` engages the auth gate. If no auth provider is configured (basic auth or OAuth), the dashboard refuses to start with: `Refusing to bind dashboard to 0.0.0.0 — the auth gate engages on non-loopback binds, but no auth providers are registered.` Configure `dashboard.basic_auth` in config.yaml first.
- **`--insecure` is deprecated** (June 2026) — no longer bypasses auth. A non-loopback bind always requires a configured auth provider.
