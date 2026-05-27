---
title: FTS5 rowid bug and timestamped dump filenames
summary: hoplite_dump_index returned wrong paths because FTS5's rowid was independent of documents.id; binding rowid to documents.id fixed the path resolution. Default dump filename gains an ISO timestamp so prior dumps survive on disk.
tags: [journal, hoplite, mcp, fts5, bug-fix]
created: 2026-05-25
aliases: []
---

# FTS5 rowid bug and timestamped dump filenames

`hoplite_dump_index` returned wrong paths because FTS5's rowid was independent of `documents.id`; binding rowid to `documents.id` fixed the path resolution. Default dump filename gains an ISO timestamp so prior dumps survive on disk.

## The bug

The dump command lets a developer snapshot the in-memory graph to a SQLite file and run arbitrary SQL against it. Useful for "why did this query return that result." The dump's `documents_fts` virtual table was a contentless FTS5 mirror — body and summary tokenized for BM25 scoring, content rows stored on the canonical `documents` table.

The defect: contentless FTS5's rowid auto-increments independently of any external table. When the walker populated `documents_fts` row by row, FTS5 assigned `rowid = 1, 2, 3, ...` in insertion order, with no relationship to the `documents.id` values they were supposed to mirror. The join in dump queries — `JOIN documents ON documents.id = documents_fts.rowid` — returned wrong rows.

The symptom: BM25 scoring would surface correct hits during normal `match_nodes` calls (the in-memory path used the matched rowid to look up the document directly), but the dump SQL would resolve those same rowids to the wrong `documents` rows. A query for "show me the top 10 hits and their paths" returned paths that did not match the bodies.

## The fix

Bind the FTS5 rowid to `documents.id` explicitly on insert. Instead of `INSERT INTO documents_fts(body, summary) VALUES (?, ?)`, the insert becomes `INSERT INTO documents_fts(rowid, body, summary) VALUES (?, ?, ?)` with the `documents.id` passed as the rowid. The FTS5 rowid now equals the documents.id; the join resolves correctly.

## What landed

- 2026-05-25 17:09 — Hoplite dump: bind FTS5 rowid to `documents.id` so paths resolve. The fix.
- 2026-05-25 17:21 — `hoplite_dump_index`: timestamped default filename. Default destination changes from `.hoplite/index.sqlite` to `.hoplite/<ISO-timestamp>.index.sqlite`. Each dump produces a uniquely-named file; prior dumps survive on disk for comparison.
- 2026-05-25 17:24 — Roadmap: columnar projection for multi-property predicates. Recognition that multi-property tag queries (`tags has 'a' AND tags has 'b'`) would benefit from a columnar projection pass; recorded for later.

## Decisions captured

- Contentless FTS5 needs explicit rowid binding. The convenience-default of auto-incrementing rowid breaks any consumer that wants to join through it. Always bind rowid to the canonical id on insert.
- Dumps are diagnostic artifacts that compound. Timestamped filenames let the developer keep a history of dumps without one overwriting another. "What did the graph look like before I changed X?" gets answered by reading the older dump.
- The dump is the developer-facing window into the in-memory graph. If the dump returns wrong joins, the diagnostic tool is misleading. Bug in the dump path is at least as bad as a bug in the query path because it corrupts the debugging loop.

## What this surfaced

The defect was latent for ~6 hours — the in-memory query path didn't exercise the rowid join. The first call that actually depended on the join was a developer exploration in `sqlite3` on a dump file. The bug was real but only visible from the developer-debugging vantage; production usage stayed clean.

A test for the dump's row-resolution would have caught it. The test suite at this point covered `match_nodes` and `traverse_nodes` end-to-end but did not assert against dump structure. Adding dump-shape tests is roadmap work.

## Cross-references

- `[[journal/2026-05-25-1137-eav-property-graph-refactor]]` — the EAV refactor that introduced the contentless FTS5 pattern this bug lived in.

## Next

Traverse-tool tests, version bump to 1.0.0, README rewrite. See `[[journal/2026-05-25-1836-tests-1-0-0-and-readme-rewrite]]`.
