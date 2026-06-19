# CLAUDE.md

Claude Code marketplace `msl.hoplite` plugin, `hoplite`, at `plugins/hoplite/`. The plugin bundles the Hoplite MCP server (knowledge graph over markdown) with related agent-facing skills (`research`, `taking-notes`, `journaling`, `todo`). Skill bodies and one hook are mail-merged at build time from `templates/` so the shipped plugin contains no runtime cross-tree reads.

README covers install. Spec corpus lives at `docs/hoplite/`.

## Layout

- `plugins/hoplite/mcp/` — MCP server source (Python, FastMCP, src/tests layout). Committed source, not built.
- `plugins/hoplite/skills/{research,taking-notes,journaling,todo}/SKILL.md` — generated from `templates/skills/`.
- `plugins/hoplite/hooks/check-frontmatter.py` — generated from `templates/hooks/check-frontmatter.py`.
- `plugins/hoplite/hooks/bootstrap-venv.py`, `plugins/hoplite/hooks/hooks.json` — committed source, not built.
- `templates/skills/<name>/SKILL.md` — skill source with `{{components/<path>}}` markers.
- `templates/components/{shape,prose,hoplite}/` — leaf content inlined into skills and hooks.
- `templates/hooks/check-frontmatter.py` — hook source carrying a `{{components/shape/frontmatter.md}}` marker inside a Python string constant.
- `templates/build/manifest.txt` — `src -> dst` list of files the build owns.
- `templates/build/build.py` — the mail-merge script. Run from repo root: `python templates/build/build.py`.
- `docs/hoplite/` — spec corpus. Architecture, tool API, roadmap.
- `docs/hoplite/glossary/` — domain glossary, one node per term; `README.md` is the index over them.
- `docs/notes/` and `docs/journal/` — the agent's own corpus. Notes from the design history live here as historical record; agents are free to add new ones.
- `docs/proxies/` — proxy documents for external resources: frontmatter'd markdown stand-ins carrying an external resource's URLs and summary so it can be linked and referenced from the graph.

## Conventions

- Skill bodies inject components at build time via `{{components/<area>/<file>.md}}` markers. The marker sits on its own line; the build replaces it with the literal file content. Composition is one level deep — components must not contain markers.
- Components start at H2; the consuming skill owns the H1.
- Cross-reference a section in an injected component with a markdown anchor link to its H2, not a filename. The GitHub-style anchor is the heading lowercased with spaces hyphenated and punctuation dropped — `## Artifact structure` becomes `[Artifact structure](#artifact-structure)`. Skill bodies and component bodies render into the same document after merge, so the anchor resolves.
- Edit skills and the templated hook under `templates/`, then re-run `python templates/build/build.py`; never touch the generated outputs.
- The bootstrapped venv at `${CLAUDE_PLUGIN_DATA}/venv/` is editable-pinned to `plugins/hoplite/mcp/src/`, so server-side Python changes take effect on the next process spawn.

## Python idioms

- Use protocol style interfaces.
