# MCP Tool Response Formatting Patterns

Conventions for formatting `TextContent` responses in custom MCP servers so they render well across Telegram, Discord, and CLI.

## General Rules

- Keep responses under 2000 characters when possible (Discord limit is 2000, Telegram is 4096).
- Use line breaks liberally. Dense JSON blobs are hard to read.
- Use emoji headers for visual scanning: `🏹`, `⚔️`, `📊`, `🎉`.
- Avoid markdown tables — Telegram auto-rewrites them into bullet lists anyway. Use labeled lines or bullet lists.

## Patterns by Tool Type

### Status / Dashboard Tool
```
🏹 Hunter Status
Rank: S
Mana: 4200
Shadow Army: 87
Current Streak: 12 days
Best Streak: 45 days
Next Rank: MAX
```

### List Tool
```
⚔️ Active Quests:
[1] Morning Run (fitness) — Difficulty: 3 — Cleared today: 1
[2] Code Review (work) — Difficulty: 2 — Cleared today: 0
[3] Read 20 Pages (general) — Difficulty: 1 — Cleared today: 1
```

### Action / Completion Tool
```
⚡ Dungeon Cleared! +30 mana
🎉 RANK UP! You are now Rank D!
```

### Empty State
```
No active quests. Use create_quest to add one.
```

### Error State
```
Quest 42 not found.
```

## Anti-patterns

- ❌ Raw JSON dumps: `{"id":1,"name":"run"}`
- ❌ Dense single-line output: `Quest 1: run (fitness) Difficulty 3 Cleared 1`
- ❌ Over-explaining: `The operation was successful and the database has been updated...`
