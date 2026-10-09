# Oh My Pi (omp) — Reference

## Overview

Oh My Pi (omp) is a coding agent CLI — fork of Pi by Mario Zechner, with a Rust core. 40+ providers, 32 built-in tools, LSP (14 ops), DAP (28 ops), browser automation, subagent spawning.

- GitHub: https://github.com/can1357/oh-my-pi
- Docs: https://omp.sh
- Install: `curl -fsSL https://omp.sh/install | sh` or `bun install -g @oh-my-pi/pi-coding-agent`

## Config Structure

All config lives under `~/.omp/agent/` (or `$PI_CODING_AGENT_DIR`):

| File | Purpose |
|------|---------|
| `config.yml` | Model roles, display, compaction, providers, extensions |
| `models.yml` | Provider definitions (baseUrl, api format, model list) |
| `mcp.json` | MCP server connections |
| `agent.db` | SQLite session store (auto-created) |

### config.yml key fields

```yaml
Models:
  - deepseek/*
  - ollama-cloud/*
modelRoles:
  default: ollama-cloud/deepseek-v4-flash
  smol: ollama-cloud/deepseek-v4-flash
  plan: ollama-cloud/kimi-k2.6:cloud
  commit: ollama-cloud/deepseek-v4-flash
  slow: ollama-cloud/deepseek-v4-pro
  designer: ollama-cloud/minimax-m3:cloud
  vision: ollama-cloud/gemma4:31b-cloud
  task: ollama-cloud/deepseek-v4-flash
defaultThinkingLevel: medium
steeringMode: one-at-a-time
followUpMode: auto
interruptMode: immediate
compaction:
  enabled: true
  reserveTokens: 16384
  keepRecentTokens: 20000
retry:
  networkOnly: true
  maxRetries: 3
  baseDelayMs: 2000
providers:
  webSearch: auto
```

### models.yml key fields

Each provider entry:
```yaml
providers:
  provider-name:
    baseUrl: https://api.example.com/v1
    api: openai-completions       # or anthropic-messages, etc.
    apiKey: ***                   # read from env var by convention
    authHeader: true              # send as Bearer token
    models:
      - id: model-id
        name: Human Name
        reasoning: true
        thinking:
          minLevel: high
          maxLevel: xhigh
          mode: effort
        input: [text, image]
        contextWindow: 1000000
        maxTokens: 65536
        compat:
          supportsDeveloperRole: false
          supportsReasoningEffort: true
          maxTokensField: max_tokens
          reasoningEffortMap:
            high: high
            xhigh: max
          supportsToolChoice: false
          requiresReasoningContentForToolCalls: true
          requiresAssistantContentForToolCalls: true
          extraBody:
            thinking:
              type: enabled
```

## Auth

omp reads API keys from environment variables. Convention: uppercase provider name, hyphens → underscores, suffix `_API_KEY`.

| Provider name in models.yml | Env var |
|----------------------------|---------|
| `ollama-cloud` | `OLLAMA_CLOUD_API_KEY` |
| `deepseek` | `DEEPSEEK_API_KEY` |
| `openrouter` | `OPENROUTER_API_KEY` |
| `anthropic` | `ANTHROPIC_API_KEY` |

Also supports:
- `--api-key <key>` flag (inline override)
- `omp auth-broker` for credential vault (serve/token/login/logout/import/migrate)
- `omp token <provider>` to check what key omp is reading

## Key CLI Flags

| Flag | Description |
|------|-------------|
| `-p "prompt"` | One-shot: run prompt and exit |
| `--model provider/model` | Pick provider/model (fuzzy match) |
| `--smol` / `--slow` / `--plan` | Model presets |
| `--api-key <key>` | API key override |
| `--resume` | Resume a past session |
| `--profile <name>` | Isolated profile |
| `--thinking <level>` | off/minimal/low/medium/high/xhigh/auto |
| `--auto-approve` | Skip all approval prompts |
| `--config <file>` | Load extra config overlay (repeatable) |
| `--allow-home` | Allow starting in ~ without temp dir |
| `--cwd <path>` | Working directory |
| `--no-tools` | Disable all built-in tools |
| `--no-lsp` | Disable LSP tools |
| `--no-pty` | Disable PTY-based bash |
| `--tools <list>` | Comma-separated tool allowlist |
| `--mode text\|json\|rpc\|rpc-ui` | Output mode |
| `--max-time <seconds>` | Stop session after N seconds |

## Available Tools (default-enabled)

read, bash, edit, write, grep, glob, lsp, python (requires `omp setup python`), notebook, inspect_image, browser, task (subagents), todo, web_search, ask

## Hermes Orchestration

### One-shot
```bash
terminal(command="omp -p 'prompt'", workdir="~/project", pty=true)
```

### Background interactive
```bash
terminal(command="omp", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="follow-up prompt")
```

### With API key from file (avoids terminal redaction)
```bash
terminal(command="KEY=$(cat /tmp/keyfile) && omp -p 'prompt' --api-key \"$KEY\"", workdir="~/project", pty=true)
```

## Pitfalls

1. **Terminal tool redacts `***` patterns** — API keys containing `***` or matching the redaction pattern get replaced before reaching the shell. Workaround: write the key to a file and use `$(cat /path/to/keyfile)` to inject it.

2. **Config must be at `~/.omp/agent/`** — omp reads from `$PI_CODING_AGENT_DIR` (default `~/.omp/agent`). Place `config.yml`, `models.yml`, `mcp.json` there.

3. **Git repo required** — omp refuses to run outside a git repo.

4. **Always use `pty=true`** for interactive sessions.

5. **Provider auth mismatch** — if a provider works via curl but omp returns 401, check:
   - The env var name matches omp's convention (uppercase, hyphens→underscores, `_API_KEY` suffix)
   - The `baseUrl` in models.yml is correct
   - The model ID format matches what the provider expects
   - Use `omp token <provider>` to verify omp is reading the right key

6. **`omp auth-broker migrate --from-local --include-env`** requires `OMP_AUTH_BROKER_URL` to be set — it uploads to a remote broker, not local. For local-only auth, just set env vars.

## Commands

| Command | Description |
|---------|-------------|
| `omp` | Interactive mode |
| `omp -p "prompt"` | One-shot non-interactive |
| `omp --continue` | Continue previous session |
| `omp --resume <id>` | Resume specific session |
| `omp config list\|get\|set\|reset\|path\|init-xdg` | Config management |
| `omp token <provider>` | Show API key for provider |
| `omp auth-broker serve` | Start credential vault |
| `omp auth-broker import <path>` | Import credentials |
| `omp auth-broker migrate --from-local --include-env` | Migrate env vars to broker |
| `omp models` | List/search/refresh models |
| `omp setup` | Run onboarding setup |
| `omp update` | Check for updates |
| `omp agents unpack` | Export bundled subagents |
| `omp commit` | Generate commit message |
| `omp worktree` | List/clear agent-managed worktrees |
| `omp acp` | Run as ACP server over stdio |
