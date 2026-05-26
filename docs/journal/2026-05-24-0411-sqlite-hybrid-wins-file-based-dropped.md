---
title: SQLite-hybrid wins; file-based dropped; paths-as-ids; hoplite naming
summary: SQLite-hybrid lands as a peer implementation to the file-based design, then displaces it as the day-one target; storage restructures so docs/ holds content and .hoplite/ holds the index; paths become the natural-key identity; the package renames hoplite_mcp; label expressions land on match and traverse.
tags: [journal, hoplite, mcp, sqlite, architecture, milestone]
created: 2026-05-24
aliases: []
---

# SQLite-hybrid wins; file-based dropped; paths-as-ids; hoplite naming

SQLite-hybrid lands as a peer implementation to the file-based design, then displaces it as the day-one target; storage restructures so `docs/` holds content and `.hoplite/` holds the index; paths become the natural-key identity; the package renames `hoplite_mcp`; label expressions land on `match` and `traverse`.

## Intent

The data-model spec from the prior day declared per-node YAML sidecars in a flat directory, label folders with empty marker files, and label envelope files. Functional, but several concerns surfaced when reading it back:

- A query for "all nodes with label X" is O(N file reads) without an index. Per the spec, a `_meta.json` cache would handle the common case. Carrying a cache file invites the cache-invalidation problems the file-based design was trying to avoid.
- BM25 scoring over a corpus of thousands needed an inverted index. The spec deferred this. Deferral past day-one was suspicious.
- Atomic cross-file writes were best-effort with a future write-ahead journal. Two-file invariants across sidecar + marker were already fragile.

The case for SQLite as the index layer: a real database under the hood, ACID semantics for the index writes, FTS5 for BM25, an inverted index for free. The files-as-source-of-truth property stays — the database is derived, rebuildable from the corpus.

## What landed (chronological)

- 2026-05-23 18:45 — Add SQLite-hybrid implementation as a peer alternative to file-based. The two designs coexist in the spec for a few hours so the comparison is concrete rather than abstract.
- 2026-05-24 00:24 — Specify WAL mode and companion PRAGMAs in the SQLite-hybrid spec. WAL for concurrent reads while a write is in flight, plus `synchronous=NORMAL`, `temp_store=MEMORY`, `mmap_size` for the read path.
- 2026-05-24 01:25 — Drop file-based; SQLite-hybrid is the day-one build target. The peer-alternative comparison closed.
- 2026-05-24 02:20 — Restructure id and storage: `docs/` for content, `.graph/` for index, paths-as-ids. ULIDs and surrogate keys retire; the document's path becomes its natural-key identity. Edges reference paths. Wikilinks resolve to paths. Renames are expensive (grep-and-rewrite) but every other operation gets simpler.
- 2026-05-24 02:25 — Extract deferred items to `roadmap.md`; tighten day-one specs. Move pagination, embeddings, multi-writer support, reindex scheduling — everything not day-one — out of the contract docs into a roadmap so day-one stays a small, shippable target.
- 2026-05-24 02:43 — Add MCP tool hints (`readOnly`/`destructive`/`idempotent`/`openWorld`) to `tool-api`. Hints help downstream clients reason about what each tool does without parsing the description prose.
- 2026-05-24 02:44 — Add pagination for `match` and `traverse` to roadmap.
- 2026-05-24 03:31 — Rename to `hoplite_mcp`; address findings from review. The package gets its real name.
- 2026-05-24 03:52 — Add label expressions to `match` and `traverse`; frame DSL question on roadmap. Predicates gain boolean composition over labels — `notes & mcp`, `(notes | journal) & !draft`. The full DSL surface gets deferred to roadmap; day-one ships a recognizable subset.
- 2026-05-24 03:55 — Reframe pagination as an open question in roadmap, parallel to the DSL question.
- 2026-05-24 03:58 — Sweep outstanding files: mcp-skill reference docs, hoplite logo, server stub, gitignore additions.
- 2026-05-24 04:01 — Fix stale predicate examples in `orchestrator-skill.md`.
- 2026-05-24 04:03 — Rename index directory `hoplite/` → `.hoplite/` (hidden). Convention alignment with `.git/`, `.obsidian/`.
- 2026-05-24 04:11 — Finished. Day-one shape stable; spec sweep complete.

## Decisions captured

- SQLite for the index, files for the source of truth. The database is derived; the corpus is authoritative. Rebuild the database from files at any time. This split survives the next two days; it ends up reshaped (in-memory SQLite instead of on-disk) but the principle holds.
- Paths-as-ids. Identity collapses to one tier. Edges reference paths. Renames pay a real cost (grep-and-rewrite); every other operation pays less. This decision retires the ULID + three-tier identity work from the spec, including the `ids.py` module that gets ripped out the next day.
- `.hoplite/` for the index directory. Hidden by convention, ignored by default in tooling that respects dot-directories. The choice mirrors `.git/`.
- Hoplite is the name. The package gets `hoplite_mcp`; the project is Hoplite. (The package name later loses the `_mcp` suffix; the project name stays.)
- Label expressions are day-one. A boolean predicate over labels is small enough to ship in the recognizable subset; the question of how far the DSL grows is roadmap material, not day-one material.

## What this set up

- The next session draws the line between the spec and the code. Spec is stable; time to write Python. The Python toolchain (`writing-python` skill, ruff + pyright gate, src/tests layout) lands the same day. See `[[2026-05-24-1701-python-toolchain-and-writing-python-skill]]`.
- The decision-log file grows. SQLite-hybrid wins gets recorded; ULIDs get marked superseded; the three-tier identity model gets marked superseded.

## What this didn't survive

The SQLite-hybrid wins for ~24 hours. On the night of 2026-05-24 the architecture pivots again: persistent SQLite drops in favor of in-memory `:memory:` SQLite for FTS5 only. The hybrid name retires. See `[[2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]`.

The paths-as-ids decision survives the redesign and ships in day-one.

## Next

The Python toolchain lands and the first hoplite modules start. See `[[2026-05-24-1701-python-toolchain-and-writing-python-skill]]`.
