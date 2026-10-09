---
name: arxiv-mcp
description: "Use when searching or reading arXiv papers via MCP."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Arxiv, MCP, Papers, Academic, Citations]
    related_skills: [arxiv, native-mcp]
---

# arXiv MCP Server

The `arxiv` MCP server (blazickjp/arxiv-mcp-server) runs locally via `uvx` and
exposes 14 tools for search, download, full-text reading, LaTeX retrieval,
citation graphs, and research alerts. Installed on this VPS in
`~/.hermes/config.yaml` → `mcp_servers.arxiv`.

**Tools are prefixed `mcp_arxiv_`** (e.g. `mcp_arxiv_search_papers`).

## When to Use

- Search arXiv with advanced filters (author, category, date range)
- **Download a paper and read its actual content** (not just abstract)
- Get the **original LaTeX source** of a paper
- Follow a **citation graph** (who cites what, references)
- Set up a **topic watch** that alerts on new papers
- Semantic search over papers already downloaded

For quick abstract/metadata lookups where the REST API is fine, the `arxiv`
skill works too — but this MCP server is the richer path.

## Tool Reference

| Tool | Purpose |
|------|---------|
| `mcp_arxiv_search_papers` | Search with advanced filtering + query optimization |
| `mcp_arxiv_download_paper` | Download paper, return text content (HTML first, PDF fallback) |
| `mcp_arxiv_list_papers` | List all papers downloaded locally |
| `mcp_arxiv_read_paper` | Read text content of a previously downloaded paper |
| `mcp_arxiv_get_abstract` | Abstract + metadata by arXiv ID (no download) |
| `mcp_arxiv_semantic_search` | Semantic similarity over downloaded papers |
| `mcp_arxiv_reindex` | Rebuild local semantic index |
| `mcp_arxiv_citation_graph` | Papers citing a paper + papers it references (Semantic Scholar) |
| `mcp_arxiv_export_citations` | BibTeX export for one or more papers |
| `mcp_arxiv_watch_topic` | Save/update a persistent topic watch |
| `mcp_arxiv_check_alerts` | Check saved watches for new papers |
| `mcp_arxiv_get_paper_latex` | Download + cache original LaTeX source |
| `mcp_arxiv_list_paper_latex_sections` | Outline of headings from LaTeX source |
| `mcp_arxiv_get_paper_latex_section` | One bounded LaTeX section by outline ID/title |

## Workflows

### 1. Search → Read Full Paper (most common)

```text
1. mcp_arxiv_search_papers(query="GRPO reinforcement learning", ...)
2. mcp_arxiv_download_paper(paper_id="2402.03300")   # downloads + returns text
3. mcp_arxiv_read_paper(paper_id="2402.03300")       # read again later
```

### 2. Get LaTeX Source

```text
1. mcp_arxiv_get_paper_latex(paper_id="2402.03300")
2. mcp_arxiv_list_paper_latex_sections(paper_id="2402.03300")
3. mcp_arxiv_get_paper_latex_section(paper_id="2402.03300", section="Methodology")
```

### 3. Citation Graph

```text
mcp_arxiv_citation_graph(paper_id="2402.03300")
# → papers citing it + papers it references, with metadata
mcp_arxiv_export_citations(paper_ids=["2402.03300", "2401.12345"])
# → BibTeX
```

### 4. Topic Alerts

```text
mcp_arxiv_watch_topic(topic="MCP protocol security", query="MCP protocol security")
# later:
mcp_arxiv_check_alerts()   # new papers since last check
```

## Storage

- Default paper directory: `~/.arxiv-mcp-server/papers`
- Downloaded papers persist locally; `list_papers` / `read_paper` / `semantic_search` operate on them
- The semantic index can be rebuilt with `mcp_arxiv_reindex` if search feels stale

## Pitfalls

- **Requires gateway restart after install** — MCP servers are discovered at
  agent startup. `systemctl --user restart hermes-gateway` from a shell OUTSIDE
  the gateway (the agent cannot restart its own gateway process).
- **Tools are read-only safe** except `watch_topic` (persists state) and
  `download_paper` (writes to disk) — harmless local writes.
- **download_paper fetches HTML first, falls back to PDF** — some papers only
  have PDF; text extraction may be imperfect on those.
- **Citation graph uses Semantic Scholar** — rate-limited (~1 req/sec without key).
- **LaTeX retrieval is bounded** — returns chunks, not the whole source, by design.
- If tools don't appear: check `hermes mcp list` and the gateway log
  (`grep -i mcp ~/.hermes/logs/gateway.log`).
