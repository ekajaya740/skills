# Resource Organization Per Project

Standalone reference rows (Notes with Type=Reference) are organized by **topic relevance to
active projects**, not by generic categories.

## Rules

1. **Project-specific** -> a Notes row with a `Project` relation
2. **Area-specific** -> a Notes row with an `Area` relation
3. **Global (no specific project)** -> a standalone Notes row (Type=Reference) with no relation
4. **Outdated / not relevant to any active project** -> an **Archive** row

## Current distribution

| Destination | Topics |
|---|---|
| Notes rows related to the PT-SUM-Digital-Konsultan area | Git/GitHub, Java/Spring, Web Dev/Frontend, Backend/API, DevOps/Docker |
| Notes rows related to the Profill-Link-Monorepo-Web project | Git/GitHub, Node.js, Web Dev/Frontend, Backend/API, DevOps/Docker, Cloudflare, Supabase |
| Standalone Notes rows | Fitness, Finance, AI, lifestyle, language, music, books, health, guitar, stocks, productivity |
| Archive rows | Everything else (old frameworks, unused languages, outdated tutorials) |

## How to decide

1. Does this relate to an active project/area? -> set the `Project`/`Area` relation
2. Is it about Fitness, Finance, AI, lifestyle, language, music, health or general knowledge? ->
   keep it standalone
3. Is it about a technology/tool not used by any active project? -> create an Archive row

## Naming

Area and project names use **hyphens between words** in TitleCase: `PT-SUM-Digital-Konsultan`.
Never change to spaces unless the user explicitly asks, and never rename a row without updating
the relations that point at it.
