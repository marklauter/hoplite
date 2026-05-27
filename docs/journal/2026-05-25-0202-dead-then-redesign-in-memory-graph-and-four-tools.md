---
title: Dead then redesign — in-memory graph and four query tools
summary: ULIDs die, identity collapses to path, persistent SQLite drops in favor of in-memory FTS5, retrieval tools (invoke_node, read_node) die, the 11-tool surface collapses to 4 query tools, Hoplite becomes dataview over documents. The in-memory graph + 4-tool surface lands at 01:44; the bug sweep at 02:02 closes the night.
tags: [journal, hoplite, mcp, architecture, decision, milestone]
created: 2026-05-25
aliases: []
---

# Dead then redesign — in-memory graph and four query tools

ULIDs die, identity collapses to path, persistent SQLite drops in favor of in-memory FTS5, retrieval tools (`invoke_node`, `read_node`) die, the 11-tool surface collapses to 4 query tools, Hoplite becomes dataview over documents. The in-memory graph + 4-tool surface lands at 01:44; the bug sweep at 02:02 closes the night.

## Intent

Going into this session, the spec had:

- ULID + filename + integer-PK three-tier identity.
- Persistent SQLite-hybrid storage with WAL mode.
- 11-tool MCP surface: `match`, `invoke`, `read`, `insert`, `update`, `delete`, `apply_framing`, `slugify`, `traverse`, plus the indexer-facing `reindex` and `repair`.
- Per-doc sidecars holding cached metadata.
- Framing-axis labels (`instruction`, `reference`, `observation`) driving response envelopes on retrieval.

The session opened with a tidy-up — the "dead" commit at the previous evening's 22:06 just deleted a stale 2508-line caveat file. The real architecture work started after midnight.

A sub-agent's clarification question about parsing the title from a body's line-1 H1 surfaced a defect — documents in the corpus had no H1. That single observation cracked open a stack of decisions that had to fall together.

## What fell (chronological)

- 2026-05-24 22:06 — "dead". Removed the 2508-line caveat file. Setup move, not the architectural pivot. Workspace gets clean before the design pivot.
- 2026-05-25 00:45 — "redesign". The pivot commit. Adds the design decision log (309 lines documenting the supersession trail), adds the `refactor-ids-and-metadata` snapshot note, deletes `ids.py` (91 lines), deletes `test_ids.py` (128 lines). The decision-log entries from this commit:
  - **Lift title and summary out of body into YAML frontmatter** — body-shape contract broke for code, transcripts, fragments. Frontmatter is the standard pattern. Title and summary become first-class metadata.
  - **ULIDs and three-tier identity dropped** — identity collapses to path. Aliases handle rename continuity.
  - **All derived state lives only in memory; no sidecars, no cache files** — corpus of `.md` files is the only persistence. Everything else builds at MCP startup from those files.
  - **BM25 via in-memory SQLite FTS5** — `:memory:` SQLite with FTS5; C-backed tokenization beats pure-Python; built-in BM25 scoring is sub-millisecond.
  - **MCP surface drops CRUD tools** — agents have Write, Edit, Bash through Claude Code; they can write `.md` files directly. The skill teaches the file shape and the wikilink rules.
  - **All retrieval tools eliminated; Hoplite is dataview over documents** — `invoke_node` and `read_node` die. Hoplite stops being a content-retrieval system. Agents discover candidates through `match_nodes` and `traverse_nodes` (returning paths, summaries, tags — no bodies), then use Claude's built-in `Read` to fetch content.
- 2026-05-25 01:44 — "in-memory graph + 4-tool query surface". The implementation commit. The new shape lands as working code. The 4 tools: `hoplite_match_nodes`, `hoplite_traverse_nodes`, `hoplite_reindex`, `hoplite_dump_index`.
- 2026-05-25 02:02 — "vault = <cwd>/docs; fix tag casefold, fts5 escape, traverse casefold, crlf frontmatter". The bug sweep after the first working state. Corpus root resolves to `<cwd>/docs` rather than an env-var; tag matching casefolds for lookup; FTS5 special-character escape; traversal target lookup casefolds; CRLF-line-ending frontmatter parses correctly.

## What the new shape looks like

Runtime storage layout:

- `Graph.documents: dict[str, Document]` — entity index by path.
- `Graph.tags: dict[str, Tag]` — tag index by name.
- `Graph.out_edges`, `in_edges`, `aliases` — adjacency and alias indexes.
- `Graph.fts: sqlite3.Connection` — in-memory `:memory:` SQLite with one FTS5 virtual table populated at startup. BM25 scoring runs here.
- `Graph.minhash: dict[str, bytes]` — per-doc 128-permutation signatures in RAM.

Cold-start budget at 1000 docs:

- Walk + body load: ~150 ms (read ~5 MB from SSD).
- FTS5 populate: ~500 ms.
- MinHash compute: ~50 s (dominant cost).
- Pairwise MinHash for `:related`: ~100 ms.
- Total: ~50 s for 1000 docs, ~5 s for 100 docs, ~5 min for 5000 docs.

For a long-running MCP server (start once per session, run for hours), the 50 s startup is acceptable.

## Why this collapses cleanly

- Identity = path. Edges store paths. Wikilinks resolve to paths. No surrogate-key resolution layer. The cost is rename — a path-as-id system pays grep-and-rewrite on rename. Aliases catch the most common case (a wikilink whose target was renamed).
- No sidecars. The corpus is the source; the graph is the projection. Throw the projection away whenever — it rebuilds from the corpus in seconds.
- No CRUD tools. Claude Code's existing file tools (`Write`, `Edit`, `Bash`) do everything a CRUD surface would. The `/hoplite` skill teaches the file shape, the location convention, the wikilink rules. Discipline lives in the protocol, not in tool signatures.
- No retrieval tools. `match_nodes` and `traverse_nodes` return paths plus summaries plus tags. The agent uses `Read` to fetch content. Hoplite returns small candidate records; Read returns bodies. Clean role split.
- Four tools, not eleven. The reduction tracks the responsibility reduction: Hoplite is the query index, nothing else.

## Decisions captured

- Hoplite is dataview over the corpus. Inspired by the Obsidian Dataview plugin pattern: the corpus is the source of truth; the query layer is a derived view that returns landings, not content.
- All derived state in memory. The only persistence is the `.md` files. This retires the cache-invalidation problem the SQLite-hybrid still had under the hood — when there is no cache, there is no invalidation.
- `:memory:` SQLite as a runtime detail. SQLite returns as a dependency, but only as an in-memory FTS5 engine for BM25 scoring. Files remain the source of truth; SQLite is a derived index that rebuilds at startup.
- Reindex defaults to auto-detect. The MCP server stat-and-content-hashes documents on each query and rebuilds the index when divergence shows. `hoplite_reindex()` exists as an explicit-trigger escape hatch.
- Dump tool ships day one. `hoplite_dump_index(path?)` snapshots the in-memory state to a SQLite file for developer debugging. The dump is the developer-facing window into what the in-memory graph actually contains.

## What this collapsed

The label-driven framing envelope concept dies in this session. The three framing-axis labels (`instruction`, `reference`, `observation`) lose any special status. The envelope files retire. The `apply_framing` tool retires. The verb-is-the-intent (`invoke` vs `read`) distinction retires.

The thinking that produced framings was right for a graph runtime *that retrieves bodies*. Once Claude's built-in `Read` handles retrieval, the agent is reading the file directly with no Hoplite-applied envelope in the middle. Framings stop being load-bearing because Hoplite stops being the content surface.

## What surprised me

Cutting tools simplified things faster than adding them ever did. Each retirement freed a layer of design questions — what envelope shape, what verb mapping, what label vocabulary, what response composition. The 4-tool surface is what fits cleanly in the head; the 11-tool surface required ongoing rereading of the spec to keep oriented.

The 50 s cold-start cost felt expensive on paper. In practice the MCP server runs for the length of a session — a 50 s warmup once, then sub-millisecond queries for hours. The cost shape matched the use shape; the persistent-cache mechanism the SQLite-hybrid kept on hand was preventing a problem that didn't exist.

## Cross-references

- `[[journal/2026-05-24-0411-sqlite-hybrid-wins-file-based-dropped]]` — the day-old design that got superseded.
- `[[decision-log]]` — the full record of the supersession trail.
- `[[refactor-ids-and-metadata]]` — the intermediate-identity snapshot.

## Next

The venv bootstrap dance for plugin install starts the same morning. SessionStart hook, launch.py dispatcher, race defenses. See `[[journal/2026-05-25-0413-venv-bootstrap-race]]`.
