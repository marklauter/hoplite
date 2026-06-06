---
title: Wikilink resolver leaves alias and anchor in the target
summary: Anchor and alias syntax survive wikilink capture and resolution, producing ghost paths like `hoplite/roadmap|roadmap.md` for documents that already exist.
tags: [note, todo, hoplite, mcp, wikilinks, bug]
created: 2026-05-27
document:
  priority: medium
  effort: low
  status: closed
---

# Wikilink resolver leaves alias and anchor in the target

Anchor and alias syntax survive wikilink capture and resolution, producing ghost paths like `hoplite/roadmap|roadmap.md` for documents that already exist.

## Observation

The export at `.hoplite/2026-05-27T08-06-43.index.sqlite` lists ghost documents whose paths carry raw wikilink display syntax:

- `hoplite/architecture#dump-schema|architecture.md`
- `hoplite/architecture#tag-predicates|architecture.md`
- `hoplite/roadmap|roadmap.md`
- `hoplite/tool-api|tool-api.md`

Each corresponds to an authored link of the form `[[target#anchor|alias]]` or `[[target|alias]]`. The intended target — `hoplite/architecture`, `hoplite/roadmap`, `hoplite/tool-api` — has a backing `.md` file in the corpus. The resolver still emits a ghost.

## Mechanism

`wikilinks.extract` at `plugins/hoplite/mcp/src/hoplite/wikilinks.py:42` matches `\[\[([^\]]+)\]\]` and only strips surrounding whitespace from the capture. Anchor (`#section`) and alias (`|display text`) syntax pass through verbatim.

`Graph.resolve_wikilink` in `plugins/hoplite/mcp/src/hoplite/graph.py` walks four lookup steps — direct path, declared alias, casefolded path, `.md`-appended retry — and skips the alias/anchor split. The raw string `hoplite/roadmap|roadmap.md` misses every step and materializes a ghost with that exact path. (After the SQLite refactor the casefold step folds into `node.uri COLLATE NOCASE`; the alias/anchor-split bug this note describes is independent of that.)

## Fix shape

The split belongs in the resolver, not the extractor — `extract` is contract-stable as "body-in, raw capture out," and the walker is the documented owner of resolution. Before the existing lookup chain, derive the resolution key by taking the slice before the first `|` and before the first `#`. Authored display syntax remains available for any downstream renderer; resolution uses the path alone.

## Adjacent

Two code-fragment ghosts in the same export — `...` and `frozenset[str` — were a distinct bug: extraction ran inside fenced code blocks and inline-code spans, where `[[X]]` is sample text rather than a link. Fixed in the same change set by masking code spans before the wikilink regex runs.

## Resolution

Landed. `resolve_wikilink` at `plugins/hoplite/mcp/src/hoplite/graph.py:143` now strips alias and anchor before the lookup chain: `target.split("|", 1)[0].split("#", 1)[0].strip()`. The docstring records the contract — "Display syntax — `#anchor` and `|alias` — is stripped before lookup." The walker's convention check at `graph.py:326` strips the same suffixes before the `docs/` / `ghost/` prefix gate, so malformed-target warnings no longer false-positive on aliased or anchored links.
