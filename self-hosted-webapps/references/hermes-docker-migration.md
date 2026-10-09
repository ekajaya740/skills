# Hermes Docker Migration

Moving Hermes from baremetal (systemd) to Docker containers.

## Architecture

Single container per profile, each with its own data directory:

```
~/hermes-docker/docker-compose.yml
~/.hermes/              → /opt/data  (personal)
~/.hermes-business/     → /opt/data  (business, future)
```

## Docker Compose Template

```yaml
services:
  hermes-personal:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-personal
    restart: unless-stopped
    network_mode: host
    volumes:
      - ~/.hermes:/opt/data
      # NOTE: the old personal knowledge vault (~/second-brain) is RETIRED (knowledge now lives in
      # Notion) — do not mount it.
    environment:
      - HERMES_UID=1000        # match host user's uid
      - HERMES_GID=1000        # match host user's gid
      - HERMES_DASHBOARD=1
    command: ["gateway", "run"]
```

## Migration Steps

1. **Stop systemd services** (from host, not inside gateway):
   ```bash
   systemctl --user stop hermes-gateway hermes-dashboard
   systemctl --user disable hermes-gateway hermes-dashboard
   ```

2. **Create compose file** at `~/hermes-docker/docker-compose.yml`

3. **Start container:**
   ```bash
   cd ~/hermes-docker && docker compose up -d
   ```

4. **Verify:**
   ```bash
   docker ps | grep hermes-personal
   docker logs hermes-personal --tail 20
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/   # should be 302 (login)
   ```

## Volume Permission Pitfall

The container runs as `hermes` user (UID 10000 by default). If you mount a host volume owned by a different UID (e.g. 1000), writes will fail with "Permission denied."

**Fix:** Set `HERMES_UID` and `HERMES_GID` in the compose file to match the host user:

```bash
# On host, check the owner of the dir you're mounting (e.g. ~/.hermes)
stat -c '%u:%g' ~/.hermes/
# → 1000:1000

# In compose:
environment:
  - HERMES_UID=1000
  - HERMES_GID=1000
```

The s6 stage2 hook remaps the internal `hermes` user to these values via usermod/groupmod.

## Git Worktree Path Inside Container

The git config at `.git/config` has `worktree = /home/user/.hermes` (the host path). Inside the container, the data dir is `/opt/data`. Fix with:

```bash
git --git-dir=/opt/data/.git config core.worktree /opt/data
```

After this, `cd /opt/data && git status` works normally.

## SSH Key for Git Push

The container needs an SSH key to push to GitHub. Mount the host's SSH key:

```yaml
volumes:
  - ~/.ssh:/opt/data/home/.ssh:ro
```

The key lives at `$HERMES_HOME/home/.ssh/id_ed25519` inside the container. Use explicit `GIT_SSH_COMMAND` in scripts (SSH agent may not be running):

```python
GIT_SSH_COMMAND = "ssh -i /opt/data/home/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new"
```

**Important:** Add `.ssh/` and `home/.ssh/` to `.gitignore` to prevent accidental commit of SSH keys. If accidentally committed, force-push to remove from history.

## Write Tool Limitation

The `write_file` tool refuses to write to paths outside `/opt/data` (e.g. a host dir mounted as `/home/user/<something>/`). To write to mounted volumes outside the data dir, use `terminal` with `cat` or `echo` instead:

```bash
cat > /home/user/<mount>/outbox/note.md << 'EOF'
content here
EOF
```

## Nginx Config Update

When moving from systemd to Docker with `network_mode: host`, the dashboard binds to `0.0.0.0` (not `127.0.0.1`). Update the nginx Host header:

```nginx
# Before (systemd, dashboard on 127.0.0.1):
proxy_set_header Host "127.0.0.1";

# After (Docker, dashboard on 0.0.0.0):
proxy_set_header Host $host;
```

Also set `dashboard.public_url` in config.yaml so the auth gate constructs correct redirect URLs.

## Dashboard Auth

The Docker container's dashboard binds to `0.0.0.0` by default (required for `-p` port mapping). The auth gate engages automatically. Configure basic auth:

```yaml
# config.yaml
dashboard:
  basic_auth:
    username: your-username
    password_hash: "scrypt$..."  # hash, not plaintext
  public_url: "https://hermes.yourdomain.com"
```

Generate a password hash:
```bash
python3 -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('your-password'))"
```
