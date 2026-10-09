# Foreign overwrite forensics: React DCE error + asset re-upload skip (2026-08-21)

Follow-up to `worker-ops-and-forensics.md` — a second foreign-overwrite
incident on the `investment` worker, this time diagnosed from the CLIENT side
(React error + broken Tailwind) instead of the server side.

## Symptom: React DCE error + Tailwind not loading

User reported in the browser console:
`Uncaught Error: React is running in production mode, but dead code elimination
has not been applied` (at `installHook.js` — React DevTools' DCE check) plus
"seems the tailwind is not loaded properly too".

**Root cause was NOT the repo build.** The live worker had been clobbered by a
foreign deployment (server-rendered app, nav Companies/People/Indices,
`/assets/client.js` 1.1MB **unminified**). An unminified React development
bundle served as production triggers the DCE error; the foreign HTML also
referenced inconsistent CSS (`/app.css` vs `/app.574e0db9ec.css`) → broken
Tailwind.

## Diagnosis order (client-side forensics)

1. **Check the repo build first** — grep the local bundle for DCE markers:
   `grep -c 'perf-use-production-build' dist/client/assets/index-*.js` → 0 in
   a healthy production build. Also `grep -c '\^\^_\^\^'` (React's DCE marker).
   If the local build is clean, the problem is what's SERVED, not what's built.
2. **Compare served HTML to repo build**: `curl -s URL` and look for the
   hashed asset names from `dist/client/index.html`. Foreign HTML references
   different assets entirely.
3. **Check `wrangler deployments list`** for a deployment created AFTER yours
   (timestamps). A foreign deploy ~1-2 min after your own is the smoking gun.
4. **Check `cf-cache-status`**: `curl -s -D - URL` — a `HIT` on the HTML means
   edge cache may still serve the foreign page even after you redeploy.

## Fix: force asset re-upload after a clobber

After a foreign deploy replaced the worker, `wrangler deploy` printed
"4 already uploaded" and did NOT re-upload the assets — the remote manifest
still pointed at the foreign build's assets, so the SPA was broken even though
the worker code was ours.

Fix: touch a marker file in the assets dir, deploy (forces a new manifest),
verify, then remove the marker and deploy again:

```bash
echo "reupload-marker $(date +%s)" > dist/client/force-upload.txt
bun x wrangler deploy   # now uploads all assets
rm dist/client/force-upload.txt
bun run build:client && bun x wrangler deploy   # clean final state
```

Verify with `curl -s "URL/?t=$(date +%s%N)"` (cache-busting query) and grep the
hashed asset names from the local build.

## Edge-cache nuance

After redeploy, `curl URL` may still show the foreign HTML with
`cf-cache-status: HIT` — that is edge cache, not a live foreign deploy. Use a
cache-busting query string (`?t=<nanotime>`) to bypass. If the fresh fetch
shows your build, you're done; if it still shows foreign markers, check
`deployments list` again (a newer foreign deploy may be active).
