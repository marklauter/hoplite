# CLAUDE.md

Hoplite — a knowledge graph over a markdown corpus. The repo is a Claude Code plugin marketplace (`hoplite`) shipping two plugins, plus the spec corpus under `docs/`.

## Layout

- `.claude-plugin/marketplace.json` — the `hoplite` marketplace: two plugins, `hoplite-skills` and `hoplite-mcp`.
- `plugins/hoplite-skills/` — the live plugin: authoring skills, the frontmatter-validation hook, and the locked specs.
  - `references/` — **source of truth** for the locked specs: `expressing-edges.md` (the wikilink/edge grammar) and `frontmatter.md` (the frontmatter standard). `docs/hoplite/` reaches them through symlinks, so corpus wikilinks still resolve.
  - `skills/` — the seven authoring skills (glossary, spec, decision, taking-notes, journaling, todo, domain-modeling). They cite the specs via `${CLAUDE_PLUGIN_ROOT}/references/`.
  - `hooks/` — `check-frontmatter.py` (a PostToolUse hook validating wikilinks in `docs/`) and `edge_grammar.py` (the executable form of `expressing-edges.md`, with `test_edge_grammar.py`).
- `plugins/hoplite-mcp/` — stub. The knowledge-graph MCP server, under design; no server is shipped yet.
- `docs/hoplite/` — the spec corpus: architecture, tool API, roadmap, and symlinks to the locked specs.
- `docs/hoplite/glossary/` — domain glossary, one node per term; `README.md` indexes them.
- `docs/notes/` and `docs/journal/` — the agent's own corpus: design history and running notes. Free to add.
- `docs/proxies/` — proxy documents for external resources: frontmatter'd markdown stand-ins carrying a URL and summary so the resource can be linked from the graph.
- `templates/` — **dead.** A retired "mail-merge" build (`build/build.py`, `manifest.txt`) that once generated skill bodies and the hook. Abandoned; don't edit or build from it.

## Conventions

- The source of truth for the frontmatter and edge model is the locked specs under `plugins/hoplite-skills/references/`. The hook enforces them; edit it directly in `plugins/hoplite-skills/hooks/`.
- Write corpus prose to the Microsoft Writing Style Guide: plain, scannable, one idea per sentence.

## Python idioms

- Use protocol style interfaces.
