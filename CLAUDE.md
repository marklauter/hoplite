# CLAUDE.md

Claude Code marketplace `msl.hoplite` shipping one plugin, `hoplite`, at `plugins/hoplite/`. The plugin bundles the Hoplite MCP server (knowledge graph over markdown) with two agent-facing skills (`taking-notes`, `journaling`) that author into the vault and inject the hoplite tool reference from `components/hoplite/`.

README covers install. Spec corpus lives at `docs/mcp/`.

## Layout

- `plugins/hoplite/mcp/` — MCP server source (Python, FastMCP, src/tests layout).
- `plugins/hoplite/skills/{taking-notes,journaling}/` — agent-facing skills. Both inject the components below.
- `plugins/hoplite/components/hoplite/` — shared markdown fragments: `frontmatter.md` (the YAML contract) and `tool-reference.md` (the MCP tools, edges, vocabulary).
- `plugins/hoplite/hooks/` — `SessionStart` bootstrap (`bootstrap-venv.py`) and `PostToolUse` frontmatter validator (`check-frontmatter.py`).
- `docs/mcp/` — spec corpus. Canonical data model, behavior, implementation, decision log, roadmap.
- `docs/notes/` and `docs/journal/` — the agent's own corpus. Notes from the design history live here as historical record; agents are free to add new ones.

## Conventions

- Components start at H2; the consuming skill owns the H1.
- Component paths in skill bodies are anchored on `${CLAUDE_PLUGIN_ROOT}/components/...`.
- The bootstrapped venv at `${CLAUDE_PLUGIN_DATA}/venv/` is editable-pinned to `plugins/hoplite/mcp/src/`, so server-side Python changes take effect on the next process spawn.
