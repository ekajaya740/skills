## MCP Setup and Excalidraw Fallback — End-to-End Recipe

### Context
This recipe captures the full workflow discovered when attempting to connect Figma MCP tools in a Hermes Agent session, including the pivot to Excalidraw when the gateway restart was blocked by policy.

### Decision tree

```
User asks for low-fi / mid-fi / hi-fi prototype
        |
        v
Is user asking for "low-fidelity" or "wireframe" or "rough"?
        |
        +-- YES --> Use Excalidraw (faster, hand-drawn look, no setup)
        |
        +-- NO  --> Does Figma MCP work already?
                        |
                        +-- YES --> Use Figma (pixel-perfect, design system)
                        |
                        +-- NO  --> Can we get consent for gateway restart?
                                        |
                                        +-- YES --> Full MCP setup recipe below
                                        |
                                        +-- NO  --> Use Excalidraw as fallback
```

### Prerequisites check

```bash
# 1. Verify MCP SDK is installed
python3 -c "import mcp; print(mcp.__version__)"

# 2. Check if Figma tools are already registered
hermes tools | grep -i figma
# If output shows use_figma, get_screenshot, etc. -- skip to "Using Figma"
# If empty -- proceed with setup below
```

### Step A: Install MCP SDK

```bash
# In the Hermes venv (path depends on installation)
/home/user/.hermes/hermes-agent/venv/bin/python -m pip install --upgrade mcp
```

### Step B: Install the Figma skill

```bash
# Set cache for read-only filesystems
export npm_config_cache=/tmp/npm-cache
npx skills add https://github.com/figma/mcp-server-guide --skill figma-generate-design -y
```

**Post-install verification:** Repo READMEs list aliases (e.g., `implement-design`) that may not exist as actual install directories. Always inspect the filesystem:
```bash
ls /path/to/project/.agents/skills/
# Look for the actual directory name (e.g., figma-generate-design)
```

### Step C: Symlink into Hermes skills

```bash
ln -s /path/to/project/.agents/skills/figma-generate-design /home/user/.hermes/skills/figma-generate-design
```

Now `skill_view('figma-generate-design')` and `skills_list()` will discover it.

### Step D: Configure the Figma MCP server

Add to `~/.hermes/config.yaml` under `mcp_servers:`

```yaml
mcp_servers:
  figma:
    url: "https://mcp.figma.com/mcp"
    timeout: 120
    connect_timeout: 60
```

If direct file edits are blocked by Hermes, use Python I/O:
```python
python3 -c "import yaml; ..."
```

### Step E: Restart the Hermes gateway

```bash
hermes gateway restart
```

**CRITICAL — the gateway guard:** If you issue `systemctl --user start/restart/stop` (or `hermes gateway restart`) for ANY gateway unit *from inside a session the gateway itself serves* (e.g. a Telegram/Discord chat), it is blocked with:
> Blocked: cannot restart or stop the gateway from inside the gateway process.

This is because SIGTERM would propagate to the running gateway. **Fix:** run the restart from a *real SSH shell* on the server, NOT from a gateway-served chat. (For multi-profile setups, restarting a *separate* profile's unit from the default profile's Telegram session is still blocked — use a real shell.)

### Step F: Verify registration

```bash
hermes tools | grep -i figma
```

Expected tools: `use_figma`, `get_screenshot`, `get_metadata`, `search_design_system`, etc.

---

## OAuth on Headless Servers (SSH Tunnel)

When Hermes runs on a headless server (no local browser), OAuth-based MCP servers like Figma cannot complete the callback because the redirect hits `127.0.0.1` on the server.

**Solution: SSH local port forwarding with a fixed redirect port.**

1. **Pin the OAuth redirect port** so it is predictable for the tunnel:
   ```yaml
   mcp_servers:
     figma:
       url: "https://mcp.figma.com/mcp"
       timeout: 120
       connect_timeout: 60
       oauth:
         redirect_port: 8765
   ```

2. **On your local machine**, open a tunnel (keep it running):
   ```bash
   ssh -N -L 8765:127.0.0.1:8765 user@<server-ip>
   ```

3. **On the server**, run:
   ```bash
   hermes mcp login figma
   ```

4. **Copy the authorization URL** the agent prints and open it in your **local browser**.

5. After granting access, Figma redirects to `http://127.0.0.1:8765/callback`, which travels through the tunnel back to the server.

6. **Restart Hermes** (`hermes gateway restart`) so the token is discovered and Figma tools are registered.

> **Note:** If `oauth.redirect_port` is omitted, the OAuth client picks a random ephemeral port, making tunneling impossible. Always fix the port in config for headless setups.

> **Note:** The agent's OAuth handler (`mcp_oauth.py`) already detects SSH sessions (via `SSH_CLIENT` / `SSH_TTY`) and prints the `ssh -N -L ...` hint automatically, but only when the port is known ahead of time.

---

## "Figma MCP Blocked" Fallback: Excalidraw

When the gateway restart is blocked, Figma tools cannot be registered. **Excalidraw is the recommended drop-in alternative** for low-fidelity wireframes -- zero setup, no accounts, no API keys.

### When to pivot to Excalidraw

- Gateway restart was denied by user or policy
- Figma MCP tools do not appear after restart (auth/account issues)
- User has a Figma Starter/View/Collab seat (rate-limited to ~6 tool calls/month)
- Network issues prevent reaching `mcp.figma.com`
- The task explicitly says "low-fidelity prototype" (Excalidraw's rough style is often preferred for this)

### Pivot workflow

1. **Load the `excalidraw` skill** -- contains the JSON schema and color palette
2. **Inventory all screens** -- read all PHP/HTML files to understand the full page list
3. **Generate the `.excalidraw` JSON** via `execute_code` -- build an `elements` array for each screen
4. **Save** with `write_file` using the standard envelope:
   ```json
   {"type":"excalidraw","version":2,"source":"hermes-agent","elements":[...]}
   ```
5. **Upload for shareable link** via the skill's `scripts/upload.py`:
   ```bash
   python3 /home/user/.hermes/skills/creative/excalidraw/scripts/upload.py /path/to/file.excalidraw
   ```
6. **Deliver the link** to the user -- opens editable at excalidraw.com without accounts

### Excalidraw vs Figma trade-offs

| Factor | Excalidraw | Figma MCP |
|--------|-----------|-----------|
| Setup time | None | 5-10 min (install + config + restart) |
| External dependencies | None | MCP SDK, Node.js, Figma account with Dev seat |
| Gateway restart | Not needed | Required |
| User consent needed | No | Yes (for gateway restart) |
| Fidelity | Low-fi (rough hand-drawn) | Hi-fi (exact design system) |
| Editability | Yes, in browser | Yes, in Figma editor |
| Best for | Quick wireframes, screen inventory | Pixel-perfect design system alignment |

### Key lesson

When the user asks for a "low-fidelity prototype," the Excalidraw path is often **faster and equally valid** -- the rough hand-drawn aesthetic is actually what "low-fi" means. Do not default to the heavier Figma path without considering whether the faster alternative already satisfies the requirement.
