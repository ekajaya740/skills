---
name: daily-global-news-briefing
description: "Use when compiling or automating a multi-source daily global news briefing. Aggregates geopolitical, economic, and tech news via RSS feeds and web sources, synthesizes a concise report, and delivers it through cron or on-demand execution."
version: 1.1.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [news, briefing, rss, aggregation, cron, research, monitoring]
    related_skills: [blogwatcher, writing-plans]
---

# Daily Global News Briefing

## Overview

Compile a concise, structured daily global news briefing by aggregating headlines and stories across **six categories**: **Geopolitics**, **Business & Economy**, **Technology & Science**, **Indonesia 🇮🇩**, **China 🇨🇳**, and **Israel 🇮🇱**. The skill supports both automated cron scheduling and on-demand manual execution.

This skill favors **RSS feeds** for reliability over scraping, uses multiple independent news sources, and gracefully degrades if LLM synthesis is unavailable — always producing at minimum a headlined bullet summary.

## When to Use

- User asks for a daily news briefing ("what's happening in the world today","run my briefing","global news round-up")
- Setting up a recurring cron job to deliver a daily briefing
- The scheduled daily briefing failed and you need to manually produce one
- User wants to customize the source list, categories, or format of their briefing
- You need to debug why a scheduled briefing job produced an error or `[SILENT]`

## When NOT to Use

- User asks about a single specific niche topic — use `blogwatcher` or direct search instead
- This is not a financial-market-intelligence skill (no price feeds, technical analysis, or portfolio data)
- Not a translation skill — if user wants non-English headlines, fetch those sources explicitly

## Source Configuration

### Default RSS Feed Sources

| Source | URL | Category Focus | Reliability |
|---|---|---|---|
| BBC World | `https://feeds.bbci.co.uk/news/world/rss.xml` | World / Politics | High |
| BBC Business | `https://feeds.bbci.co.uk/news/business/rss.xml` | Economy / Markets | High |
| BBC Technology | `https://feeds.bbci.co.uk/news/technology/rss.xml` | Tech / Science | High |
| BBC US/Canada | `https://feeds.bbci.co.uk/news/us_and_canada/rss.xml` | US Policy | Medium |
| Reuters World | `https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best` | Markets | Medium (rate-limited) |
| CNBC World | `https://www.cnbc.com/id/100727362/device/rss/rss.html` | Business | Medium |

### Regional RSS Feed Sources

| Region | Source | URL | Reliability |
|---|---|---|---|
| **Indonesia** | CNN Indonesia | `https://www.cnnindonesia.com/nasional/rss` | Medium |
| **Indonesia** | Jakarta Post | `https://www.thejakartapost.com/feed/` | Medium |
| **China** | South China Morning Post (SCMP) | `https://www.scmp.com/rss/91/feed` | High |
| **China** | Global Times | `https://www.globaltimes.cn/rss/out.xml` | Medium |
| **Israel** | Times of Israel | `https://www.timesofisrael.com/feed/` | High |
| **Israel** | Jerusalem Post | `https://www.jpost.com/Rss/RssFeedsHeadlines.aspx` | Medium |

See `references/rss-feed-config.md` for troubleshooting blocked feeds, rate-limit handling, and how to add custom sources.

### Web Scraping Fallback

If RSS is unavailable or thin, use `r.jina.ai/http://<url>` to get plain-text markdown extraction:

```python
import requests
url = f"https://r.jina.ai/http://www.bbc.com/news"
text = requests.get(url, timeout=30).text[:4000]
```

⚠️ `r.jina.ai` rate-limits; do not make more than ~5 requests per minute. If blocked, wait 60s or switch to another source. Full rate-limit guidance is in `references/rss-feed-config.md`.

## Workflow

### Phase 1: Fetch

1. Fetch 3–5 global RSS feeds in parallel (world, business, tech sources)
2. Fetch 1–2 regional RSS feeds for **Indonesia**, **China**, and **Israel**
3. Parse each feed extracting top 3–5 stories
4. Gather a small pool of candidate headlines (~18–22 stories)

### Phase 2: Curate

1. **If LLM available:** Feed candidate headlines to the model with a structured prompt asking it to pick the 2–3 most significant stories per category and write 1-sentence headlines + 1–2 sentence summaries. **Prioritize region-specific stories** for Indonesia, China, and Israel sections.
2. **If LLM unavailable / cron lacks provider:** Pick the top 2–3 most significant yourself using judgment (breaking leaders, market movers, tech regulatory or security events, and major regional developments)

### Phase 3: Format

Produce a clean markdown report with this structure. Use **numbered citations** `[1]`, `[2]`, etc. inline after each headline, and collect all URLs in a **References** glossary at the bottom.

```markdown
## Geopolitics 🌍

**• [One-sentence headline]** [1]
1–2 sentences of key context / impact.

**• [One-sentence headline]** [2]
1–2 sentences of key context / impact.

## Business & Economy 💰

**• [One-sentence headline]** [3]
1–2 sentences of key context / impact.

## Tech & Science 🔬

**• [One-sentence headline]** [4]
1–2 sentences of key context / impact.

## Indonesia 🇮🇩

**• [One-sentence headline]** [5]
1–2 sentences of key context / impact.

## China 🇨🇳

**• [One-sentence headline]** [6]
1–2 sentences of key context / impact.

## Israel 🇮🇱

**• [One-sentence headline]** [7]
1–2 sentences of key context / impact.

## Big Picture

2–3 sentences synthesizing how the top stories connect or what to watch next.

---

## References

[1] https://www.bbc.com/news/articles/...
[2] https://www.reuters.com/world/...
[3] https://www.bbc.com/business/...
[4] https://www.bbc.com/technology/...
[5] https://www.cnnindonesia.com/...
[6] https://www.scmp.com/...
[7] https://www.timesofisrael.com/...

*Sources: BBC, Reuters, CNBC, CNN Indonesia, SCMP, Times of Israel | Compiled: 2026-05-14 11:00 UTC*
```

**Citation rules:**
- Number sequentially in order of first appearance (not by category)
- Each headline gets exactly one citation pointing to its canonical URL
- If two headlines share the same source article, reuse the same `[N]` number
- Never embed bare URLs inline — always use the `[N]` shorthand

See `references/citation-format.md` for the canonical template.

### Phase 4: Deliver

- **On-demand:** Return the markdown as your final response
- **Cron job:** Return the markdown as your final response (delivery is handled automatically — do NOT use `send_message`)
- If genuinely no news found, respond with exactly `[SILENT]` to suppress delivery

## Automated Cron Setup

### Creating the Job

```bash
hermes cron create --name "Daily Global News Briefing" \
  --schedule "0 1 * * *" \
  --toolsets terminal,file \
  --prompt "You are a news briefing agent. Use execute_code with Python requests to fetch BBC World, BBC Business, BBC Technology RSS feeds PLUS regional feeds: CNN Indonesia (https://www.cnnindonesia.com/nasional/rss), South China Morning Post (https://www.scmp.com/rss/91/feed), and Times of Israel (https://www.timesofisrael.com/feed/). Parse the XML, pick top stories per category (Geopolitics, Business, Tech, Indonesia, China, Israel), format with bracket citations [1] [2] etc., add a References glossary, and return formatted markdown."
```

Alternatively, use `cronjob(action='create', ...)` from the agent.

### Critical Requirements for Cron Success

Cron jobs run in **isolated environments** with no chat context.

1. **Toolsets must be explicitly enabled.** The cron job MUST declare `enabled_toolsets=["terminal", "file"]` (or whichever sets are needed). Without `"terminal"`, the agent has no `execute_code` tool and cannot fetch RSS feeds. Without `"file"`, reading local reference files fails. The old `"web"` toolset alone does **not** provide `execute_code`.
2. **The cron prompt must be self-contained.** Do NOT reference past conversations or "the plan from earlier". Include the full instructions inside the cron `prompt` field.
3. **Skills are loaded automatically if referenced.** Setting `skills=["daily-global-news-briefing"]` pre-loads the skill. Otherwise, the skill may not be available in the isolated cron session.
4. **LLM provider must be configured in the cron environment.** The error `RuntimeError: No LLM provider configured` means the cron environment lacks `OLLAMA_API_KEY`, `OPENAI_API_KEY`, or whichever provider is used. Set these in `~/.hermes/.env` so the cron inherits them.

Example cron create with all safeguards:

```json
{
  "action": "create",
  "name": "Daily Global News Briefing",
  "schedule": "0 1 * * *",
  "skills": ["daily-global-news-briefing"],
  "enabled_toolsets": ["terminal", "file"],
  "prompt": "[IMPORTANT: You are running as a scheduled cron job. DELIVERY: Your final response will be automatically delivered to the user — do NOT use send_message. Just produce your report/output as your final response and the system handles the rest. SILENT: If there is genuinely nothing new to report, respond with exactly \"[SILENT]\".]\n\nYou are a news briefing agent. Use execute_code with Python requests to fetch:\n- BBC World (https://feeds.bbci.co.uk/news/world/rss.xml)\n- BBC Business (https://feeds.bbci.co.uk/news/business/rss.xml)\n- BBC Technology (https://feeds.bbci.co.uk/news/technology/rss.xml)\n- CNN Indonesia (https://www.cnnindonesia.com/nasional/rss)\n- South China Morning Post (https://www.scmp.com/rss/91/feed)\n- Times of Israel (https://www.timesofisrael.com/feed/)\n\nParse the XML, pick top stories per category (Geopolitics, Business & Economy, Tech & Science, Indonesia, China, Israel), format with bracket citations [1] [2] etc., add a References glossary at the bottom, and return the formatted markdown.",
  "deliver": "origin"
}
```

### Checking / Debugging Cron

- See all jobs: `cronjob(action='list')`
- Check last run status and error: look at `last_status` and `last_delivery_error` fields
- Find historical outputs: `~/.hermes/cron/output/<job_id>/`
- Run on demand: `cronjob(action='run', job_id=<id>)`

For step-by-step debugging of the two most common cron failures, see `references/cron-debugging.md`.

## One-Shot Recipes

### Recipe A: On-Demand Manual Briefing

When user says "run my daily briefing now" and the cron failed:

1. Check `cronjob(action='list')` for the briefing job
2. If it exists and state is `error`/`failed`, note the reason from `last_status`
3. **Fast path:** Run the bundled script to fetch headlines:
   ```bash
   python ~/.hermes/skills/research/daily-global-news-briefing/scripts/fetch_briefing.py
   ```
4. **Full path:** If LLM is available, use the script output as candidate headlines, then ask the LLM to curate and write summaries per category
5. Return the formatted markdown as your final response

If the script is unavailable, fall back to manual Python `requests` + `xml.etree.ElementTree` against the verified feed URLs.

### Recipe B: Setting Up a New Cron Briefing

1. Verify `~/.hermes/.env` contains the required LLM provider key
2. Build the cron prompt using the template above (self-contained, includes skill reference)
3. `cronjob(action='create', ...)` with `skills=["daily-global-news-briefing"]` and `enabled_toolsets=["terminal", "file"]`
4. Run it once manually: `cronjob(action='run', job_id=<new_id>)`
5. Check `~/.hermes/cron/output/<job_id>/` for the output file

### Recipe C: Graceful Degradation (LLM Unavailable)

If thecron or manual run lacks an LLM:

1. Fetch the RSS feeds with Python
2. Print the top 3 headlines per category verbatim (title + source + link)
3. Wrap in the standard markdown structure
4. Add a note: `*(Briefing generated in headline-only mode due to unavailable LLM)*`
5. Deliver the output — still valuable to the user

## References

- **`references/session-tested-sources.md`** — Verified working RSS feeds, known rate-limited sources, and tested fetch code from 2026-05-14 session.
- **`references/cron-debugging.md`** — Step-by-step debugging guide for the two most common cron failures (`No LLM provider configured`, `invalid tool call: web_searc`), verified toolset mapping, and a working production cron JSON template.

## Common Pitfalls

1. **RSS feed changes or goes offline.** Always wrap feed fetches in `try/except`. Silently skip a dead source rather than aborting the entire briefing. Re-run the verification checklist after any source rotation.
2. **`r.jina.ai` rate limits.** If you get `SecurityCompromiseError` or `Too many requests`, switch to direct RSS or wait 60 seconds before retrying. In practice, Reuters, AP News, TechCrunch, and The Guardian are all blocked by `r.jina.ai` rate limits — direct RSS is strictly preferred.
3. **Cron job fails with "No LLM provider configured."** The cron environment does not inherit your current session's provider state. The exact error is:
   ```
   RuntimeError: No LLM provider configured. Run `hermes model` to select a provider, or run `hermes setup` for first-time configuration.
   ```
   Ensure `~/.hermes/.env` sets the key permanently (e.g. `OLLAMA_API_KEY=sk-...`).
4. **Cron job uses `skills` field incorrectly.** The correct key is `skills: ["daily-global-news-briefing"]` (string list). It pre-loads the skill into the cron session. It is separate from `enabled_toolsets`.
5. **Using `send_message` inside a cron job.** This causes delivery duplication or errors. Cron output is auto-delivered — just return the text.
6. **Not declaring `enabled_toolsets`.** Without `enabled_toolsets=["terminal", "file"]`, the cron agent has no `execute_code` tool and cannot fetch RSS feeds. This is the most common reason a cron briefing produces zero output. The `"web"` toolset alone does **not** include `execute_code`.
7. **Forgetting source attribution.** Every story should cite its source (BBC, Reuters, CNBC, etc.). Build trust and allow the user to verify.
8. **Over-reliance on a single source.** Use at least two independent sources per category to avoid blind spots. If the BBC World feed is down, CNBC World RSS or direct Reuters RSS are fallbacks.
9. **Regional feeds returning non-English content.** CNN Indonesia and Global Times may return Indonesian or Chinese headlines. If the user expects English, prioritize SCMP and Times of Israel for China/Israel coverage, and Jakarta Post for Indonesia. If the user wants native-language headlines, include the local feeds directly.

## Verification Checklist

- [ ] `enabled_toolsets` includes `"terminal"` and `"file"` when creating the cron job
- [ ] Cron prompt is fully self-contained (no references to prior context)
- [ ] At least 2 independent sources per category are configured
- [ ] Regional feeds for Indonesia, China, and Israel are included in fetch list
- [ ] LLM provider key is persistently set in `~/.hermes/.env`
- [ ] RSS fetch code has `try/except` per feed
- [ ] Every story cites its source
- [ ] Big Picture synthesis section is present in output
- [ ] When run as cron, no `send_message` is used
- [ ] `[SILENT]` is used only when there is genuinely nothing to report
- [ ] Historical cron outputs verified at `~/.hermes/cron/output/<job_id>/`
