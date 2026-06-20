# CLAUDE.md

Claude Code marketplace `msl.hoplite` plugin, `hoplite`, at `plugins/hoplite/`. The plugin bundles the Hoplite MCP server (knowledge graph over markdown) with related agent-facing skills (`research`, `frontmatter`). Skill bodies and one hook are "mail-merged" at build time from `templates/` so the shipped plugin contains no runtime cross-tree reads.

README covers install. Spec corpus lives at `docs/hoplite/`.

## Layout

- `plugins/hoplite/` — the shipped plugin: MCP server source (`mcp/`, Python, FastMCP, src/tests layout), generated skills (`skills/`), and hooks (`hooks/`). Build details are governed by skills.
- `docs/hoplite/` — spec corpus. Architecture, tool API, roadmap.
- `docs/hoplite/glossary/` — domain glossary, one node per term; `README.md` is the index over them.
- `docs/notes/` and `docs/journal/` — the agent's own corpus. Notes from the design history live here as historical record; agents are free to add new ones.
- `docs/proxies/` — proxy documents for external resources: frontmatter'd markdown stand-ins carrying an external resource's URLs and summary so it can be linked and referenced from the graph.

## Conventions

- The shipped plugin's generated skills and templated hook are mail-merged from `templates/` — see the `/building-templates` skill. Edit the `templates/` source and rebuild; never touch the generated outputs.
- The bootstrapped venv at `${CLAUDE_PLUGIN_DATA}/venv/` is editable-pinned to `plugins/hoplite/mcp/src/`, so server-side Python changes take effect on the next process spawn.

## Python idioms

- Use protocol style interfaces.
