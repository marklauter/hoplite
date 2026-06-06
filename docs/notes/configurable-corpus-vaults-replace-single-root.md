---
title: Configurable corpus vaults replace single-root indexing
summary: tools.set_root binds the index to one corpus root under cwd. Cross-repo knowledge graphs need a configurable collection of corpus vaults indexed into one catalog, with global vocabulary so BM25 IDF spans the union and per-vault tagging stays addressable.
tags: [note, hoplite, mcp, corpus, config, design, todo]
created: 2026-05-27
document:
  priority: medium
  effort: high
  status: open
---

# Configurable corpus vaults replace single-root indexing

`tools.set_root` binds the index to one corpus root under `cwd`. Cross-repo knowledge graphs need a configurable collection of corpus vaults indexed into one catalog, with global vocabulary so BM25 IDF spans the union and per-vault tagging stays addressable.

## Current shape

[Observation] `plugins/hoplite/mcp/src/hoplite/server.py:23` calls `tools.set_root(Path.cwd())` once at module load. The corpus root resolves to `<cwd>/docs`. `tools._corpus_root` holds one `Path`, and `_get_graph` walks that single tree to populate the in-memory graph.

[Observation] This works for a single-repo corpus — Hoplite's own `docs/` tree, for example. It breaks for the cross-repo case where personal knowledge lives across many git repositories, each with its own `docs/notes/` and `docs/journal/`.

## Vault collection over virtual root

[Inference] The corpus root becomes a *collection* of roots rather than a single path. Two shapes:

1. A configurable list of vaults — each a path, each walked independently, results unified into one in-memory graph.
2. A single virtual root with the vaults symlinked or mounted underneath. The walker stays single-rooted; unification happens at the filesystem layer.

[Inference] (1) makes the multi-vault structure explicit in the index, so each document carries its vault provenance and queries can scope by it. (2) hides the vault layer behind directory layout; the walker cannot distinguish a vault boundary from a sub-directory boundary. Pick (1).

## Configuration surface

[Inference] The configuration lives outside `set_root(cwd)`. Options to explore:

- An environment variable carrying a delimited list of paths (`HOPLITE_VAULTS=/path/one;/path/two` — semicolons on Windows for path compatibility).
- A config file at `~/.hoplite/vaults.yaml` listing vault roots and per-vault metadata.
- An MCP-level argument set at server launch, via FastMCP's initialization hooks.

[Inference] The config-file shape composes with future per-vault metadata — a friendly name, a default tag injection, a read-only flag for archived repos. The environment variable is the simpler v1 path if metadata can be deferred.

## Identity and provenance

[Inference] Documents currently identify by path relative to the corpus root — `docs/notes/foo.md`. Two vaults can both contain that path and collide. Two ways to resolve:

1. Prefix the canonical path with a vault identifier — `<vault>/docs/notes/foo.md`. The vault becomes a first-level path component.
2. Materialize the vault as a node property (`vault: a`) and let paths collide. Queries filter by the property; the canonical key becomes `(vault, path)` rather than `path` alone.

[Inference] (1) is cleaner for cross-vault wikilinks — `[[<vault-b>/docs/notes/bar.md]]` resolves unambiguously by syntax alone. (2) preserves current path shape but requires every query to thread the vault qualifier. Pick (1).

## Per-vault metadata as tags

[Inference] Each vault injects a synthetic tag on every document it contributes — the way the walker injects `ghost` onto unresolved wikilink targets and `url` onto markdown URL nodes. A vault tagged `work` or `personal` makes `where({"tagged": "work"})` scope a search without filename-pattern hacks. Per-vault tagging belongs in the configuration alongside the path.

## IDF spans the union

[Inference] Once [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] lands, BM25 IDF computes over the union of vaults, not per vault. Cross-vault `related` only finds the same idea in two notebooks if term frequency calibrates against the full vocabulary — a term common in one vault but rare across the union still scores low and surfaces as a topical signal.

[Inference] Per-vault IDF would over-weight vault-local jargon and under-weight cross-vault rare terms. The catalog is one index; the IDF is one vocabulary.

## Refresh granularity

[Observation] `refresh()` today re-walks the entire single corpus, recomputes signatures, rebuilds FTS5, re-emits edges. At single-vault scale that suffices; at multi-vault scale with thousands of documents across many repos, full reindex on every write is wasteful.

[Inference] Per-vault refresh — re-walk one vault, recompute its signatures, update the global index in place — is the natural follow-up. Out of scope for the initial multi-vault landing; tracked for after the basic structure works.

## Open questions

- Vault identifier shape — short slug, full path hash, or git remote URL?
- Sticky vault identity when a vault moves on disk. Stable identifier vs. path-derived?
- Cross-vault wikilink syntax — `[[<vault>/docs/...]]` baked into the resolver, or a separate vault qualifier in the link?
- Watch-mode reindex (on filesystem change) becomes more interesting at multi-vault scale. Currently out of scope.

## See also

- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — paired upgrade. BM25 cosine over the FTS5 index needs global vocabulary, which multi-vault both enables and requires.
- [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]] — adjacent retrieval pattern; multi-vault matters there too if vault-scoping graph signals like centrality is in scope.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that surfaced the scale question.
