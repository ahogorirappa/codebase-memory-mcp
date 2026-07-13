# OpenClaw GraphRAG Plugin (codebase-memory-mcp)

A self-contained bundle that turns [codebase-memory-mcp](../../README.md) into a
**GraphRAG / knowledge-graph RAG** source for the **OpenClaw** coding agent.

codebase-memory-mcp indexes your repository into a persistent knowledge graph of
functions, classes, call chains, HTTP routes, and cross-service links. This
plugin wires that graph into OpenClaw as an MCP server **and** installs a rules
file that steers the agent to retrieve context from the graph (via `search_graph`,
`trace_path`, `get_code_snippet`, `query_graph`, `get_architecture`) instead of
blind grep/glob — the retrieval-augmented-generation workflow, backed by a graph.

## Contents

```
openclaw-graphrag-plugin/
├── README.md                        # this file
├── openclaw.json                    # MCP server entry (merge into ~/.openclaw/openclaw.json)
└── rules/
    └── codebase-memory-mcp.md       # GraphRAG guidance (copy to ~/.openclaw/rules/)
```

## Install (automatic)

The main installer detects OpenClaw and drops both files for you:

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

It writes:

| File | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | registers the `codebase-memory-mcp` MCP server under `mcp.servers` |
| `~/.openclaw/rules/codebase-memory-mcp.md` | the GraphRAG rules (marker-wrapped, idempotent) |

Restart OpenClaw, then say **"Index this project"**.

## Install (manual)

1. Copy the rules file:
   ```bash
   mkdir -p ~/.openclaw/rules
   cp rules/codebase-memory-mcp.md ~/.openclaw/rules/
   ```
2. Merge `openclaw.json` into your `~/.openclaw/openclaw.json` (keep your other
   settings). Point `command` at your installed binary:
   ```bash
   command -v codebase-memory-mcp   # use this path
   ```
3. Restart OpenClaw and verify the `codebase-memory-mcp` server is connected.

## Uninstall

```bash
codebase-memory-mcp uninstall
```

removes the MCP entry from `openclaw.json` and strips the marker-wrapped section
from `~/.openclaw/rules/codebase-memory-mcp.md`. The rules file uses the markers
`<!-- codebase-memory-mcp:start -->` / `<!-- codebase-memory-mcp:end -->`, so an
upsert only ever touches its own section and leaves the rest of the file intact.

## Notes

- The rules content is identical to what every other instruction-capable agent
  (Codex, Gemini CLI, OpenCode, KiloCode, …) receives — one shared GraphRAG
  prompt, kept in sync from the CLI source.
- All indexing happens 100% locally; your code never leaves your machine.
