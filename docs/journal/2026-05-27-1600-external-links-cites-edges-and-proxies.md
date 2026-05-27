---
title: External links — cites edges from inline markdown links, proxies for durable refs
summary: Picked the middle ground for external references. Inline `[text](url)` markdown links auto-index as `cites` edges to URL-keyed graph nodes; durable refs that earn metadata get a proxy note at `docs/proxies/<slug>.md`. Rejected wikilink-the-URL (renders as literal `[[https://...]]` everywhere outside Hoplite) and proxy-only (ceremony tax on casual mentions).
tags: [journal, hoplite, wikilinks, decision]
created: 2026-05-27
---

# External links — cites edges from inline markdown links, proxies for durable refs

Picked the middle ground for external references. Inline `[text](url)` markdown links auto-index as `cites` edges to URL-keyed graph nodes; durable refs that earn metadata get a proxy note at `docs/proxies/<slug>.md`. Rejected wikilink-the-URL (renders as literal `[[https://...]]` everywhere outside Hoplite) and proxy-only (ceremony tax on casual mentions).

## Context

Coming out of the wikilinks Part 1 refactor (commits `0dc018e`, `860f729`, `3cd15a2`), every wikilink has to start with `docs/` or `ghost/` — the walker rejects anything else. That left external references with no first-class shape. The trigger was a stale ghost in the export: `ghost/notes/karpathy-llm-wiki`, intended as a pointer to Karpathy's LLM-wiki gist, which the corpus had no idiomatic way to cite.

## Three options weighed

1. **Wikilink-the-URL** — `[[https://gist.github.com/...]]`. Cheap to author, graph-indexed. Fatal flaw: doesn't render as a clickable link in Obsidian, GitHub, or any IDE markdown preview — the reader sees literal wikilink syntax. Also: no metadata on the node, URL-as-graph-key is brittle, and inline prose with a 60-character wikilink reads worse than a slug.

2. **Proxy-only** — every external URL goes through a `docs/proxies/<slug>.md` note that wraps the URL with context. Clean, metadata-rich, one source of truth per resource. Cost: ceremony. A journal entry mentioning "I tried this Stack Overflow answer" doesn't earn a whole new file; the friction pushes contributors to bypass the rule.

3. **Middle ground** — keep inline `[text](url)` markdown links and teach the walker to index them too. Add `docs/proxies/` for the cases that earn metadata. Two mechanisms compose: inline links catch casual citations for free; proxies hold metadata and a backlink hub for durable refs.

## Decision

Ship the middle ground. The proxy convention is structurally right where it earns its keep; mandating it everywhere collapses to over-ceremony. Inline markdown links keep rendering clickable in every markdown viewer, get backlink-discoverable through `cites` edges, and require zero author work.

Edge kind: a new `cites` value alongside `mentions` and `related`. Letting callers filter `relatives(predicate={"edge_types": ["cites"]})` to see only external citations is the kind of query that's clearer with a dedicated kind than with a property on `mentions`.

## What shipped

- New module `plugins/hoplite/mcp/src/hoplite/urls.py`, parallel to `wikilinks.py`. Same `_mask_code` strategy: skip code spans and fenced blocks so sample URLs in prose don't pollute the graph. Duplicate the masking helper rather than share it — two short copies beat a shared dependency between siblings.
- Walker pass 2 in `graph.py` emits a `cites` edge for each unique URL. Nodes stored verbatim (no canonicalization — different fragments produce different nodes; author authority).
- URL nodes carry `resolved=false`, no FTS row, no body. Terminal — discoverable through `relatives`, never through `where` text search.
- `WriteResult.counts` gains a `urls` key so the categories — documents, ghosts, urls, edges — stay distinct in exports.
- `docs/proxies/karpathy-llm-wiki.md` is the first proxy. The Karpathy ghost from Part 1 is gone; the file now lives at `docs/proxies/` and holds both the human-facing gist URL and the raw-markdown URL plus context.

## Out of scope

Autolinks (`<https://...>`), bare URLs in prose, URL canonicalization, and link health checks all deferred. The matched-pair `[text](url)` form is enough surface area to absorb every real-world citation; bare URLs and autolinks are easy adds when a case for them appears.

## See also

- [[docs/hoplite/architecture.md]] — external references subsection added under wikilinks and ghost documents.
- [[docs/proxies/karpathy-llm-wiki.md]] — first proxy note in the corpus.
- [[docs/journal/2026-05-25-2252-venv-bootstrap-follows-the-canonical-pattern.md]] — adjacent earlier entry that surfaced the original karpathy ghost reference.
