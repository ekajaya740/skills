---
name: coding-agents
description: "Delegate coding tasks to AI coding agent CLIs: Claude Code, Codex, or OpenCode — orchestrate via Hermes terminal/process tools."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Autonomous, Code-Review, Refactoring, PTY]
    related_skills: [hermes-agent, subagent-driven-development, github-workflow]
---

# AI Coding Agents

Delegate coding tasks to autonomous AI coding agent CLIs — Claude Code, OpenAI Codex, or OpenCode — orchestrated through Hermes terminal and process tools. All three agents can read files, write code, run commands, and manage git workflows autonomously.

Choose the agent based on availability and task:

| Agent | Install | Best for | Auth |
|-------|---------|----------|------|
| **Claude Code** | `npm install -g @anthropic-ai/claude-code` | Complex multi-file refactors, PR reviews, subagent orchestration | Anthropic API key or `hermes login --provider anthropic` |
| **Codex** | `npm install -g @openai/codex` | One-shot feature building, batch issue fixing, parallel worktree tasks | `OPENAI_API_KEY` or Codex OAuth (`~/.codex/auth.json`) |
| **OpenCode** | `npm i -g opencode-ai@latest` | Provider-agnostic coding, iterative sessions, PRs on any model | `opencode auth login` or provider env vars |
| **Oh My Pi (omp)** | `curl -fsSL https://omp.sh/install \| sh` or `bun install -g @oh-my-pi/pi-coding-agent` | Provider-agnostic, 40+ providers, LSP/DAP, subagents, browser | Provider-specific env vars (e.g. `OLLAMA_CLOUD_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`) or `--api-key` flag |

---

## Shared Patterns

All three agents share these Hermes orchestration patterns:

### One-Shot Execution

```
terminal(command="<agent> <exec/run flag> 'prompt'", workdir="~/project", pty=true)
```

### Background Mode (Long Tasks)

```
terminal(command="<agent>", workdir="~/project", background=true, pty=true)
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
process(action="submit", session_id="<id>", data="follow-up prompt")
```

### PR Review

Clone to temp dir for safe review, then run agent on the diff against main.

### Parallel Worktrees

```
terminal(command="git worktree add -b fix/issue-N /tmp/issue-N main", workdir="~/project")
terminal(command="<agent> 'Fix issue #N' ", workdir="/tmp/issue-N", background=true, pty=true)
```

---

## Claude Code

[Full reference](references/claude-code.md)

Claude Code is the most capable for complex tasks — it can spawn subagents, manage PRs, and handle multi-file refactors.

**Quick start:**
```bash
# One-shot
terminal(command="claude -p 'Add dark mode toggle'", workdir="~/project", pty=true)

# Background
terminal(command="claude", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Refactor the auth module")
```

**Key flags:**
| Flag | Effect |
|------|--------|
| `-p "prompt"` | One-shot: run prompt and exit |
| `--allowedTools` | Restrict available tools for safety |
| `--dangerously-skip-permissions` | Skip all approval prompts (yolo mode) |
| `--verbose` | Show detailed tool usage |

**Capabilities:** File read/write, shell commands, git operations, subagent spawning, web search, PR creation/review.

---

## Codex

[Full reference](references/codex.md)

Codex excels at batch operations — parallel issue fixing, bulk PR reviews, worktree-based workflows.

**Quick start:**
```bash
# One-shot
terminal(command="codex exec 'Add retry logic to API calls'", workdir="~/project", pty=true)

# With auto-approve
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
```

**Key flags:**
| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

**Rules:**
1. Always use `pty=true` — Codex is an interactive terminal app
2. Git repo required — Codex won't run outside one
3. Use `exec` for one-shots; background for long tasks

---

## OpenCode

[Full reference](references/opencode.md)

OpenCode is provider-agnostic — use any LLM provider. Good for iterative sessions.

**Quick start:**
```bash
# One-shot (no pty needed)
terminal(command="opencode run 'Add error handling for token expiry'", workdir="~/project")

# Interactive
terminal(command="opencode", workdir="~/project", background=true, pty=true)
```

**Key flags:**
| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue last session |
| `--model provider/model` | Force specific model |
| `--file <path>` / `-f` | Attach file(s) to message |
| `--thinking` | Show model thinking blocks |

**Pitfalls:**
- `/exit` is NOT a valid command — it opens agent selector. Use Ctrl+C to exit
- Interactive TUI sessions require `pty=true`; `opencode run` does NOT need pty
- Enter may need to be pressed twice to submit in TUI

---

---

## Oh My Pi (omp)

[Full reference](references/oh-my-pi.md)

Oh My Pi is a fork of Pi with a Rust core, 40+ providers, 32 built-in tools, LSP/DAP support, browser automation, and subagent spawning. Provider-agnostic — use any LLM provider.

**Install:**
```bash
curl -fsSL https://omp.sh/install | sh
# or
bun install -g @oh-my-pi/pi-coding-agent
```

**Quick start:**
```bash
# One-shot
terminal(command="omp -p 'Add retry logic to API calls'", workdir="~/project", pty=true)

# Background interactive
terminal(command="omp", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Refactor the auth module")
```

**Key flags:**
| Flag | Effect |
|------|--------|
| `-p "prompt"` | One-shot: run prompt and exit |
| `--model provider/model` | Pick provider/model (fuzzy match) |
| `--smol` / `--slow` / `--plan` | Model presets (set in config.yml) |
| `--api-key <key>` | API key override |
| `--resume` | Resume a past session |
| `--profile <name>` | Isolated profile for auth/sessions |
| `--thinking <level>` | Set thinking level (off/minimal/low/medium/high/xhigh/auto) |
| `--auto-approve` | Skip all approval prompts |
| `--config <file>` | Load extra config overlay (repeatable) |

**Config structure** (lives at `~/.omp/agent/`):
- `config.yml` — model roles, display, compaction, providers, extensions
- `models.yml` — provider definitions (baseUrl, api format, model list with compat settings)
- `mcp.json` — MCP server connections
- `agent.db` — SQLite session store (auto-created)

**Auth:** omp reads API keys from environment variables named after the provider. Convention: uppercase provider name with hyphens replaced by underscores, suffixed with `_API_KEY` (e.g. `OLLAMA_CLOUD_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`). Also supports `--api-key` flag and `omp auth-broker` for credential vault.

**Pitfalls:**
- Always use `pty=true` for interactive sessions
- Git repo required in workdir
- Config files must be at `~/.omp/agent/` — omp reads from `PI_CODING_AGENT_DIR` or `~/.omp/agent`
- The terminal tool may redact `***` patterns in API keys passed inline — use `$(cat /path/to/keyfile)` or env vars set from a file to work around this
- `omp token <provider>` confirms the key omp is reading
- If a provider works via curl but omp returns 401, check: (a) the env var name matches omp's convention, (b) the baseUrl in models.yml is correct, (c) the model ID format matches what the provider expects

## Choosing an Agent

| Situation | Best agent |
|-----------|------------|
| Complex multi-file refactor | Claude Code (subagent support) |
| Batch parallel issue fixing | Codex (worktree-native) |
| Specific non-OpenAI/Anthropic model | OpenCode (provider-agnostic) |
| PR review on a PR number | Claude Code (`/pr N`) or OpenCode (`pr N`) |
| Scratch/throwaway experiment | Any — `mktemp -d && git init && <agent>` |
| User explicitly names an agent | Use that one |

## Cross-Cutting Rules

1. **Always use `pty=true`** for interactive agent sessions
2. **Git repo required** — all three agents refuse to run outside one
3. **Scope each session to one repo/workdir**
4. **Monitor long tasks** with `process(action="poll"|"log")`
5. **For parallel tasks**, use different worktrees/workdirs per agent
6. **Report concrete outcomes** (files changed, tests, risks)
7. **Exit gracefully** — use Ctrl+C or process kill, not random commands

## Related Skills

- `hermes-agent` — Spawning Hermes instances as an alternative
- `subagent-driven-development` — Hermes-native task delegation (no external CLI)
- `github-workflow` — PR/merge operations after agent completes
- `kanban-codex-lane` — Using Codex as a lane inside Kanban workers