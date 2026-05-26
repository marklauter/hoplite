[![claude code](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=anthropic)](https://docs.claude.com/en/docs/claude-code/plugins)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![hoplite](https://raw.githubusercontent.com/marklauter/hoplite/main/images/hoplite.small.png "Hoplite MCP")
![MSL Armory](https://raw.githubusercontent.com/marklauter/hoplite/main/images/msl.armory.small.png "MSL Armory")

# Hoplite MCP

*Another weapon from the MSL Armory*

A knowledge graph over markdown documents. Claude Code MCP plugin that organizes your agent's thoughts.

## What hoplite is

The vault is a directory of `.md` files with YAML frontmatter — fully Obsidian-compatible. At MCP server startup, hoplite builds an in-memory graph from the vault and exposes four query tools so agents can discover documents, traverse the graph, refresh after writing, and dump state for SQL debugging.

Content reads happen through the agent's built-in `Read` tool; writes happen through `Write` and `Edit`. There is no CRUD surface on hoplite itself.

The corpus of `.md` files is the only persistent state in the system. Everything else — edges, MinHash signatures, the FTS5 text index, alias and casefold lookup tables — derives at startup and lives in RAM.

## Install

From inside Claude Code, with `<repo>` as the absolute path to your clone (the directory holding `.claude-plugin/marketplace.json`):

```text
/plugin marketplace add <repo>
/plugin install hoplite@msl.hoplite
```

**After first install, fully restart Claude Code.** The plugin's MCP server runs under a venv that a `SessionStart` hook builds in `${CLAUDE_PLUGIN_DATA}` — this is Anthropic's [recommended pattern for plugins that ship language dependencies](https://code.claude.com/docs/en/plugins-reference#persistent-data-directory). `SessionStart` fires on session start, not on `/plugin install`, so the very first install requires one full Claude Code restart for the venv to build before the MCP server can connect. `/reload-plugins` alone is not enough — the supervisor would keep retrying against an empty venv and time out at 30 s.

After source changes, run `/plugin uninstall hoplite@msl.hoplite` followed by `/plugin install hoplite@msl.hoplite` to refresh the cached SKILL.md and components. `/reload-plugins` alone respawns the MCP server but keeps stale cached prose.

## Prerequisites

`python3` on `PATH`. The MCP server runs under a bootstrapped venv built at SessionStart; the bootstrap itself runs under system `python3`.

On Windows: install Python 3.x **from the Microsoft Store** for the simplest path — it registers both `python` and `python3` as working executables on `PATH`.

Modern Windows ships a `python3.exe` *App Execution Alias* at `%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe` that **looks** like Python but is actually a stub that opens the Microsoft Store page when invoked. If you skip the Store install (or installed only from python.org, which ships `python` but not `python3`), this stub is what `python3` resolves to. The SessionStart hook then silently fails to bootstrap the venv, and the MCP server reports `connection timed out after 30000ms` with no obvious cause.

To verify your `python3` is real, not the stub:

```powershell
python3 --version   # should print "Python 3.x.y", not open the Store
where.exe python3   # the first hit should NOT be under WindowsApps\python3.exe
```

If the first `where.exe` hit is the WindowsApps stub, either install Python from the Microsoft Store, or disable the alias under **Settings → Apps → Advanced app settings → App execution aliases** and symlink `python3.exe → python.exe` in your python.org install directory.

Linux distributions vary — `python3` resolves out of the box on most. If your distribution ships only `python`, install `python-is-python3` or the equivalent.

## What you get

### Skills

Three agent-facing skills compose with the knowledge graph:

- `graph-reference` — query the graph. Loads the tool reference and edge vocabulary only; use this when you want to search, traverse, reindex, or dump without loading the authoring workflow.
- `taking-notes` — author atomic notes under `docs/notes/`, each capturing the current state of one idea.
- `journaling` — author dated, append-only entries under `docs/journal/`.

The `graph-reference` skill is a thin wrapper over `components/hoplite/mcp-reference.md`. The authoring skills (`taking-notes`, `journaling`) inject that same reference alongside `shape/artifact-structure.md`, `shape/frontmatter.md`, and `prose/writing-prose.md` — covering structure, frontmatter, query surface, and prose virtues. One canonical source per component; multiple invocation paths.

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

For depth on the architecture, see [docs/hoplite/architecture.md](docs/hoplite/architecture.md).

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

If the MCP server times out on first install on Windows, the most common cause is the WindowsApps `python3.exe` App Execution Alias being used instead of a real Python — see the Windows note under [Prerequisites](#prerequisites).

## Development

Layout:

- `plugins/hoplite/mcp/` — the MCP server (Python). `src/hoplite/` holds the package; `tests/` holds the unit and smoke tests.
- `plugins/hoplite/skills/` — `graph-reference`, `taking-notes`, and `journaling`, each with a `SKILL.md`.
- `plugins/hoplite/components/shape/` — `artifact-structure.md` (document composition + template) and `frontmatter.md` (the YAML contract).
- `plugins/hoplite/components/hoplite/` — `mcp-reference.md` (the MCP tools, edges, vocabulary).
- `plugins/hoplite/components/prose/` — `writing-prose.md` (title/summary/body virtues, composition, grammar, validation).
- `plugins/hoplite/hooks/` — `hooks.json` plus the Python hook scripts (`bootstrap-venv.py`, `check-frontmatter.py`).

Running tests:

```bash
cd plugins/hoplite/mcp && pytest
```

The MCP server's test suite is the only test corpus in this repo (~145 tests covering the walker, parser, filtering, minhash, wikilinks, traverse, and an end-to-end smoke).

Build gate is `ruff format --check`, `ruff check`, `pyright`, then `pytest` — run each in sequence from `plugins/hoplite/mcp/`.

Adding a skill: create `plugins/hoplite/skills/<skill-name>/SKILL.md`, then `/plugin uninstall` + `/plugin install` to refresh the cache.

## Reference

- [docs/hoplite/readme.md](docs/hoplite/readme.md) — spec index.
- [docs/hoplite/architecture.md](docs/hoplite/architecture.md) — corpus, graph, walker, FTS5, MinHash, dump schema, error model.
- [docs/hoplite/tool-api.md](docs/hoplite/tool-api.md) — MCP tool signatures and semantics.
- [docs/hoplite/roadmap.md](docs/hoplite/roadmap.md) — features deferred past day one.
- [plugins/hoplite/components/shape/artifact-structure.md](plugins/hoplite/components/shape/artifact-structure.md) — document composition and template, injected by the authoring skills.
- [plugins/hoplite/components/shape/frontmatter.md](plugins/hoplite/components/shape/frontmatter.md) — the frontmatter contract, injected by the authoring skills.
- [plugins/hoplite/components/hoplite/mcp-reference.md](plugins/hoplite/components/hoplite/mcp-reference.md) — the MCP tool reference, injected by all three skills.
- [plugins/hoplite/components/prose/writing-prose.md](plugins/hoplite/components/prose/writing-prose.md) — title/summary/body virtues, composition, grammar, validation; injected by the authoring skills.
