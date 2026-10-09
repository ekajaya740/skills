---
name: youtube-playlist-management
description: "Reorder or list YouTube playlists via the Data API v3."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [youtube, playlists, api, oauth]
---

# YouTube Playlist Management (Data API v3)

List, reorder, and move items in the user's YouTube playlists via the official API. Uses a **dedicated YouTube-only OAuth token** stored separately from the Gmail/Drive GWS token.

## When to Use

- User asks to reorder / rearrange a YouTube playlist
- User asks to move a video to a different position
- User wants a playlist listing (items + positions)
- Any YouTube Data API work (the auth pattern applies generally)

## Auth Setup (the critical part)

**Google refuses to combine `youtube.force-ssl` with `drive.file` in one consent screen** — `Error 400: invalid_request, "This request contains scopes that cannot be requested together"`. This bit us when trying to re-auth the full GWS scope set with YouTube added.

**Working pattern: separate YouTube-only token file.**

1. OAuth flow for ONLY `https://www.googleapis.com/auth/youtube.force-ssl` (access_type=offline, prompt=consent), redirect_uri `http://localhost:18080`.
2. Save result to `~/.hermes/gws/youtube_token.json` (format: `token`, `refresh_token`, `token_uri`, `client_id`, `client_secret`, `scopes`, `type: authorized_user`) — do NOT overwrite the main `token_cache.json` / `credentials.json`.
3. On the VPS: run a background callback server (`python3 /tmp/gws_oauth_yt.py` style) to print `AUTH_URL:`, send the link to the user, and have them paste back the redirect URL. **Gotcha:** when the user opens the link on THEIR machine, the callback hits THEIR localhost, not the VPS's — so exchange the code manually with a direct POST to `https://oauth2.googleapis.com/token` using the pasted `code=` parameter. The code is single-use and valid for a short window.
4. Verify: refresh-token POST → call `youtube/v3/playlists?part=snippet&mine=true` → should list the user's playlists (their channel has ~19 playlists: アニメ, ギター, 料理, Manga, Programming, etc.).

## Helper Script

`scripts/yt_playlist.py` — auto-refreshes the token and supports:

```bash
python3 ~/.hermes/scripts/yt_playlist.py list PLAYLIST_ID
python3 ~/.hermes/scripts/yt_playlist.py reorder PLAYLIST_ID videoId1,videoId2,...   # full reorder
python3 ~/.hermes/scripts/yt_playlist.py move PLAYLIST_ID VIDEO_ID NEW_POSITION
```

- `list` verified live (2026-08-10): returns position | videoId | title.
- `reorder` requires the exact same set of videoIds (sanity-checks before mutating).

## Reorder Technique

The API has **no atomic reorder**. Use `playlistItems.update` (part=snippet) with `snippet.position`. To avoid position drift (moving item A shifts item B's index), process moves **from the end of the desired order toward the front** (reverse iteration). Sleep ~0.3s between writes to be gentle on rate limits.

Quota: each `playlistItems.update` costs 50 units; default daily quota is 10,000 units — a 113-video playlist ≈ 5,650 units, fine within a day but not something to re-run repeatedly.

## Pitfalls

- **System playlists**: `WL` (Watch Later) works via `playlistItems?playlistId=WL` even though `relatedPlaylists` never lists it; `LL` (Liked) caps at 5,000 items; `FV`/`SV`/`SP` are dead (400). Full table + account-mismatch diagnosis in `references/system-playlists-and-account-probing.md`.
- **"Watch Later is full" ≠ API is wrong**: user devices are often signed into a different Google account than the token. Verify `WL`/`LL` totals and identify the token's channel before planning a sort.
- **Scope conflict**: never put `youtube.force-ssl` in the same consent request as `drive.file` — Google rejects the whole request. Separate token file is the fix.
- **Callback server on VPS ≠ user's browser**: the OAuth redirect goes to whatever machine the user's browser is on. Always be ready to exchange the pasted code directly instead of relying on the local callback.
- **Token file must be git-ignored** — it's under `~/.hermes/gws/` which is already ignored (never commit secrets).
- **Write scopes are irreversible-ish**: reordering a playlist is a real mutation — always `list` first and show the user the current order, confirm the target order, then apply.

## Verification

After any auth setup, prove it works before claiming success: refresh the token, call `playlists?mine=true`, and print the count. A `PLAYLISTS: N` listing is the green light.
