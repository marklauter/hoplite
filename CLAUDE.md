# CLAUDE.md

Claude Code marketplace `msl.hoplite` shipping one plugin, `hoplite`, at `plugins/hoplite/`. The plugin bundles the Hoplite MCP server (knowledge graph over markdown) with two agent-facing skills (`taking-notes`, `journaling`) that author into the corpus and inject the hoplite tool reference from `components/hoplite/`.

README covers install. Spec corpus lives at `docs/hoplite/`.

## Layout

- `plugins/hoplite/mcp/` — MCP server source (Python, FastMCP, src/tests layout).
- `plugins/hoplite/skills/{graph-reference,taking-notes,journaling}/` — agent-facing skills. `graph-reference` is a thin wrapper over the MCP tool reference; the two authoring skills inject the components below.
- `plugins/hoplite/components/shape/` — `artifact-structure.md` (document composition + template) and `frontmatter.md` (the YAML contract).
- `plugins/hoplite/components/hoplite/` — `mcp-reference.md` (the MCP tools, edges, vocabulary).
- `plugins/hoplite/components/prose/` — `writing-prose.md` (title/summary/body virtues, composition, grammar, validation).
- `plugins/hoplite/hooks/` — `SessionStart` bootstrap (`bootstrap-venv.py`) and `PostToolUse` frontmatter validator (`check-frontmatter.py`).
- `docs/hoplite/` — spec corpus. Architecture, tool API, roadmap.
- `docs/notes/` and `docs/journal/` — the agent's own corpus. Notes from the design history live here as historical record; agents are free to add new ones.

## Conventions

- Components start at H2; the consuming skill owns the H1.
- Component paths in skill bodies are anchored on `${CLAUDE_PLUGIN_ROOT}/components/...`.
- **Components contain no cat injections and no `${CLAUDE_PLUGIN_ROOT}` references in their bodies.** Cat invocations only live in skill SKILL.md files; components are leaf content. This means the consuming skill's injection is a bare `!`cat <path>`` — no sed pipe needed to expand placeholders, and no compound-command permission gate to negotiate. Composition stays one level deep: skill cats component; component cats nothing.
- The bootstrapped venv at `${CLAUDE_PLUGIN_DATA}/venv/` is editable-pinned to `plugins/hoplite/mcp/src/`, so server-side Python changes take effect on the next process spawn.
