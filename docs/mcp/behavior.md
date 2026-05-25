---
title: Behavior
summary: "[Contract] Frontmatter shape, wikilink resolution, tag predicates, edge derivation, reindex semantics, and the error model — pure behavioral spec."
tags: [hoplite, mcp, contract, behavior]
created: 2026-05-25
aliases: []
---

## Overview

Hoplite reads a corpus of markdown files at the MCP server's working directory, builds an in-memory graph from frontmatter and body content at startup, and serves four query tools over the graph. The `.md` files are the only persistent state; everything else is derived. Hand-edits to files round-trip through `hoplite_reindex`; humans editing in Obsidian and agents writing through `Write` are indistinguishable from Hoplite's view.

The behavior contract covers: what frontmatter must contain, how wikilinks resolve, what edges materialize and when, how tag predicates filter results, when changes get picked up, and what errors look like.

## Frontmatter

Every document carries a YAML frontmatter block delimited by `---` fences at the top of the file. Five fields are mandatory; arbitrary user-defined fields pass through unchanged.

Mandatory fields:

- `title` (string) — short, human-readable name.
- `summary` (string) — one-line lede.
- `tags` (list of strings) — tag slugs the document carries. Empty list allowed (`tags: []`).
- `created` (ISO date string, `YYYY-MM-DD`) — creation date.
- `aliases` (list of strings) — alternate paths that resolve to this document. Empty list allowed.

User-defined fields:

Arbitrary YAML keys beyond the mandatory five pass through unchanged. Hoplite reads and stores them; it doesn't act on them. They're available for user queries and for external tools (Obsidian, Dataview). Example user fields: `status: draft`, `priority: high`, `due: 2026-06-01`.

`updated` is intentionally absent from frontmatter. The modification timestamp derives from git history when callers need it — `mtime` lies after git checkouts and file copies, frontmatter can drift from reality, git is the source of truth for file change history.

### Frontmatter parse failures

A document with a missing or unparseable frontmatter block is reported as a warning in the `hoplite_reindex` result and skipped from the in-memory graph. It doesn't crash the indexer. Fix the file's frontmatter and re-run reindex to include it.

A document with the frontmatter block intact but missing a mandatory field is also reported as a warning and skipped. The walker doesn't synthesize defaults; the contract is "all five mandatory fields, or you're not indexed."

## Wikilinks

Body text uses Obsidian's wikilink syntax: `[[target]]`. The `target` is a path relative to the corpus root (with or without the `.md` extension) or an alias declared in some document's `aliases` list. Resolution is case-insensitive ordinal (`str.casefold()`-equivalent) — `[[Notes/Foo.MD]]`, `[[notes/foo.md]]`, and `[[NOTES/foo.MD]]` all resolve to the same target.

The walker emits a `:mentions` edge for every wikilink it finds in a body, carrying the source document's path and the wikilink's line and column for locating dangling links later.

### Forward references and ghost documents

A wikilink whose target doesn't yet exist on disk resolves to a **ghost document** — a first-class graph entity with `resolved = false` and no body content. Inbound `:mentions` edges point at the ghost as if it were a real document.

When a document at the matching path is later added (and reindex runs), the ghost is promoted in place: identity stays stable, content fields fill in, every inbound edge already points at the right node. The set of unresolved documents is queryable as an "open loops" view — documents referenced but not yet written.

Wikilinks are never silently dropped. A target that doesn't exist on disk becomes a ghost; a target that does exist resolves to the real document. Either way an edge materializes.

## Tags

Tags are free-form annotations. Document frontmatter carries a list of tag slugs; the walker materializes a `member` edge from each tag to each document that carries it.

Tag naming is convention, not enforcement. Hoplite stores tag slugs verbatim from frontmatter; the `/hoplite` skill teaches kebab-case (`graph-db`, `system-design`) so authored content stays consistent and case-insensitive lookup works as expected. There's no auto-derived tag — tags come from the agent or user explicitly.

Tag membership is queryable through the predicate `tagged: <slug>`. See [Tag predicates](#tag-predicates) below.

## Edges

Three edge kinds materialize, closed set. No aspirational types reserved.

- `member` — tag → document. The walker emits one `member` edge per `(tag, doc)` pair where the document's `tags` list contains the tag.
- `mentions` — document → document (real or ghost). The walker emits one `mentions` edge per `(source, target)` pair regardless of how many `[[wikilink]]` occurrences point at the target. Multiple references collapse to a single edge — the graph records relationships, not occurrences.
- `related` — document ↔ document, symmetric. After the walker has computed every document's MinHash signature, a pairwise pass emits a bidirectional `related` edge for every pair whose Jaccard similarity exceeds a configured threshold (default 0.20). Both directions emitted as two edge rows.

Use cases for richer relations (`cites`, `contradicts`, `requires`, `see-also`) express through `mentions` plus body prose. Tag hierarchy doesn't exist day one. See the [data model](data-model.md#edge-vocabulary) for the full field set.

## Tag predicates

Tools that filter by tag membership (`hoplite_match_nodes` and `hoplite_traverse_nodes`) accept a tag predicate — a boolean expression over tag slugs.

Grammar:

```
expr     ::= or_expr
or_expr  ::= and_expr ( '|' and_expr )*
and_expr ::= not_expr ( '&' not_expr )*
not_expr ::= '!' not_expr
           | atom
atom     ::= slug
           | '(' expr ')'
slug     ::= [a-z0-9-]+
```

Operators:

- `&` — intersection. `notes & mcp` selects documents tagged both `notes` and `mcp`.
- `|` — union. `notes | journal` selects documents tagged either.
- `!` — exclusion. `!draft` selects documents not tagged `draft`.
- `(...)` — grouping.

Precedence: `!` binds tightest, then `&`, then `|`. Left-associative. Use parentheses when mixing `&` and `|`.

Examples:

- `notes & mcp` — documents tagged both.
- `(notes | journal) & !draft` — notes or journal entries, excluding drafts.
- `mcp & !2026-05-24` — mcp-tagged docs excluding the ISO-date slug (when an author uses dates as tags).

The bare slug `notes` is itself a valid predicate.

### Tagged-sugar

The wire shape on `hoplite_match_nodes` and `hoplite_traverse_nodes` accepts a `tagged:` sugar. `tagged: graph-db` is equivalent to the predicate `graph-db`. The sugar exists because the user-facing read of `tagged: X` matches Obsidian's tagging convention; internally it compiles to traversal over `member` edges with `src` filtered to the tag slug. See [tool-api.md](tool-api.md#predicates) for the wire format.

### Empty predicate

When the predicate is absent or empty, no tag filter applies. `hoplite_match_nodes` returns the top-`k` BM25 results unfiltered. `hoplite_traverse_nodes` returns every document the edge predicate reaches.

### Semantics — post-filter on results

Predicates apply as post-filter on the result set. For `hoplite_match_nodes`, the predicate narrows the BM25-scored candidate list. For `hoplite_traverse_nodes`, the walk follows edges per the edge predicate; the tag predicate filters which reached documents appear in the result. Non-matching intermediate documents are still traversed through.

## Reindex

`hoplite_reindex()` triggers a fresh corpus walk. The walker:

1. Identity collection — globs `**/*.md`, parses frontmatter, builds the `path → Document` index and the `alias-or-path → canonical-path` lookup. Cheap; just frontmatter.
2. Body load + edges + indexes — reads bodies, parses wikilinks, materializes `mentions` edges (with ghost creation on miss) and `member` edges (from tag lists), populates the in-memory FTS5 virtual table, computes MinHash signatures.
3. Aggregate — pairwise MinHash comparison emits `related` edges above threshold.

The graph is rebuilt from scratch on every reindex call. No incremental updates day one; the cost (~50ms per doc for MinHash, sub-second for everything else at 1000 docs) is small enough that a full rebuild is the simplest correct behavior.

Day one, reindex is the only way to pick up file changes — there's no automatic detection of edits between calls. An agent that writes a file calls `hoplite_reindex()` afterward. Human edits in Obsidian show up after the next reindex call. The aspirational upgrade is per-query stat-checking; see [roadmap.md](roadmap.md).

The server initializes the graph at startup by running the walk implicitly (same as a reindex call). No init tool, no init-mode gate — the graph is ready to serve as soon as the server has finished walking.

## Validation and error model

Two failure modes, distinguished by remediability:

- **Invariant violations throw exceptions.** Programming errors — calls that violate the API contract in ways the caller could have prevented (`None` for a required string, out-of-range integer, malformed predicate string). Throwing surfaces the bug to the caller.
- **Constraint violations return warnings in the result.** Runtime conditions the caller couldn't have known in advance — a document with malformed frontmatter, a wikilink that resolves to a ghost (not strictly an error, but worth surfacing), a `dump_index` destination path that the server can't write to.

At the MCP wire boundary, both failure modes land as content responses. Thrown invariant exceptions become structured error content with `isError: true`; constraint warnings ride along inside successful results in the `warnings` field of `WriteResult` or analogous output shapes. JSON-RPC protocol errors stay reserved for transport failures (malformed requests, connection loss); tool execution failures always come back as content the agent can read.

The four tools have narrow input contracts: `hoplite_match_nodes` and `hoplite_traverse_nodes` reject malformed predicates (parser error) and out-of-range `k` or `depth`; `hoplite_reindex` accepts no parameters; `hoplite_dump_index` rejects unwritable destination paths. No CRUD validation exists — agents write `.md` files directly via their own file tools, and Hoplite picks up whatever's there on the next reindex.
