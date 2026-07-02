[![claude code](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=anthropic)](https://docs.claude.com/en/docs/claude-code/plugins)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![hoplite](https://raw.githubusercontent.com/marklauter/hoplite/main/images/hoplite.small.png "Hoplite MCP")
![MSL Armory](https://raw.githubusercontent.com/marklauter/hoplite/main/images/msl.armory.small.png "MSL Armory")

# Hoplite MCP

*Another weapon from the MSL Armory*

A knowledge graph over a markdown corpus — a **map of meaning** your agent can read, traverse, and act on. A Claude Code MCP plugin that organizes your agent's thoughts.

## What hoplite is

A directory of `.md` files with Obsidian-compatible YAML frontmatter is bare text on disk. Hoplite reads it as a layered map:

- **Substrate** — the bare graph. Every document is a `node`, every link an `edge`. Structure, no meaning.
- **Meaning** — the knowledge graph. A `document` is what a node holds: its frontmatter and content. A `relationship` is a stereotyped link that says *how* two documents relate, not merely that they do. This is the map drawn on the structure.
- **Use** — `affordances`. What the map makes possible for an agent: search it, walk a neighborhood, filter edges by what a link means, rank by relatedness.

Provenance runs through the meaning layer. Every feature is a **fact** — intrinsic, read off the bytes — or a **claim** — asserted by the author or inferred by the engine. So the map separates the terrain from what was drawn on it.

Under the hood, the graph is **RDF-shaped**: a triple store where every statement is subject–predicate–object, every subject and object is a named node, and per-statement confidence rides as an RDF-star annotation. Frontmatter keys and link predicates form one open vocabulary. The full model is in [docs/hoplite/schema.md](docs/hoplite/schema.md).

Hoplite natively supports Google's [Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/). OKF and Hoplite share the same substrate — markdown files with YAML frontmatter, linked into a graph — so an OKF bundle is already a valid Hoplite corpus: each concept file becomes a node, its frontmatter becomes properties, and its markdown links become edges. Drop a bundle into the corpus and it comes out queryable as part of the RDF graph.

The corpus of `.md` files is the only persistent state. The graph, the MinHash signatures, and the text index all derive at session start and live in RAM, rebuilt from the files on demand. There is no CRUD surface on hoplite itself: content reads go through the agent's `Read` tool, writes through `Write` and `Edit`.

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

- `research` — query the graph. Loads the tool reference and edge vocabulary only; use this when you want to search, traverse, reindex, or dump without loading the authoring workflow.
- `taking-notes` — author atomic notes under `docs/notes/`, each capturing the current state of one idea.
- `journaling` — author dated, append-only entries under `docs/journal/`.

The `research` skill is a thin wrapper over `components/hoplite/mcp-reference.md`. The authoring skills (`taking-notes`, `journaling`) inject that same reference alongside `shape/artifact-structure.md`, `shape/frontmatter.md`, and `prose/writing-prose.md` — covering structure, frontmatter, query surface, and prose virtues. One canonical source per component; multiple invocation paths.

### MCP tools

Four tools register under the `plugin:hoplite:catalog` server:

- `where(predicate, k=5)` — search. BM25 over title, summary, and body; optional tag-expression post-filter (`notes & mcp`, `(plan | journal) & !draft`).
- `relatives(from_, predicate=None, depth=1)` — breadth-first walk from a starting document. Filters by edge kind, direction, similarity confidence, and tag predicate on reached nodes.
- `refresh()` — rebuild the in-memory graph from the current corpus. Call after writing or editing `.md` files.
- `export(path=None)` — snapshot the in-memory graph to a SQLite file. Default destination is `.hoplite/<ISO-timestamp>.index.sqlite`.

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
   ---

   Beans roast in three colors. Light, medium, dark. See [[notes/brewing-methods.md]] for extraction.
   ```

2. Reload the plugin so the MCP server picks up the new file:

   ```text
   /reload-plugins
   ```

3. Ask the agent to query the graph. The agent calls `where({"text": "coffee"})` and gets back hits with summary and tags. Following the wikilink resolves through `relatives(from_="notes/coffee.md")` — the unwritten `notes/brewing-methods.md` appears as a ghost node, queryable as an open loop.

4. (Optional) Dump the index for SQL exploration. Call `export()` — the tool writes `.hoplite/<timestamp>.index.sqlite`. Open it:

   ```bash
   sqlite3 .hoplite/<timestamp>.index.sqlite
   .tables
   SELECT d.path, p.value FROM document d
     JOIN document_property p ON p.path = d.path
     WHERE p.key = 'title';
   ```

## How it works

The markdown files on disk are the source of truth. Hoplite holds no canonical state of its own — every reindex rebuilds the in-memory graph from scratch by walking the corpus, parsing frontmatter, extracting wikilinks, and computing MinHash signatures.

The in-memory graph carries four surfaces: documents (file-level identity, `resolved` flag, content hash, MinHash bytes), document properties (everything from frontmatter, in EAV form), edges (`mentions` from wikilinks, `cites` from inline markdown URLs, `related` from MinHash similarity), and edge properties (currently `confidence` on `related` edges). An in-memory SQLite FTS5 index supports BM25 ranking. Tag membership is a document property, not an edge.

The dump renders this state as a property-graph projection that mirrors the in-memory shape one-to-one: `document` keyed by path, `document_property` and `edge` and `edge_property` keyed on the same natural keys their in-memory dicts use. The FTS5 index ships in contentless mode — the inverted index survives the dump for `MATCH` queries, but bodies live only in the source markdown.

For depth on the architecture, see [docs/hoplite/hoplite-architecture.md](docs/hoplite/hoplite-architecture.md).

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
- `plugins/hoplite/skills/` — `research`, `taking-notes`, and `journaling`, each with a `SKILL.md`.
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

- [docs/hoplite/hoplite-architecture.md](docs/hoplite/hoplite-architecture.md) — corpus, graph, walker, FTS5, MinHash, dump schema, error model.
- [docs/hoplite/hoplite-tool-api.md](docs/hoplite/hoplite-tool-api.md) — MCP tool signatures and semantics.
- [docs/hoplite/hoplite-roadmap.md](docs/hoplite/hoplite-roadmap.md) — features deferred past day one.
- [plugins/hoplite/components/shape/artifact-structure.md](plugins/hoplite/components/shape/artifact-structure.md) — document composition and template, injected by the authoring skills.
- [plugins/hoplite/components/shape/frontmatter.md](plugins/hoplite/components/shape/frontmatter.md) — the frontmatter contract, injected by the authoring skills.
- [plugins/hoplite/components/hoplite/mcp-reference.md](plugins/hoplite/components/hoplite/mcp-reference.md) — the MCP tool reference, injected by all three skills.
- [plugins/hoplite/components/prose/writing-prose.md](plugins/hoplite/components/prose/writing-prose.md) — title/summary/body virtues, composition, grammar, validation; injected by the authoring skills.
