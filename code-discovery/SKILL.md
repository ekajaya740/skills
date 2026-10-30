---
name: code-discovery
description: Answer structural code questions from a persistent code graph instead of reading files — who calls this, what does it call, what is the shape of this module — and decide whether the graph can be trusted before you query it. Use when exploring an unfamiliar codebase, tracing a call chain, planning a refactor, hunting dead code, or whenever a grep would fan out across hundreds of lines. Also covers installing and registering the MCP server, index freshness, per-directory project resolution, and reclaiming disk from stale indexes.
disable-model-invocation: true
version: 0.1.0
---

# Code Discovery

**A graph query is an accelerator, not a gate.** If the index is absent or stale, read files. A
wrong answer from a stale graph costs more than the tokens it saved.

The tool is [`codebase-memory-mcp`](https://github.com/DeusData/codebase-memory-mcp) — DeusData,
MIT — which builds a persistent knowledge graph of functions, call chains, imports and HTTP
routes, keyed by **directory**, so a structural question is one query instead of a dozen reads.

It is a separate program, not part of this skill. Install and register it yourself; this skill
documents how, and what to do with it once it is running.

## Install

The tool is a single static binary. Install it once per machine, then register it with each agent
harness you use.

```bash
codebase-memory-mcp --version          # already installed?
codebase-memory-mcp update             # update in place
```

If it is missing, install from the upstream release at
<https://github.com/DeusData/codebase-memory-mcp/releases>, and put the binary somewhere on
`PATH` — `~/.local/bin` is the conventional place, and the script falls back to it when `PATH`
is not set up:

```bash
install -d ~/.local/bin
# download the release for your platform into ~/.local/bin/codebase-memory-mcp
chmod +x ~/.local/bin/codebase-memory-mcp
export PATH="$HOME/.local/bin:$PATH"    # add to your shell profile
```

**Register it with a harness.** One command per agent, and it edits that agent's MCP config itself:

```bash
codebase-memory-mcp install --clients=claude --dry-run   # see what it would change
codebase-memory-mcp install --clients=claude             # write it
```

`codebase-memory-mcp install --clients` lists every token. Common ones: `claude`, `codex`, `gemini`,
`opencode`, `cursor`, `windsurf`, `zed`, `vscode`, `copilot-cli`, `amp`, `goose`, `cline`. The
installer also writes a skill file and subagent definitions into the harness, and adds hooks that
remind the agent to use the graph. Pass several comma-separated tokens to do them in one run.

**`--dry-run` first.** The installer writes outside this repository — MCP config, agent files, hook
entries — and an uninstall is the only way back:

```bash
codebase-memory-mcp uninstall --dry-run      # what would be removed
codebase-memory-mcp uninstall                # keep the indexes
codebase-memory-mcp uninstall --delete-indexes
```

**Two things that bite on install:**

- **A second MCP server for the same tool loads every tool twice.** If the harness already has a
  `codebase-memory-mcp` entry in its MCP config, the installer edits that entry rather than adding
  another — but a hand-added duplicate stays. Check the harness config after installing.
- **The CLI refuses to start while a daemon holds the store:** `CBM CLI could not start because an
  active pre-coordination or unverified CBM daemon is running.` That is a lock, not a bug. Close the
  session that owns it, or use the MCP tools from inside that session instead of the CLI.

## Before any query: prove the index is current

An agent may start in one directory and work in another. Resolve from the **current** directory
every time — never from where the session began, never hardcoded.

```bash
bash scripts/cbm-here.sh            # one line: state= project= ...
bash scripts/cbm-here.sh --json     # same facts, machine-readable
bash scripts/cbm-here.sh --ensure   # reindex if stale, then re-check
```

| `state` | Meaning | What to do |
| --- | --- | --- |
| `fresh` | The graph matches this tree. | Query it. |
| `stale` | An indexed file changed, or a new one appeared. | `--ensure`, then query. |
| `absent` | This directory was never indexed. | `grep`. Index only if you will keep editing here. |
| `unknown` | The index exists but its schema is unreadable — a tool upgrade renamed a table. | `grep`. Treat as `absent`. |
| `missing` | Not a git worktree. | `grep`. Run from inside a worktree. |

Exit code is `1` for `stale`, `2` for `unknown`/`missing`, so a script can gate on it. `unknown` is
the fail-closed branch: **an index nobody can vouch for must not read as trusted.**

`--ensure` reindexes `stale` and re-runs the check, so a call cannot report a state it was asked to
fix. It does **not** create an index for `absent` — that would be the "just in case" indexing the
space budget forbids.

## The cheapest-first order

Token cost is the tool result the agent pays for: 4 bytes ≈ 1 token. Measured over 366 sessions of
real tool-result payloads on a TypeScript monorepo, plus a live A/B holding scope constant:

| Question | Call | Cost (p50 / mean) |
| --- | --- | --- |
| Who calls / what does this call | `trace_path` (`inbound`/`outbound`) | 62 tok (one live sample) |
| A symbol name you know exactly | `search_code --mode compact` | 127 / 163 tok |
| A literal, key, config, doc string | `grep` | 182 / 492 tok |
| A body, a whole file, several regions | `read` / `get_code_snippet` | 386 / 605 tok |

`search_code` is ~3× cheaper than `grep` **on the mean**, because grep fan-out on a common term
returns hundreds of lines; on a single distinctive symbol it is a tie (154 vs 156 tok in the live
A/B). The win is structural, not lexical: `trace_path` answers "who calls this" in one call where
grep needs a sequence of probes.

| Ask | Graph | `grep` to actually answer |
| --- | --- | --- |
| Who calls `dispatchEmail` | `trace_path inbound` → 341 B, one call | `rg` for lines + `rg -B2 -A4` for names = 1033 B |
| Body of one symbol | `get_code_snippet` → 676 B | `rg -A20` → 970 B |
| Outline of a 484-line file | `get_file_outline` → 1043 B | not expressible in one grep |

**~3× on callers, a tie on names and single bodies, and the only option for an outline.** Treat
any figure claiming 8× with suspicion: it usually compares a project-wide graph query against a
narrow grep that could not answer the question at all. Hold the scope constant or the ratio is
meaningless.

## The decision matrix

| Question | Call |
| --- | --- |
| Who calls X? | `trace_path(direction="inbound")` |
| What does X call? | `trace_path(direction="outbound")` |
| Full call context | `trace_path(direction="both")` |
| Find by name pattern | `search_graph(name_pattern=...)` |
| Dead code | `search_graph(max_degree=0, exclude_entry_points=true)` |
| High fan-out | `search_graph(min_degree=10, relationship="CALLS", direction="outbound")` |
| High fan-in | `search_graph(min_degree=10, relationship="CALLS", direction="inbound")` |
| Cross-service edges | `query_graph` with Cypher |
| Impact of local changes | `detect_changes()` |
| Text search | `search_code`, or grep |

Edge types worth knowing: `CALLS`, `HTTP_CALLS`, `ASYNC_CALLS`, `DATA_FLOWS`, `IMPORTS`, `DEFINES`,
`DEFINES_METHOD`, `HANDLES`, `IMPLEMENTS`, `OVERRIDE`, `USAGE`, `CONFIGURES`, `SIMILAR_TO`,
`SEMANTICALLY_RELATED`, `CONTAINS_FILE`, `CONTAINS_FOLDER`, `CONTAINS_PACKAGE`.

## The rulings

These are the rules that make the graph trustworthy. Each one exists because skipping it produced a
confident wrong answer.

1. **Query the graph before probing files** — for symbol, caller/callee and structure questions.
   Grep and read keep literals, docs, config, and any directory that was never indexed.
2. **Prove freshness first, every time.** `cbm-here.sh` in the directory you are editing, not the
   one you started in. `stale`, `unknown` and `absent` all mean grep.
3. **One authoritative graph per piece of work:** the one whose `root_path` equals your current
   directory. A sibling's graph answers from another branch.
4. **Never hardcode the project name.** Derive it with `--project`. The name encodes an absolute
   path, so a name written into a doc is wrong for everyone else and wrong for you after a move.
5. **Index the directory you are editing, never "just in case".** One or two live indexes is the
   budget.
6. **Delete the index before the directory.** An index outlives its worktree and leaves both a
   database and a dead `list_projects` entry.
7. **An empty result is inconclusive, not a negative.** The literal `|`, a misspelled name, and a
   page boundary all return nothing. Confirm with grep before concluding a symbol does not exist.

## Traps that make the graph cost more, or lie

- **`|` is literal unless `regex: true`.** `pattern: "foo|bar"` returns **0 results**, with only a
  warning inside the payload — which reads as "the symbol does not exist". Treat an empty result as
  inconclusive and fall back to grep.
- **A miss still costs ~343 chars** of footer. Two wrong-name guesses cost more than one grep.
- **`--mode compact` returns no source body.** You still pay for `get_code_snippet` or `read`. Grep
  with context returns the snippet inline; for "show me this function", grep is fine.
- **`--format json` costs ~1.5× `tree`** on the same query. Use `tree`.
- **`trace_path` needs exact names.** Find the name with `search_graph(name_pattern=...)` first.
- **`direction="outbound"` misses cross-service callers.** Use `"both"` when the boundary matters.
- **`search_graph` paginates at 50.** Check `has_more` and pass `offset`.
- **`search_graph(relationship=...)` filters nodes by degree**, so it can hide real edges. Use
  `query_graph` with Cypher to see the edges themselves.
- **`query_graph` has a 100k row ceiling.** Add a Cypher `LIMIT` to broad queries.

## One index per directory

The tool keys an index by **root path**, so each worktree is its own project with its own database.
There is no cross-directory query and no global search — every call takes `--project`.

- Index **this** directory, not the repo in general. A query against a sibling answers from that
  branch's code, which is usually not what you want.
- **Exactly one graph is authoritative for a piece of work: the one whose `root_path` equals the
  directory you are editing in.** Everything else is reference material.
- Never index every worktree "just in case". A `moderate` index is ~50 MB; six worktrees is 300 MB
  of duplicate graphs of the same repository.

**Never hardcode the project name.** It is the absolute root path with the leading `/` dropped and
every `/` replaced by `-`, so it encodes the machine's directory layout and changes when the clone
moves. Derive it:

```bash
bash scripts/cbm-here.sh --project       # empty when this directory has no index
```

**Freshness is automatic only for the session's own directory.** A watcher polls the project a live
session opened, so edits there reindex with no agent action. Every other index stops being
maintained the moment its session ends — measured in one workspace, `watched: true` for the main
clone and `watched: false` for all five siblings, whose indexes had frozen eight days earlier. An
index is not self-maintaining; check it before trusting an answer.

## Mode and space

| Mode | Size (measured) | Use for |
| --- | --- | --- |
| `fast` | filtered only, no semantic edges | a very large tree, one-off |
| `moderate` | ~50 MB | working copies and worktrees |
| `full` | ~160 MB | the main clone's reference graph, once |

`full` adds an LSP surface — 95 MB of type definitions in one measured project — which is a 3×
difference over `moderate`. A worktree indexed `full` is wasting ~110 MB.

**Mode is fixed at creation.** Reindexing a `full` index with `--mode moderate` leaves it `full` and
the same size (measured: 157 MB stayed 157 MB). Demoting means delete, then rebuild.

| Lever | Reclaims |
| --- | --- |
| Root gone | whole index |
| Wrong mode (worktree `full`) | 157 → 52 MB, 3 s |
| Idle live root | whole index |
| Worker logs | ~4 KB per log |

`--mode moderate` does not demote; `--demote-full` does. `--idle-days N` reaps only when nothing has
touched the index since the cutoff — measured from the index's own high-water mark, not
`projects.indexed_at`, which lags and would reap an index refreshed minutes ago.

**The practical budget: one or two live indexes at a time.** Anything above that is either a
directory you are actively editing or garbage awaiting collection.

## End of task: delete the index before the directory

An index outlives its directory if you do not, leaving its database plus a dead `list_projects`
entry.

```bash
cd ../<worktree-dir> && bash scripts/cbm-here.sh --project   # resolve, do not copy
codebase-memory-mcp cli delete_project --project <that name>
git worktree remove ../<worktree-dir>                        # from a sibling, never from inside
```

`cbm-here.sh --project` prints nothing for a directory that was never indexed, so a teardown script
can skip the delete safely.

`git worktree remove` refuses to remove the worktree it is invoked from — run it from a sibling, and
pass a relative path. It also exits 0 **after discarding gitignored work**, so commit anything you
need first.

## Recording a decision

`manage_adr` stores architecture decisions alongside the graph, so the reason a module is shaped the
way it is survives the session that produced it. Use it when a structural choice would otherwise
have to be re-derived by the next agent.

## When not to use this

- Literals, config keys, doc strings, error text: `grep`.
- A directory that was never indexed and you will not edit: `grep`.
- Anything the index calls `stale` or `unknown` until it is re-checked.
- "Just in case" exploration. An unindexed directory is a grep directory, not a violation.
