# Hermes Dashboard — Basic Auth Setup

The Hermes Dashboard has a built-in auth framework with three bundled provider plugins:

| Provider | Type | Best for |
|----------|------|----------|
| `basic` | Username/password (scrypt hashed, HMAC-signed tokens) | Self-hosted, no OAuth IDP |
| `nous` | OAuth via Nous Portal (PKCE, RS256 JWTs) | Nous Portal users |
| `self-hosted` | Generic OpenID Connect (Google, GitHub, Keycloak, Authentik, etc.) | Any OIDC provider |

## Auth gate engagement

The auth gate engages **automatically** when the dashboard binds to a **non-loopback** host (`0.0.0.0`, `::`, or any public IP) **without** the `--insecure` flag.

| Bind address | `--insecure`? | Auth gate |
|---|---|---|
| `127.0.0.1` / `localhost` / `::1` | N/A | **Off** (loopback mode, legacy `_SESSION_TOKEN`) |
| `0.0.0.0` | No | **On** (OAuth / password gate) |
| `0.0.0.0` | Yes | **Off** (operator opted out) |

## Basic auth setup

### 1. Configure in config.yaml

```yaml
dashboard:
  basic_auth:
    username: your-username
    password: your-password          # plaintext (hashed in-memory at load)
    # OR precomputed scrypt hash (preferred — no plaintext at rest):
    # password_hash: "scrypt$16384$8$1$..."
    secret: ''                       # optional; random per-process if empty
    session_ttl_seconds: 43200       # optional; default 12h
```

Or via env vars (env wins over config.yaml):
```
HERMES_DASHBOARD_BASIC_AUTH_USERNAME
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD       # plaintext fallback
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH  # preferred
HERMES_DASHBOARD_BASIC_AUTH_SECRET
HERMES_DASHBOARD_BASIC_AUTH_TTL_SECONDS
```

### 2. Generate a password hash (optional, recommended)

```bash
cd ~/.hermes/hermes-agent
python -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('your-password'))"
```

Then set `password_hash` in config and clear the plaintext `password` field.

### 3. Change bind address

Edit the systemd service to bind to `0.0.0.0`:

```ini
ExecStart=.../python -m hermes_cli.main dashboard --port 9119 --host 0.0.0.0 --no-open
```

### 4. Restart

```bash
systemctl --user daemon-reload
systemctl --user restart hermes-dashboard
```

## Behind nginx reverse proxy

When proxying through nginx, the dashboard validates the `Host` header against its bound address. Set the header explicitly:

```nginx
location / {
    proxy_pass http://127.0.0.1:9119;
    proxy_set_header Host "127.0.0.1";   # dashboard expects this
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Login flow

- **Login page:** `GET /login` — server-rendered HTML (no JS dependency for OAuth providers; password form uses a small inline script)
- **Password login:** `POST /auth/password-login` with JSON body `{"provider":"basic","username":"...","password":"..."}`
- **Session cookies:** `hermes_session_at` (access token, ~15 min) + `hermes_session_rt` (refresh token, 30d) — both HttpOnly, SameSite=Lax
- **Transparent refresh:** Expired access tokens auto-rotate via the refresh token cookie
- **Rate limiting:** 10 password attempts per 60s per client IP (in-process, resets on restart)

## Verification

```bash
# Check registered providers
curl -s http://127.0.0.1:9119/api/auth/providers

# Test login
curl -s -X POST http://127.0.0.1:9119/auth/password-login \
  -H "Content-Type: application/json" \
  -d '{"provider":"basic","username":"...","password":"..."}'

# Unauthenticated requests get 302 → /login
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/
# → 302
```

## Pitfalls

- **Config changes need restart.** `hermes config set` writes to config.yaml but the running dashboard doesn't hot-reload it. Always `systemctl --user restart hermes-dashboard` after auth config changes.
- **Don't commit passwords to git.** The config repo at `~/.hermes/` tracks config.yaml. Use `password_hash` (precomputed) instead of plaintext `password`, or set via env var.
- **Loopback mode has no auth.** If you bind to `127.0.0.1` (the default), the auth gate is off regardless of config. The dashboard relies on the legacy `_SESSION_TOKEN` mechanism in that mode.
- **Session cookies are per-prefix.** If behind a reverse proxy with a path prefix (e.g. `/hermes/`), cookie names use `__Secure-` prefix and `Path=/hermes`. Direct deploys use `__Host-` prefix and `Path=/`.
- **Password rate limit is in-process.** Resets on dashboard restart. Not suitable as the sole brute-force defence — pair with fail2ban or nginx rate limiting at the proxy layer.
