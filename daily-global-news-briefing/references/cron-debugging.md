# Cron Debugging: Daily Global News Briefing

Session: 2026-05-14

## Error 1: No LLM Provider Configured

**Symptom:** Cron job fails with:
```
RuntimeError: No LLM provider configured.
Run `hermes model` to select a provider, or run `hermes setup` for first-time configuration.
```

**Cause:** Cron runs in an isolated subprocess. It does NOT inherit the current interactive session's model/provider selection. The `~/.hermes/.env` file must contain the API key permanently.

**Fix:** Ensure `~/.hermes/.env` contains:
```bash
OLLAMA_API_KEY=sk-...
OLLAMA_BASE_URL=https://ollama.com/v1   # optional
```

Verify with:
```bash
grep OLLAMA ~/.hermes/.env
```

---

## Error 2: Model hallucinated `web_searc`

**Symptom:** Cron output shows:
```
RuntimeError: Model generated invalid tool call: web_searc
```

**Cause:** The cron prompt told the agent to "fetch news via RSS" but didn't specify *how*. The model, wanting to search the web, hallucinated a `web_search` tool call. The cron had `enabled_toolsets: ["web", "terminal"]` which includes `execute_code`, but the prompt never instructed the agent to *use* `execute_code`.

**Secondary cause:** The `daily-global-news-briefing` skill originally documented `enabled_toolsets: ["web"]` which does NOT include `execute_code`. Even after adding `"terminal"`, the prompt didn't explicitly tell the model to use it.

**Fix:** The cron prompt must explicitly say:
```
You are a news briefing agent. Use execute_code with Python requests
 to fetch BBC World, BBC Business, and BBC Technology RSS feeds.
Parse the XML, pick top stories per category...
```

This removes ambiguity. The model knows exactly which tool to call.

---

## Tool Mapping Discovery: `"web"` ≠ `execute_code`

The `"web"` toolset name is misleading. In Hermes, toolsets are named groups, not capability descriptions. `"web"` does NOT provide:
- `execute_code`
- `browser_navigate`
- `web_search`

What `"web"` actually provides depends on the Hermes version. In practice, the agent needs `"terminal"` to run Python code that fetches RSS feeds.

**Working cron toolsets for this briefing:**
```json
"enabled_toolsets": ["terminal"]
```

Adding `"file"` is useful if the skill reads local reference files. `"web"` is optional if all fetching is done via `execute_code` + Python `requests`.

---

## Working Cron Configuration (Verified 2026-05-14)

```json
{
  "name": "Daily Global News Briefing",
  "schedule": "0 1 * * *",
  "skills": ["daily-global-news-briefing"],
  "enabled_toolsets": ["web", "terminal"],
  "prompt": "[IMPORTANT: You are running as a scheduled cron job. DELIVERY: Your final response will be automatically delivered to the user — do NOT use send_message. Just produce your report/output as your final response and the system handles the rest. SILENT: If there is genuinely nothing new to report, respond with exactly \"[SILENT]\".]\n\nYou are a news briefing agent. Your task is to compile a daily global news briefing.\n\nUse execute_code with Python requests to fetch BBC World, BBC Business, and BBC Technology RSS feeds. Parse the XML, pick top stories per category (Geopolitics, Business, Tech), format with bracket citations [1] [2] etc., and add a References glossary at the bottom. Return the formatted markdown.",
  "deliver": "origin"
}
```

---

## Symlink Pattern for Personal Skills

When a skill lives in `~/.hermes/skills/` but you also want it discoverable by cron or the hermes-agent repo tree, create a symlink:

```bash
ln -s ~/.hermes/skills/research/daily-global-news-briefing \
  ~/.hermes/hermes-agent/skills/research/daily-global-news-briefing
```

This lets you:
- Edit the source in ONE place (`~/.hermes/skills/`)
- Have it available to the hermes-agent runtime that scans `hermes-agent/skills/`
- Avoid committing it to the hermes-agent repo (which the user may not want)

---

## RSS Feed Status (2026-05-14 Session)

| Source | Method | Status |
|---|---|---|
| BBC World | Direct RSS XML | ✅ Working |
| BBC Business | Direct RSS XML | ✅ Working |
| BBC Technology | Direct RSS XML | ✅ Working |
| Reuters | `r.jina.ai` | ❌ Rate-limited (SecurityCompromiseError) |
| TechCrunch | `r.jina.ai` | ❌ Rate-limited |
| AP News | `r.jina.ai` | ❌ Rate-limited |
| The Guardian | `r.jina.ai` | ❌ Timeout |

**Lesson:** Prefer direct RSS fetching with Python `requests` + `xml.etree.ElementTree` over `r.jina.ai` proxy. Jina AI blocks major news domains due to suspected DDoS abuse.
