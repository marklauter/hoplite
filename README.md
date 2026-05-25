[![claude code](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=anthropic)](https://docs.claude.com/en/docs/claude-code/plugins)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![hoplite](https://raw.githubusercontent.com/marklauter/hoplite/main/images/hoplite.small.png "hoplite")
![MSL Armory](https://raw.githubusercontent.com/marklauter/hoplite/main/images/msl.armory.small.png "MSL Armory")

# hoplite

*Another weapon from the MSL Armory*

Agentic note-taking with an in-memory knowledge graph over a vault of markdown documents.

## What hoplite is

The vault is a directory of `.md` files under `docs/` with YAML frontmatter — Obsidian-compatible. Every document is a node; everything authored in frontmatter (`title`, `summary`, `tags`, `created`, `aliases`, plus any user-defined keys) becomes a property on that node.

At MCP server startup the walker parses each document's frontmatter into the property store, extracts `[[wikilinks]]` from the body and emits `mentions` edges, computes a MinHash signature per body and emits symmetric `related` edges above a similarity threshold, and tokenizes title, summary, and body into an in-memory SQLite FTS5 index for BM25 search.

Agents query the graph through four MCP tools. Bodies live in the markdown files on disk — hoplite is the index, the markdown is the content. A debug-only SQLite dump renders the in-memory state as a property-graph schema you can explore with `sqlite3`.

## Install

From inside Claude Code, with `<repo>` as the absolute path to your clone (the directory holding `.claude-plugin/marketplace.json`):

```text
/plugin marketplace add <repo>
/plugin install hoplite@msl.hoplite
```

After source changes, run `/plugin uninstall hoplite@msl.hoplite` followed by `/plugin install hoplite@msl.hoplite` to refresh the cached SKILL.md and components. `/reload-plugins` alone respawns the MCP server but keeps stale cached prose.

## Prerequisites

`python3` on `PATH`. The MCP server runs under a bootstrapped venv built at SessionStart; the bootstrap itself runs under system `python3`.

On Windows: the Microsoft Store Python install ships both `python` and `python3` as working executables. The python.org installer ships only `python` and leaves `python3` as a Microsoft Store stub that opens the Store page. Use the Microsoft Store install for the simplest path, or symlink `python3.exe → python.exe` in a python.org install directory.

Linux distributions vary — `python3` resolves out of the box on most. If your distribution ships only `python`, install `python-is-python3` or the equivalent.

## What you get

### Skills

Two agent-facing skills compose with the knowledge graph:

- `taking-notes` — author atomic notes under `docs/notes/`, each capturing the current state of one idea.
- `journaling` — author dated, append-only entries under `docs/journal/`.

Both inject the hoplite tool reference from `components/hoplite/`, so an agent writing a document also learns to call `hoplite_reindex` after saving. Pure-query workflows call the MCP tools directly — they register server-side, independent of any skill.

### MCP tools

Four tools register under the `plugin:hoplite:hoplite` server:

- `hoplite_match_nodes(predicate, k=5)` — search. BM25 over title, summary, and body; optional tag-expression post-filter (`notes & mcp`, `(plan | journal) & !draft`).
- `hoplite_traverse_nodes(from_, predicate=None, depth=1)` — breadth-first walk from a starting document. Filters by edge kind, direction, similarity confidence, and tag predicate on reached nodes.
- `hoplite_reindex()` — rebuild the in-memory graph from the current corpus. Call after writing or editing `.md` files.
- `hoplite_dump_index(path=None)` — snapshot the in-memory graph to a SQLite file. Default destination is `.hoplite/<ISO-timestamp>.index.sqlite`.

### Hooks

- `SessionStart` — runs `hooks/bootstrap-venv.py` under system Python to build or refresh the MCP server's venv at `${CLAUDE_PLUGIN_DATA}/venv/`.
- `PostToolUse` matching `Write|Edit|MultiEdit` — runs `hooks/check-frontmatter.py` to validate frontmatter on every `.md` file touched under `docs/`.

## Quick start

1. Create a document with valid frontmatter. From inside a directory the agent treats as its corpus root, write `docs/notes/coffee.md`:

   ```markdown
   ---
   title: Coffee
   summary: Notes on brewing and beans.
   tags: [note, beverage]
   created: 2026-05-25
   aliases: []
   ---

   Beans roast in three colors. Light, medium, dark. See [[notes/brewing-methods.md]] for extraction.
   ```

2. Reload the plugin so the MCP server picks up the new file:

   ```text
   /reload-plugins
   ```

3. Ask the agent to query the graph. The agent calls `hoplite_match_nodes({"text": "coffee"})` and gets back hits with summary and tags. Following the wikilink resolves through `hoplite_traverse_nodes(from_="notes/coffee.md")` — the unwritten `notes/brewing-methods.md` appears as a ghost node, queryable as an open loop.

4. (Optional) Dump the index for SQL exploration. Call `hoplite_dump_index()` — the tool writes `.hoplite/<timestamp>.index.sqlite`. Open it:

   ```bash
   sqlite3 .hoplite/<timestamp>.index.sqlite
   .tables
   SELECT d.path, p.value FROM documents d
     JOIN node_properties p ON p.node_id = d.id
     WHERE p.key = 'title';
   ```

## How it works

The markdown files on disk are the source of truth. Hoplite holds no canonical state of its own — every reindex rebuilds the in-memory graph from scratch by walking the corpus, parsing frontmatter, extracting wikilinks, and computing MinHash signatures.

The in-memory graph carries five surfaces: documents (file-level identity, `resolved` flag, content hash, MinHash bytes), node properties (everything from frontmatter, in EAV form), edges (`mentions` from wikilinks, `related` from MinHash similarity), edge properties (currently `confidence` on `related` edges), and an in-memory SQLite FTS5 index for BM25 ranking. Tag membership is a node property, not an edge.

The dump renders this state as a property-graph projection. A `nodes(id, kind)` table assigns each document an integer id; `documents`, `node_properties`, `edges`, and `edge_properties` foreign-key into it. The FTS5 index ships in contentless mode — the inverted index survives the dump for `MATCH` queries, but bodies live only in the source markdown.

For depth on the data model and design rationale, see [docs/mcp/data-model.md](docs/mcp/data-model.md), [docs/mcp/implementation.md](docs/mcp/implementation.md), and [docs/mcp/decision-log.md](docs/mcp/decision-log.md).

## Troubleshooting

The MCP server respawns on `/reload-plugins`, but Claude Code's cache of SKILL.md and `components/` only refreshes on `/plugin install`. If the agent loads stale skill prose after a source change, run:

```text
/plugin uninstall hoplite@msl.hoplite
/plugin install hoplite@msl.hoplite
```

The bootstrapped venv lives at `~/.claude/plugins/data/hoplite-msl-hoplite/venv/`. If a previous install left the venv in a stuck state, remove the data directory and start a fresh Claude Code session — the SessionStart hook rebuilds the venv on the next startup:

```bash
rm -rf ~/.claude/plugins/data/hoplite-msl-hoplite
```

Hooks (`bootstrap-venv.py`, `check-frontmatter.py`) run under system Python, separate from the MCP server's venv. `python3` must resolve at the system level for the hooks to fire — verify with `python3 --version` from your shell.

## Development

Layout:

- `plugins/hoplite/mcp/` — the MCP server (Python). `src/hoplite/` holds the package; `tests/` holds the unit and smoke tests.
- `plugins/hoplite/skills/` — `taking-notes` and `journaling`, each with a `SKILL.md`.
- `plugins/hoplite/components/hoplite/` — `frontmatter.md` (the YAML contract) and `tool-reference.md` (the MCP tools, edges, vocabulary). Both skills cat both components in.
- `plugins/hoplite/hooks/` — `hooks.json` plus the Python hook scripts (`bootstrap-venv.py`, `check-frontmatter.py`).

Running tests:

```bash
cd plugins/hoplite/mcp && pytest
```

The MCP server's test suite is the only test corpus in this repo (~145 tests covering the walker, parser, filtering, minhash, wikilinks, traverse, and an end-to-end smoke).

Build gate is `ruff format --check`, `ruff check`, `pyright`, then `pytest` — run each in sequence from `plugins/hoplite/mcp/`.

Adding a skill: create `plugins/hoplite/skills/<skill-name>/SKILL.md`, then `/plugin uninstall` + `/plugin install` to refresh the cache.

## Reference

- [docs/mcp/readme.md](docs/mcp/readme.md) — spec corpus index.
- [docs/mcp/data-model.md](docs/mcp/data-model.md) — entities and fields.
- [docs/mcp/implementation.md](docs/mcp/implementation.md) — runtime shape, walker, dump schema.
- [docs/mcp/behavior.md](docs/mcp/behavior.md) — frontmatter contract, wikilink resolution, edge derivation.
- [docs/mcp/tool-api.md](docs/mcp/tool-api.md) — MCP tool signatures and semantics.
- [docs/mcp/decision-log.md](docs/mcp/decision-log.md) — chronological record of design decisions.
- [docs/mcp/roadmap.md](docs/mcp/roadmap.md) — named features deferred past day one.
- [plugins/hoplite/components/hoplite/tool-reference.md](plugins/hoplite/components/hoplite/tool-reference.md) — the tool reference injected by the authoring skills.
- [plugins/hoplite/components/hoplite/frontmatter.md](plugins/hoplite/components/hoplite/frontmatter.md) — the frontmatter contract injected by the authoring skills.
