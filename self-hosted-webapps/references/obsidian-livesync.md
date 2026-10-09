# Obsidian LiveSync — CouchDB Backend

Deploy CouchDB as the sync backend for Obsidian's Self-hosted LiveSync plugin.

## Architecture

```
Obsidian (desktop/mobile) → HTTPS → nginx → CouchDB (Docker, 127.0.0.1:5984)
```

## Quick Deploy

### 1. Create project directory

```bash
mkdir -p ~/obsidian-livesync/data ~/obsidian-livesync/etc
cd ~/obsidian-livesync
```

### 2. Generate credentials

```bash
COUCHDB_USER="ols_admin"
COUCHDB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
DB_NAME="obsidiannotes"
PASSPHRASE=$(openssl rand -base64 16 | tr -dc 'a-z' | head -c 20)

echo "Save these credentials:"
echo "User: $COUCHDB_USER"
echo "Pass: $COUCHDB_PASSWORD"
echo "DB:   $DB_NAME"
echo "Enc:  $PASSPHRASE"
```

### 3. Create `.env`

```bash
cat > .env << EOF
COUCHDB_USER=${COUCHDB_USER}
COUCHDB_PASSWORD=${COUCHDB_PASSWORD}
EOF
```

### 4. Create `docker-compose.yml`

```yaml
services:
  couchdb:
    image: couchdb:latest
    container_name: obsidian-livesync
    env_file:
      - .env
    volumes:
      - ./data:/opt/couchdb/data
      - ./etc:/opt/couchdb/etc/local.d
    ports:
      - 127.0.0.1:5984:5984
    restart: unless-stopped
```

### 5. Start CouchDB

```bash
docker compose up -d
```

### 6. Initialize CouchDB for LiveSync

```bash
cd ~/obsidian-livesync
source .env
export hostname=http://127.0.0.1:5984 username=$COUCHDB_USER password=$COUCHDB_PASSWORD
curl -s https://raw.githubusercontent.com/vrtmrz/obsidian-livesync/main/utils/couchdb/couchdb-init.sh | bash
```

Expected output: `{"ok":true}` followed by empty responses, ending with `<-- Configuring CouchDB by REST APIs Done!`

### 7. Verify

```bash
curl -s http://127.0.0.1:5984/
# Should return: {"couchdb":"Welcome","version":"3.5.2",...}
```

## Nginx Reverse Proxy

Create `/etc/nginx/sites-available/obsidian-sync`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name obsidian-sync.yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5984;
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

Enable and get SSL:

```bash
sudo ln -sf /etc/nginx/sites-available/obsidian-sync /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### SSL Options

**Option A — Let's Encrypt (DNS-only/grey cloud):**
```bash
sudo certbot --nginx -d obsidian-sync.yourdomain.com
```
Requires DNS A record pointing to server IP with Cloudflare proxy OFF.

**Option B — Cloudflare Origin Certificate (Proxied + Full Strict, orange cloud ON):**
Generate in Cloudflare Dashboard → SSL/TLS → Origin Server → Create Certificate. Hostnames: `obsidian-sync.yourdomain.com`. Download the `.pem` and `.key` files.

**Install on server:**
```bash
sudo cp obsidian-sync.pem /etc/ssl/certs/obsidian-sync.pem
sudo cp obsidian-sync.key /etc/ssl/private/obsidian-sync.key
sudo chmod 644 /etc/ssl/certs/obsidian-sync.pem
sudo chmod 600 /etc/ssl/private/obsidian-sync.key
```

**⚠️ PEM blank line pitfall:** Pasting PEM content via vim often inserts extra blank lines inside the base64 body. This breaks OpenSSL/nginx. Verify immediately:

```bash
sudo openssl rsa -in /etc/ssl/private/obsidian-sync.key -check -noout
# Should print: "RSA key ok"
# If it fails, fix with:
sudo python3 -c "
for f in '/etc/ssl/private/obsidian-sync.key' '/etc/ssl/certs/obsidian-sync.pem':
    with open(f) as fh: content = fh.read()
    lines = [l for l in content.splitlines() if l.strip()]
    with open(f, 'w') as fh: fh.write('\n'.join(lines) + '\n')
"
```

Then update nginx config to use SSL. Use this template (full HTTP→HTTPS redirect + SSL block):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name obsidian-sync.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name obsidian-sync.yourdomain.com;

    ssl_certificate /etc/ssl/certs/obsidian-sync.pem;
    ssl_certificate_key /etc/ssl/private/obsidian-sync.key;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5984;
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

Always run `sudo nginx -t` before reloading.

## Generate Setup URI for Obsidian

On a machine with `deno` installed:

```bash
export hostname=https://obsidian-sync.yourdomain.com
export database=obsidiannotes
export passphrase=<your-encryption-passphrase>
export username=ols_admin
export password=<couchdb-password>
deno run -A https://raw.githubusercontent.com/vrtmrz/obsidian-livesync/main/utils/flyio/generate_setupuri.ts
```

This outputs:
- A setup URI: `obsidian://setuplivesync?settings=...`
- A setup-URI passphrase (save this separately from the encryption passphrase)

## Obsidian Client Setup

1. Install **Self-hosted LiveSync** community plugin
2. Command palette → "Use the copied setup URI" → paste the URI
3. Enter the setup-URI passphrase
4. Answer "yes" → "Set it up" → "Keep them disabled"
5. Reload Obsidian

## Git → CouchDB Bridge: obsidian-git-livesync

For headless/server-side vault changes (git hooks, CI, scripts), use [obsidian-git-livesync](https://github.com/ecstatic-pirate/obsidian-git-livesync) to push markdown files directly to CouchDB in LiveSync's document format. This lets phone/desktop LiveSync clients replicate changes even when Obsidian desktop isn't running.

### Install

```bash
cd ~/your-vault
npm init -y
npm install obsidian-git-livesync
```

### Configure

```bash
npx obsidian-git-livesync init
# Edit .obsidian-git-livesync.json with CouchDB credentials
```

Config file (`.obsidian-git-livesync.json`):
```json
{
  "couchdbUrl": "http://localhost:5984",
  "couchdbUser": "ols_admin",
  "couchdbPassword": "<your-password>",
  "couchdbDatabase": "obsidiannotes",
  "vaultRoot": ".",
  "extensions": [".md"],
  "debounce": 200
}
```

**Security:** Add `.obsidian-git-livesync.json` to `.gitignore` — it contains CouchDB credentials.

### Validate & Sync

```bash
npx obsidian-git-livesync validate
npx obsidian-git-livesync sync --all      # sync everything
npx obsidian-git-livesync sync --git      # sync last commit's changes only
```

### Auto-sync via Git Hook

```bash
cat > .git/hooks/post-commit << 'HOOK'
#!/bin/bash
npx obsidian-git-livesync sync --git --verbose 2>&1
HOOK
chmod +x .git/hooks/post-commit
```

### NPM Scripts

```json
{
  "scripts": {
    "sync": "npx obsidian-git-livesync sync --all",
    "sync:git": "npx obsidian-git-livesync sync --git",
    "validate": "npx obsidian-git-livesync validate"
  }
}
```

### Pitfalls

- **CRITICAL: obsidian-git-livesync does NOT create CouchDB design documents.** The LiveSync plugin uses `filter=_selector` in its CouchDB `_changes` requests. This filter requires a `_design/_selector` document that only the LiveSync plugin itself creates during its own setup flow. If you sync files with `obsidian-git-livesync` before LiveSync has created the database, the phone will connect successfully but see zero changes and zero files — the `_selector` filter returns nothing because the design doc doesn't exist. **Fix:** Let the phone's LiveSync create the database first (Setup with username/password), THEN run `obsidian-git-livesync sync --all` to push files into it. If you already have a database without design docs, delete it and let LiveSync recreate it.
- **LiveSync checkpoint desync:** After connecting, the phone may report "replication already in progress" but show no data uploaded or downloaded. This happens when the phone's local checkpoint references a CouchDB sequence number that is already at the latest — it thinks it's caught up when it has no files. **Fix:** In LiveSync settings, find "Reset checkpoint" or "Wipe local database" or "Resync from scratch" to force it to fetch from seq 0.
- **"Failed to read file" error:** This error in LiveSync logs means the plugin found document metadata but couldn't read the actual file content. In the case of `obsidian-git-livesync`, the data IS present (metadata docs with `children` arrays pointing to chunk docs with `data` fields), but the `_selector` filter design doc is missing, so LiveSync never sees the documents at all. The error message is misleading — the problem is the filter, not the data.
- **node_modules in git:** Add `node_modules/` to `.gitignore`. Only commit `package.json`.
- **First sync is slow:** Initial sync of 300+ files may take a minute. Subsequent `--git` syncs are incremental.
- **E2E encryption:** If LiveSync has E2E encryption enabled, the git bridge writes files as-is on disk. The encryption is handled by LiveSync on the client side, not the bridge.

## Obsidian Client Setup

1. Install **Self-hosted LiveSync** community plugin
2. **First device:** Setup with username/password
   - URI: `https://obsidian-sync.yourdomain.com`
   - Username/Password: CouchDB credentials
   - Database name: `obsidiannotes` (or whatever you named it)
   - Enable E2E encryption (recommended) — save the passphrase in a password manager
3. **Subsequent devices:** Use Setup URI generated by the first device
4. Command palette → "Use the copied setup URI" → paste
5. Enter the setup-URI passphrase when prompted
6. Answer "yes" → "Set it up" → "Keep them disabled"
7. Reload Obsidian

### Plugin Settings (after setup)

- Sync on save → ON
- Sync on startup → ON
- Sync on file open → ON
- Sync interval: 15-30s

## Pitfalls

- **CouchDB uid 5984**: The container runs as uid 5984. Don't `chown` host directories to 5984 manually — let Docker handle volume ownership automatically.
- **DNS before SSL**: certbot's nginx authenticator requires DNS to resolve first. For Cloudflare Origin Certs this is not needed — you can install the cert before DNS propagates.
- **Cloudflare proxy must be ON (orange cloud)** for Cloudflare Origin Certificate setup. In Cloudflare Dashboard: SSL/TLS → Overview → Full (Strict), and Edge Certificates → Always Use HTTPS → ON.
- **PEM key corruption from vim paste**: Cloudflare Origin Cert keys pasted via vim often get blank lines inserted. Always verify with `openssl rsa -check -noout` before reloading nginx.
- **write_file tool cannot write to `/etc/` paths**: Use `terminal` with `sudo` and heredoc/cat redirection instead.
- **CORS origins**: The init script sets CORS origins to `app://obsidian.md,capacitor://localhost,http://localhost`. This covers desktop and mobile Obsidian apps.
- **Coordinate cert and key paths in nginx config**: A single character typo in `ssl_certificate` or `ssl_certificate_key` paths causes nginx test to fail. Double-check paths after writing the config — especially with long domain names.
- **CouchDB credentials in Docker:** Credentials are in the container's environment variables, NOT in config files on disk. To find them: `docker exec <container> sh -c 'echo $COUCHDB_USER; echo $COUCHDB_PASSWORD'`. Config files at `/etc/couchdb/` or `/opt/couchdb/etc/` may not exist or may be empty — the Docker image uses env vars exclusively.
- **Empty database after LiveSync setup:** LiveSync creates the database but doesn't push any files. You must push from desktop first or run the git bridge sync on the server. Phone shows empty vault until data exists in CouchDB.
- **Empty database after LiveSync setup:** LiveSync creates the database but doesn't push any files. You must push from desktop first or run the git bridge sync on the server. The container runs as uid 5984. Don't `chown` host directories to 5984 manually — let Docker handle volume ownership automatically.
- **DNS before SSL**: certbot's nginx authenticator requires DNS to resolve first. For Cloudflare Origin Certs this is not needed — you can install the cert before DNS propagates.
- **Cloudflare proxy must be ON (orange cloud)** for Cloudflare Origin Certificate setup. In Cloudflare Dashboard: SSL/TLS → Overview → Full (Strict), and Edge Certificates → Always Use HTTPS → ON.
- **PEM key corruption from vim paste**: Cloudflare Origin Cert keys pasted via vim often get blank lines inserted. Always verify with `openssl rsa -check -noout` before reloading nginx.
- **write_file tool cannot write to `/etc/` paths**: Use `terminal` with `sudo` and heredoc/cat redirection instead.
- **docker compose up -d**: The terminal tool blocks this as a long-lived process. Use `background=true` when running through the tool.
- **CORS origins**: The init script sets CORS origins to `app://obsidian.md,capacitor://localhost,http://localhost`. This covers desktop and mobile Obsidian apps.
- **Coordinate cert and key paths in nginx config**: A single character typo in `ssl_certificate` or `ssl_certificate_key` paths causes nginx test to fail with misleading errors. Double-check paths after writing the config — especially with long domain names where typos like `mysite.com` vs `mysitee.com` are easy to make.
- **User preference — Cloudflare config:** User manages Cloudflare Dashboard themselves (DNS records, proxy toggle, SSL mode, Origin Cert generation). Agent handles server-side only: placing certs, configuring nginx, managing Docker containers.
- **User preference — technical tasks:** User is technical (self-hosts Hermes, uses Docker, nginx, Cloudflare). Agent should execute tasks directly — read/write files, run configs, check services — without asking the user to run commands and paste output.
