# Astro SSR Password Auth Guard

A simple password-guarded web app using Astro SSR middleware and a GET-based login flow to avoid Astro's built-in CSRF protection.

## Architecture

```
Browser → nginx (443) → Astro SSR (4321)
                           |
                      middleware checks
                      'session' cookie
                           |
               +-----------+-----------+
               | match?                | no match?
               |                       |
           allow through          redirect to /login
```

## Key Concepts

### Why GET-based login?

Astro 5's `@astrojs/node` adapter enables automatic CSRF checks that block POST requests from cross-origin form submissions. Using a GET-based form (password in query param) bypasses this entirely.

This also makes curl testing trivial — no need to handle POST payloads or headers.

### Session cookie

Set a `session` cookie with the password as its value, expiring in 30 days. Check it in middleware on every request.

## Implementation

### Step 1: Create `src/middleware.ts`

```ts
import { defineMiddleware } from 'astro/middleware';

const PASSWORD = process.env.DASHBOARD_PASSWORD || 'changeme';
const PUBLIC_ROUTES = ['/login', '/_astro'];

export const onRequest = defineMiddleware((context, next) => {
  const url = new URL(context.request.url);
  if (PUBLIC_ROUTES.some((p) => url.pathname.startsWith(p))) return next();
  if (context.cookies.get('session')?.value === PASSWORD) return next();
  return context.redirect('/login');
});
```

### Step 2: Create `src/pages/login.astro`

```astro
---
const PASSWORD = process.env.DASHBOARD_PASSWORD ?? 'changeme';
const error = Astro.url.searchParams.get('error');
const password = Astro.url.searchParams.get('password');
const redirectTo = Astro.url.searchParams.get('redirect') || '/';

if (password) {
  if (password === PASSWORD) {
    Astro.cookies.set('session', password, {
      path: '/', httpOnly: true, maxAge: 60 * 60 * 24 * 30,
    });
    return Astro.redirect(redirectTo);
  }
  return Astro.redirect('/login?error=1' + (redirectTo !== '/' ? '&redirect=' + encodeURIComponent(redirectTo) : ''));
}
---
<html lang="en">
  <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Login</title></head>
  <body>
    <h1>Login</h1>
    {error && <p style="color:red;">Invalid password</p>}
    <form method="GET" action="/login">
      <input type="hidden" name="redirect" value={redirectTo} />
      <input type="password" name="password" placeholder="Password" />
      <button type="submit">Login</button>
    </form>
  </body>
</html>
```

### Step 3: Pass the password as an env var

```bash
# Docker Compose — use .env file
DASHBOARD_PASSWORD=yourpassword
```

In `docker-compose.yml`:
```yaml
environment:
  DASHBOARD_PASSWORD: ${DASHBOARD_PASSWORD:-changeme}
```

## Astro 5 CSRF trap

Even with the GET-based form workaround, **client-side fetch POST requests** (e.g. `fetch('/api/quest/complete', { method: 'POST' })`) can fail with `Cross-site POST form submissions are forbidden`.

There are two fixes:

### Fix A: `checkOrigin: false` in Astro config (preferred)

In `astro.config.mjs`:
```js
security: {
  checkOrigin: false
}
```

This disables the origin check entirely. Use this when all routes are behind authentication or when you control the client origin. DOMINATES `csrf: false` — the property is `checkOrigin`, not `csrf`.

### Fix B: Public API routes in middleware

Put `/api` in the middleware's `PUBLIC_ROUTES` array and proxy API calls to a separate backend (Hono, Express, etc.) that doesn't have CSRF checks:

```ts
const PUBLIC_ROUTES = ['/login', '/_astro', '/api'];
```

Then in the middleware, proxy API requests manually:
```ts
if (url.pathname.startsWith('/api/')) {
  return fetch(`http://localhost:3001${url.pathname}${url.search}`, {
    method: context.request.method,
    headers: context.request.headers,
    body: ['GET', 'HEAD'].includes(context.request.method) ? undefined : await context.request.text(),
  });
}
```

## Testing

```bash
# Login
curl -c /tmp/cookies "http://127.0.0.1:4321/login?password=yourpass"

# Access protected page
curl -b /tmp/cookies "http://127.0.0.1:4321/"

# Test API endpoint (if proxy used)
curl -s -X POST "http://127.0.0.1:4321/api/quest/1/complete"
```

## Pitfalls

- **`checkOrigin: false` in `astro.config.mjs` (NOT `csrf: false`)** — Astro v5 uses `security.checkOrigin` for CSRF enforcement. Setting `security.csrf` has no effect.
- **Cookie path matters** — cookie must be set with `path: '/'` to work across all routes.
- **GET form submits query params** — the browser sends password as a URL parameter. Visible in logs. Fine for a personal dashboard; add HTTPS if this is a concern.
- **Middleware ordering** — the API proxy must come before the auth check in middleware to avoid auth redirect on API calls.
- **POST without body triggers CSRF check** — Astro's CSRF protection fires on any POST request, even those without a Content-Type header. `checkOrigin: false` disables this globally.
