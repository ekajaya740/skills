# GWS Token Management

Google OAuth token refresh and config repo sync for Hermes running in Docker.

## Architecture

A `no_agent=True` cron job runs every 30 minutes:
1. Reads `credentials.json` from the GWS directory
2. Refreshes the access token via `https://oauth2.googleapis.com/token`
3. Writes the new token back to `credentials.json`
4. Commits and pushes any changes to the config git repo

## Cron Job Setup

```bash
# Create the cron job (script lives in ~/.hermes/scripts/)
hermes cron create --name gws-token-sync --schedule "30m" --script sync-gws-creds.py --no-agent

# Make it repeat forever
hermes cron edit <job-id> --repeat 0
```

## Script: `sync-gws-creds.py`

The script lives at `~/.hermes/scripts/sync-gws-creds.py` and:

- Reads `HERMES_HOME/gws/credentials.json` for the refresh token
- POSTs to Google's OAuth endpoint to get a fresh access token
- Updates `credentials.json` with the new token
- Runs `git add -A && git commit -m "..." && git push` in `HERMES_HOME`

### Git push from inside Docker

The container's SSH key is at `$HERMES_HOME/home/.ssh/id_ed25519`. The script uses an explicit `GIT_SSH_COMMAND` to avoid SSH agent dependency:

```python
SSH_CMD = ["ssh", "-i", str(HERMES_HOME / "home" / ".ssh" / "id_ed25519"),
           "-o", "StrictHostKeyChecking=accept-new"]
GIT_ENV = {**os.environ, "GIT_SSH_COMMAND": " ".join(SSH_CMD)}
subprocess.run(["git", "push"], env=GIT_ENV, ...)
```

### Pitfalls

- **SSH key must be mounted into the container.** The key lives at `~/.ssh/id_ed25519` on the host and is mounted to `$HERMES_HOME/home/.ssh/` (which is `/opt/data/home/.ssh/` inside the container).
- **Do NOT commit SSH keys to git.** Add `.ssh/` and `home/.ssh/` to `.gitignore`. If accidentally committed, force-push to remove from history.
- **`token_cache.json` is encrypted** (binary, not UTF-8). Do not try to read it as text. The `credentials.json` file is the plaintext working copy.
- **Refresh token expiry.** If the refresh token itself expires (`invalid_grant`), the full OAuth flow must be re-run. The cron job logs this failure but cannot recover automatically.
