---
title: Reify the in-memory graph as a file-based SQLite database
summary: The in-memory graph model has stabilized across several iterations; revisit persistent file-based SQLite so cold-start cost stops scaling with corpus size.
tags: [note, todo, sqlite, graph]
created: 2026-05-27
priority: high
effort: high
status: in-progress
---

# Reify the in-memory graph as a file-based SQLite database

The in-memory graph model has stabilized across several iterations; revisit persistent file-based SQLite so cold-start cost stops scaling with corpus size.

## Motivation

Persistence got dropped on 2026-05-25 when the design pivoted from SQLite-hybrid to a `:memory:` SQLite FTS5 engine plus dict-based adjacency. See [[docs/journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools.md]]. The reasoning at the time: a long-running MCP server pays one 50 s warmup per session, then serves sub-millisecond queries for hours. The persistence layer solved a problem that did not exist.

That reasoning held while the corpus was small and the in-memory shape was still settling. Two things have changed.

- Cold-start cost scales with corpus size. The roadmap already flags ~5 min startup at 5000 docs (`docs/hoplite/hoplite-roadmap.md`, MinHash section). The 50 s figure was a day-one budget, not a stable cost.
- The runtime model has held up. Identity-as-path, the four-tool surface, `mentions`/`cites`/`related` edges, the FTS5 + MinHash split: none of these have churned in weeks. The schema is no longer a moving target, so persisting it costs less than it would have during the redesign window.

The prior file-based design already exists as a reference point: `docs/` for content, `.hoplite/` for the index, WAL mode and PRAGMA tuning. See [[docs/journal/2026-05-24-0411-sqlite-hybrid-wins-file-based-dropped.md]]. It got dropped because the cache-invalidation problem was unwanted, not because the storage shape was wrong.

## What persistence would buy

- Sub-second cold start regardless of corpus size. The FTS5 index, MinHash signatures, and edge tables survive process restarts. Reindex runs only on detected divergence.
- Larger corpora become viable without rethinking the runtime. The 5000-doc cliff disappears.
- The existing `export()` debug snapshot becomes the real storage format. The schema is already exercised; promoting it from debug-only to authoritative is incremental.
- Cross-session continuity for any agent that wants to query Hoplite without paying a warmup tax.

## What persistence would cost

- Cache invalidation returns. The 2026-05-25 redesign explicitly retired this problem by making the corpus the only source of truth. Bringing back a persistent index means bringing back stat-and-content-hash divergence checks on every query, or an explicit reindex protocol.
- A second store to keep healthy. `.hoplite/index.sqlite` becomes a real artifact — corruption, partial writes, version drift across schema changes.
- Schema migration overhead. Every change to the in-memory shape now also changes a stored shape.

## Trigger

Worth doing when any of these arrive:

- Corpus pushes past ~2000 docs and cold start becomes noticeable in normal use.
- An agent workflow wants Hoplite as a short-lived process (one query, one exit). The current model makes that prohibitively expensive.
- MinHash gives way to a heavier embedding step that pushes warmup well past one minute.

Until then, the in-memory model is fine. This note exists so the option is visible when the trigger fires.

The trigger fired 2026-05-27 on a different axis than the ones listed above. The user is running many Claude Code windows against the same corpus and wants the graph shared across processes with no per-window cold start. WAL mode plus persistent file storage gives many-readers-one-writer concurrency for free. The execution plan lives at [[docs/notes/db-refactor.md]].

## Resolved

The trigger fired and the work is underway. The execution plan is [[docs/notes/db-refactor.md]]. The open questions resolved as follows.

- Schema designed fresh, not reused from the dump. Storage is authoritative now, so the schema was reworked into `node`/`node_property`/`edge` (interned `edge_kind`)/`edge_property`/`fts`, with `COLLATE NOCASE` doing case-insensitive matching. See `plugins/hoplite/mcp/src/hoplite/schema.sql`.
- Explicit `refresh`, not stat-and-hash on every query. Day-one is truncate-and-rebuild on a manual `refresh`. Divergence-based reconcile is deferred (db-refactor "Held for future").
- The in-memory graph is retired, not kept as a peer. SQLite is the only implementation; there is no Protocol and no two-impl split. [[docs/notes/swap-in-memory-graph-dicts-for-a-property-graph-object-model.md]] is superseded. Its property-graph object model is realized directly in the SQLite schema rather than as an in-memory shape.
