# Refactor: surrogate ids and explicit metadata

[SUPERSEDED — see [decision-log.md](decision-log.md)]

This document captures an intermediate point in a longer design pivot. The "Decisions locked in" section below was the working snapshot at the time of writing; many of those decisions evolved further in subsequent turns. The current canonical record lives in [decision-log.md](decision-log.md), which traces the full design trail with supersession markers. Among the changes after this document was written:

- ULIDs and the three-tier identity model were abandoned. Identity collapsed to a single tier: the document path. Aliases handle rename continuity.
- SQLite as persistent storage was dropped. The runtime is now fully in-memory; SQLite returns only as an in-memory FTS5 index for BM25 scoring.
- The 11-tool MCP surface collapsed to 4 query tools (no CRUD, no retrieval). Agents write `.md` files through their own file tools.
- Labels and tags un-collapsed; Hoplite is schemaless. Only tags exist; no Neo4j-style label-as-type-discriminator concept.
- Sidecars permanently dismissed. Frontmatter holds all authored metadata.

Treat this document as archival session history. Read [decision-log.md](decision-log.md) for what's actually locked in.

## Motivation

A sub-agent asked a clarification question about parsing the title from a body's line-1 H1. That surfaced a real defect — some documents in the corpus have no H1. Two adjacent realizations followed.

First, the body-shape contract (H1 on line 1, blank on line 2, summary on line 3, blank on line 4) collapses three concerns — title, summary, content — into one string. The shape works for prose notes that lead with a claim and a gloss. It breaks for code snippets, transcripts, tables, and fragments. Title and summary belong as first-class Node fields supplied by the agent at write time.

Second, the path-shaped id grammar `<segment>(/<segment>)*.<ext>` makes the id a natural key — derivable from the filename, mutable as the filename mutates. Edges that reference natural-key ids break when nodes move or rename. Surrogate keys (ULIDs) decouple identity from presentation: titles, filenames, labels, and bodies mutate freely without breaking the graph.

## Decisions locked in

1. Explicit metadata — title and summary become explicit parameters on the write tools. Body has no shape contract.
2. YAML frontmatter on disk — the `.md` file carries metadata in a YAML envelope at the top; body follows. Hand-edits to the frontmatter survive `hoplite_index_node`.
3. Three-tier identity:
   - `INTEGER PRIMARY KEY` — storage mechanism, drives joins, never crosses the tool API.
   - ULID — domain identifier. Edges reference it. Tools pass it. Wikilinks resolve to it.
   - Filename — presentation property, mutable, stored as a column.
4. Server generates ULIDs — `hoplite_insert_node` mints the ULID and returns it in `WriteResult`. The agent supplies title, summary, body, filename, and labels.
5. Agent picks the filename — slugify is encouraged (`hoplite_slugify_text` remains available) but not enforced. The server checks for collisions and rejects on conflict.
6. Wikilinks carry titles — the agent doesn't know the ULID of a target it didn't just create, so wikilinks in body text use the title form `[[Some title]]`. The indexer resolves title → ULID at parse time. Resolution policy is open — see the wikilinks mini-session.
7. `ids.py` splits and partly deletes:
   - `ulids.py` — owns ULID validation, possibly generation.
   - `slugify.py` — owns `slugify_text` moved verbatim.
   - `resolve` — deletes. Filename-to-path becomes `corpus_root / "docs" / filename`; ULID-to-Node becomes a `storage.py` lookup.
8. Spec rewrite precedes code rewrite — the four contract docs and the orchestrator skill rewrite first; the code follows mechanically.

## Open questions

### Labels — drop or repurpose?

The current auto-derive rules pull labels from the leading path segment (`journal/...` → `journal`) and the ISO-date filename prefix (`2026-05-24-...` → `2026-05-24`). With surrogate ids and mutable filenames, those sources are no longer stable. Two paths:

- Drop — the agent supplies the full label set explicitly. Simplest contract; biggest agent burden.
- Repurpose — the agent supplies `category` and `created_date` as explicit parameters; the indexer attaches them as labels. Same outcome as today, source moved from filename-shape to tool argument.

Mini-session pending.

### Wikilinks — four sub-questions

1. Title uniqueness — two nodes with the same title. Reject the second write? Allow duplicates with a disambiguation suffix? Allow duplicates and accept ambiguous wikilinks?
2. Case sensitivity — `[[Skill Composition]]` and `[[skill composition]]`. Same target or different?
3. Forward references — a body wikilinks a title that doesn't exist yet. Reject the write? Accept and leave a dangling edge? Accept and lazily resolve when the target appears?
4. Renames — a node's title changes; bodies of referring nodes still hold the old title. Server rewrites them? Refuses the rename? Re-resolves edges at index time and leaves stale text in bodies?

Mini-session pending.

### ULID lookup for existing nodes

The agent gets ULIDs from three sources today: `match_nodes` / `traverse_nodes` results, `insert_node` `WriteResult`, and `read_node` / `invoke_node` results. None covers "I know the filename, I need the ULID." Options:

- Add `hoplite_resolve_filename(filename) -> ulid` as an eleventh tool.
- Let `read_node` and other read tools accept either ULID or filename.
- Require the agent to call `match_nodes` first.

## Affected surface

### Code

- `ids.py` — deletes. Replaced by `ulids.py` and `slugify.py`.
- `wikilinks.py` (shipped) — extraction logic survives. Callers now expect titles inside `[[ ]]` instead of path-shaped ids. The `:mentions` edge generation moves through a title-resolution layer.
- `labels.py` (unstarted) — rescoped pending the labels mini-session.
- `body.py` (unstarted) → `frontmatter.py` — parses the YAML envelope, returns `(title, summary, body_text)`. Body proper has no shape requirements.
- `models.py` — Node gains `title`, `ulid`, `filename` fields; loses path-derived id.
- `tools.py` — write-tool signatures gain `title` and `summary` (and possibly `filename`, `category`, `created_date` depending on label decisions). ULID-keyed everywhere on the read side.
- `parser.py`, `filtering.py`, `minhash.py` — unaffected.
- `server.py` — scaffolding unaffected.

### Spec

- `behavior.md` — rewrites: id grammar (ULID format), label rules (TBD), rejected-writes (frontmatter shape replaces body shape), envelope composition unchanged, edge vocabulary unchanged.
- `data-model.md` — Node shape gains `title`, `ulid`, `filename`.
- `tool-api.md` — write-tool signatures gain `title` and `summary`; read-tool returns add `title`; identity column changes from `id: str` to `ulid: str`.
- `implementation-plan.md` — phase 1 module list and recommended next slice update.
- `/hoplite` orchestrator skill — writing protocol instructs the agent to supply title and summary explicitly; reading protocol clarifies that the agent receives ULIDs and treats them opaquely.

## Order of work

1. Labels mini-session.
2. Wikilinks mini-session.
3. Spec rewrite — `behavior.md`, `data-model.md`, `tool-api.md`, `implementation-plan.md`, `/hoplite` skill body.
4. Code rewrite — `ulids.py`, `slugify.py`, delete `ids.py`, then `frontmatter.py` and `labels.py` per the new contracts.
