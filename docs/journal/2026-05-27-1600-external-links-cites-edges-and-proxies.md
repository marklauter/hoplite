---
title: Wikilinks arc — full convention, external refs, schema mirror
summary: One session, one arc — wikilinks went from a broken regex with garbage ghosts to a strict two-prefix convention with full repo-relative paths, validated targets, and explicit open loops. External references gained a `cites` edge kind from inline markdown links plus a `docs/proxies/` convention for durable refs. The dump schema collapsed to mirror the in-memory shape one-to-one. Each step landed cleanly because the previous one cleared the question it raised.
tags: [journal, wikilinks, decision, session-summary]
created: 2026-05-27
---

# Wikilinks arc — full convention, external refs, schema mirror

One session, one arc — wikilinks went from a broken regex with garbage ghosts to a strict two-prefix convention with full repo-relative paths, validated targets, and explicit open loops. External references gained a `cites` edge kind from inline markdown links plus a `docs/proxies/` convention for durable refs. The dump schema collapsed to mirror the in-memory shape one-to-one. Each step landed cleanly because the previous one cleared the question it raised.

## The arc

- **Alias/anchor stripping in the resolver** (`0dc018e`) — `[[hoplite/roadmap]]` and `[[X#section]]` no longer materialize ghost paths carrying raw display syntax. Resolution slices on `|` and `#` before lookup.
- **Code-span and fenced-block exclusion** (`860f729`) — sample wikilinks inside backticks stop ghosting. Authoring rule: samples wear backticks; extractor honors it.
- **Full `docs/...md` paths in wikilinks and query results** (`3cd15a2`) — walker computes paths relative to `corpus_root.parent`; stored keys and returned `path` fields carry the `docs/` segment so an agent can `Read` directly without rebasing.
- **Explicit `ghost/<slug>` for intentional open loops** (`3cd15a2`) — walker rejects any target not starting with `docs/` or `ghost/`; malformed links surface as `WriteResult.warnings` rather than silent garbage.
- **`cites` edges from inline `[text](url)` markdown links** (`92923be`) — new `urls.py` extractor parallel to `wikilinks.py`; URL nodes keyed by the verbatim URL with `resolved=false` and no FTS row. Casual external citations index for free.
- **`docs/proxies/` for durable external references** (`92923be`) — proxy notes carry metadata, tags, and the URL via a markdown link. Karpathy's gist is the first proxy.
- **Synthetic `ghost`/`url` tags + tag-only `where` over unresolved nodes** (`8179468`) — `where({"tagged": "url"})` enumerates every external URL; `where({"tagged": "ghost"})` enumerates every open loop. The two categories that lacked FTS rows are now enumerable through the same predicate surface.
- **Dump schema mirrors the in-memory shape one-to-one** (`64551c3`) — dropped the `nodes(id, kind)` polymorphic root and every synthetic integer ID; `documents` keys on `path`, `edges` on `(src, dst, kind)`. The export is now a faithful view of memory state, not a different model.
- **`node_properties` → `document_properties`** (`01ce906`) — the `node` name was a vestige of the dropped polymorphism; renamed to match what the table actually holds.
- **Contentless-FTS regression caught and fixed** — the dump's `content = ''` discarded the `UNINDEXED path` column too, so FTS rows came back all NULL after the schema collapse. Dropped contentless mode; FTS now joins back to documents via the natural `path` key.

## Context

The arc opened with the catalog export showing 31 ghost documents — a mix of intentional open loops, code fragments parsed as wikilinks, alias-leaked display syntax, and ordinary typos all jumbled into the same `resolved=false` bucket. Pulling at one thread (why does `hoplite/roadmap|roadmap.md` exist as a ghost when `docs/specs/hoplite-roadmap.md` is a real file?) unraveled into the full convention shift. The cites-edges/proxies decision was the centerpiece; the schema collapse was the cleanup that followed once the rest was stable.

The original Part 1 trigger was a stale ghost: `ghost/notes/karpathy-llm-wiki`, intended as a pointer to Karpathy's LLM-wiki gist, which the corpus had no idiomatic way to cite. Resolving that one ghost forced both the strict wikilink rules (Part 1) and the external-reference design (Part 2).

## Three options weighed

1. **Wikilink-the-URL** — `[[https://gist.github.com/...]]`. Cheap to author, graph-indexed. Fatal flaw: doesn't render as a clickable link in Obsidian, GitHub, or any IDE markdown preview — the reader sees literal wikilink syntax. Also: no metadata on the node, URL-as-graph-key is brittle, and inline prose with a 60-character wikilink reads worse than a slug.

2. **Proxy-only** — every external URL goes through a `docs/proxies/<slug>.md` note that wraps the URL with context. Clean, metadata-rich, one source of truth per resource. Cost: ceremony. A journal entry mentioning "I tried this Stack Overflow answer" doesn't earn a whole new file; the friction pushes contributors to bypass the rule.

3. **Middle ground** — keep inline `[text](url)` markdown links and teach the walker to index them too. Add `docs/proxies/` for the cases that earn metadata. Two mechanisms compose: inline links catch casual citations for free; proxies hold metadata and a backlink hub for durable refs.

## Decision

Ship the middle ground. The proxy convention is structurally right where it earns its keep; mandating it everywhere collapses to over-ceremony. Inline markdown links keep rendering clickable in every markdown viewer, get backlink-discoverable through `cites` edges, and require zero author work.

Edge kind: a new `cites` value alongside `mentions` and `related`. Letting callers filter `relatives(predicate={"edge_types": ["cites"]})` to see only external citations is the kind of query that's clearer with a dedicated kind than with a property on `mentions`.

## What shipped (cites edges and proxies)

- New module `plugins/hoplite/mcp/src/hoplite/urls.py`, parallel to `wikilinks.py`. Same `_mask_code` strategy: skip code spans and fenced blocks so sample URLs in prose don't pollute the graph. Duplicate the masking helper rather than share it — two short copies beat a shared dependency between siblings.
- Walker pass 2 in `graph.py` emits a `cites` edge for each unique URL. Nodes stored verbatim (no canonicalization — different fragments produce different nodes; author authority).
- URL nodes carry `resolved=false`, no FTS row, no body. Terminal — discoverable through `relatives`, never through `where` text search.
- `WriteResult.counts` gains a `urls` key so the categories — documents, ghosts, urls, edges — stay distinct in exports.
- `docs/proxies/karpathy-llm-wiki.md` is the first proxy. The Karpathy ghost from Part 1 is gone; the file now lives at `docs/proxies/` and holds both the human-facing gist URL and the raw-markdown URL plus context.

## Schema collapse — the export mirrors memory

The cites/proxies work made the schema asymmetry visible: the in-memory `Graph` carries one `documents` collection keyed by path, but the dump projected it through a `nodes(id, kind)` polymorphic root with synthetic integer IDs. The `kind` discriminator was always `'document'`. Dead-weight indirection paying for polymorphism that never arrived.

Collapsed it. `documents.path` is the natural key throughout the dump — `node_properties` (renamed to `document_properties`) keys on `path`, `edges` on `(src, dst, kind)`, `edge_properties` carries the same composite as the edge it annotates. No `nodes` table, no synthetic IDs, no `node_ids`/`edge_ids` allocation passes in the writer. SQL reads natural: `select dst from edges where src = 'docs/notes/foo.md'`. The export is a view of memory state; reading the runtime code and the dump schema teaches one model.

Path-prefix discriminator (`docs/`, `ghost/`, `http(s)://`) does the kind-of-node job at both layers. The day a node kind earns its own columns, add a specialization table then.

## Regression caught: contentless FTS

The schema collapse removed the integer rowid linkage between the dump's FTS table and `documents`. The FTS was still declared `content = ''` (contentless mode), which discards every column value after building the inverted index — including `UNINDEXED path`. Net result: FTS was queryable via MATCH but every column read came back NULL, and there was no rowid to join on either.

Dropped `content = ''`. The `path UNINDEXED` column now survives the dump and joins back to `documents.path` directly. Per-row cost: empty body strings stored explicitly (the runtime already passes `""` for body). Caught because the other agent ran a SELECT against the FTS rowids and surfaced the NULLs.

## Out of scope

Autolinks (`<https://...>`), bare URLs in prose, URL canonicalization, and link health checks all deferred. The matched-pair `[text](url)` form is enough surface area to absorb every real-world citation; bare URLs and autolinks are easy adds when a case for them appears. Polymorphic node-kind specialization tables deferred until a kind earns columns of its own.

## See also

- [[docs/specs/hoplite-architecture.md]] — wikilinks, ghost documents, external references, and the dump-schema section all rewritten across the arc.
- [[docs/proxies/karpathy-llm-wiki.md]] — first proxy note in the corpus.
- [[docs/todos/wikilink-resolver-leaves-alias-and-anchor-in-the-target.md]] — the note that opened the arc.
- [[docs/journal/2026-05-25-2252-venv-bootstrap-follows-the-canonical-pattern.md]] — adjacent earlier entry that surfaced the original karpathy ghost reference.
