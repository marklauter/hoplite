# CLAUDE.md

Hoplite — a knowledge graph over a markdown corpus, originally packaged as the Claude Code plugin `msl.hoplite` at `plugins/hoplite/`. The active work is the spec corpus under `docs/` and the frontmatter-validation hook. The template build system and most of the shipped plugin are dead or legacy — read Layout before touching them.

## Layout

- `docs/hoplite/` — the spec corpus (active). The locked specs `expressing-edges.md` (the wikilink/edge grammar) and `frontmatter.md` (the frontmatter standard) are the source of truth; plus architecture, tool API, and roadmap.
- `docs/hoplite/glossary/` — domain glossary, one node per term; `README.md` indexes them.
- `docs/notes/` and `docs/journal/` — the agent's own corpus: design history and running notes. Free to add.
- `docs/proxies/` — proxy documents for external resources: frontmatter'd markdown stand-ins carrying a URL and summary so the resource can be linked from the graph.
- `plugins/hoplite/hooks/` — **live, committed source.** `check-frontmatter.py` (a PostToolUse hook validating wikilinks in `docs/`) and `edge_grammar.py` (the executable form of `expressing-edges.md`, with `test_edge_grammar.py`). Edit these directly.
- `plugins/hoplite/` (everything else — `mcp/`, `skills/`, plugin packaging) — **mostly dead/legacy**, not the current focus. Don't assume it reflects the current model.
- `templates/` — **dead.** A retired "mail-merge" build (`build/build.py`, `manifest.txt`) that once generated skill bodies and the hook from `templates/` source. Abandoned; don't edit or build from it. The hook it used to generate is now plain committed source under `plugins/hoplite/hooks/`.

## Conventions

- The source of truth for the frontmatter and edge model is the locked specs under `docs/hoplite/`. The hook enforces them; edit it directly in `plugins/hoplite/hooks/`.
- Write corpus prose to the Microsoft Writing Style Guide: plain, scannable, one idea per sentence.

## Python idioms

- Use protocol style interfaces.
