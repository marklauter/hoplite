# CLAUDE.md

Hoplite — a knowledge graph over a markdown corpus. A Claude Code plugin marketplace
shipping `hoplite-skills` (authoring skills, frontmatter hook) and `hoplite-mcp` (the
`catalog` MCP server), plus the corpus under `docs/`.

## Reading `docs/`

To explore the corpus, use the `catalog` MCP tools. The corpus root is `docs/` — start
there, since `under` defaults to the repo root, which is not it.

- `contents(under, keys)` — one folder: its subtree with per-folder document counts, then
  the documents in that folder with their frontmatter. `contents(under="docs")` is the
  layout. `keys` trims the frontmatter to the properties you name.
- `vocabulary(under)` — every frontmatter key in use and how many documents carry it. Call
  it before passing `keys`, since a key that doesn't exist returns nothing.

## Rules

- `plugins/hoplite-skills/references/` is the source of truth for the locked specs.
  `docs/specs/` reaches them by symlink, so edit the originals.
- `plugins/hoplite-mcp` takes no runtime dependency, ever. Stdlib only, so the plugin has
  no install step. Dev tooling is exempt.
- Python: protocol-style interfaces.
- Corpus prose: Microsoft Writing Style Guide. Plain, scannable, one idea per sentence. Run
  the `hoplite-skills:proofreading` skill after writing a markdown file.

## Plugin script-location trap

Scripts a skill uses live under that skill's own directory: `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/`. A SKILL.md that names a script without anchoring its path leaves the agent looking in the wrong place, finding nothing, and reporting "scripts not installed." Every script reference in a SKILL.md needs an explicit `${CLAUDE_PLUGIN_ROOT}/...` path.