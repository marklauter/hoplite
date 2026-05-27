---
title: First hoplite modules — parser, filter, stubs, MinHash, ids, wikilinks
summary: Five afternoon hours land the pure-compute pieces: label-expression parser with ruff/pyright gating, candidate-filter wrapper, MCP tool-surface stubs with echo-style fakes, MinHash + jaccard module, ids module with validator and resolver, wikilinks parser. The skeleton hoplite needs before any real graph wiring.
tags: [journal, hoplite, mcp, python, milestone]
created: 2026-05-24
aliases: []
---

# First hoplite modules — parser, filter, stubs, MinHash, ids, wikilinks

Five afternoon hours land the pure-compute pieces: label-expression parser with ruff/pyright gating, candidate-filter wrapper, MCP tool-surface stubs with echo-style fakes, MinHash + jaccard module, ids module with validator and resolver, wikilinks parser. The skeleton hoplite needs before any real graph wiring.

## Intent

Toolchain in place from earlier in the day. Spec stable. The next step is building the pure-compute pieces — modules that have no graph dependency, no MCP coupling, and no I/O. Each can ship with full test coverage on its own; the graph wiring layer comes later.

The ordering matters: build the leaves first, then the trunk that uses them. The leaves are pure functions over data structures; they need no mocks, no fixtures, no fake storage layer. The trunk that uses them will be much smaller and much easier to reason about once the leaves exist.

## What landed (chronological)

- 2026-05-24 17:01 — Add label expression parser; configure ruff + pyright gate. (Co-landed with the toolchain setup.) The parser handles `a & b`, `a | b`, `!a`, parentheses; produces an AST the filter walks. Pure function from string to AST.
- 2026-05-24 17:11 — Add candidate-filter wrapper around the label-expression parser. Takes a parsed predicate and a candidate stream; produces the filtered subset. Pure function; no I/O.
- 2026-05-24 17:12 — Stub hoplite_mcp tool surface with echo-style fakes. Every tool wired through to the MCP server but returning fixture data. Lets the agent integration land before the storage layer exists.
- 2026-05-24 17:33 — Remediate stub-review findings on the hoplite MCP surface.
- 2026-05-24 17:33 — Parameterize frozenset literals uniformly in `test_filtering.py`. Test cleanup pass.
- 2026-05-24 17:34 — Add empty-generic-literal rule to writing-python skill. New skill rule capturing a pattern that came up in review.
- 2026-05-24 17:46 — Revert empty-generic-literal semgrep rule. The rule was too aggressive; reverted within 12 minutes.
- 2026-05-24 17:46 — Docs drift sweep + MinHash 64-bit hash family. Spec gets updated to specify the hash family before implementation lands.
- 2026-05-24 17:48 — Gitignore: venv, egg-info, ruff/pytest caches.
- 2026-05-24 18:07 — Add MinHash + jaccard module for hoplite write flow. 128-permutation signatures over uint64; jaccard similarity over signatures.
- 2026-05-24 18:08 — MinHash: review fixes — sentinel hardening, doc cross-ref, raise tests. Sentinel for empty input; test coverage for the raise paths.
- 2026-05-24 18:16 — Add wall-clock bench for `minhash.signature()` over docs/. Confirms the cost budget — ~50 ms per kilodoc — fits the cold-start tolerance.
- 2026-05-24 18:25 — Added plan. Plan note for the ids module before writing it.
- 2026-05-24 18:26 — Fixed gate. CI fix for the ruff/pyright gate.
- 2026-05-24 18:26 — Added wikilinks. Wikilink-extraction module; pure function from markdown body to a list of `[[wikilink]]` targets.
- 2026-05-24 19:15 — Land hoplite ids module with validator, resolver, and rehomed slugify_text. The path-as-id work from the morning's spec lands as Python. Validator confirms paths are well-shaped; resolver maps wikilink text to ids; slugify_text moves from its previous home into ids.py.
- 2026-05-24 19:18 — Updated plan.

## What the modules ended up doing

Each module is a leaf, tested in isolation:

- `parser.py` — label-expression parser. Recursive-descent over the predicate grammar. Returns an AST.
- `filtering.py` — candidate filter. Walks the AST against `(id, frozenset[label])` candidates; returns survivors in order. No dedupe; that is a caller concern.
- `minhash.py` — MinHash signatures + jaccard estimate. 128 permutations over uint64; signatures are stored as 1024-byte byte strings.
- `ids.py` — path-as-id validator, resolver, slugify_text. Path validation, wikilink text → id resolution.
- `wikilinks.py` — body parser. Extracts `[[target]]` occurrences from markdown body text; returns target strings ready for resolver lookup.
- `models.py` — dataclass definitions for Document, Tag, Edge.
- `tools.py` — MCP tool surface; echo-style fakes during this session, real implementations after the storage layer lands.

## Decisions captured

- Leaves first, trunk second. Building the pure-compute modules before the graph wiring meant every commit through this session shipped clean with full test coverage. The graph wiring that came next had a much smaller surface to reason about.
- Echo-style fakes for the MCP surface. Wiring the tool surface before the storage layer let the agent integration get tested end-to-end with fixture data. The stubs disappeared a day later when the real implementations replaced them.
- Benchmarks land with the modules. The MinHash bench commit confirmed the cold-start cost budget. Doing this with the module rather than after means the cost-model assumption gets checked against reality immediately.
- The `empty-generic-literal` reversal. A rule got added then reverted within 12 minutes after the cost in reading was higher than the bug it prevented. Skills should err toward stricter, but a rule that fires too widely creates more noise than signal; the test was reading the rule's diff and feeling the friction.

## Cross-references

- `[[journal/2026-05-24-1701-python-toolchain-and-writing-python-skill]]` — the toolchain these modules built against.
- `[[journal/2026-05-24-0411-sqlite-hybrid-wins-file-based-dropped]]` — the spec these modules implement against (mostly).

## Next

The ids module gets deleted overnight when identity collapses to path and the surrogate-key work retires. The MinHash, wikilinks, parser, and filtering modules survive the redesign mostly unchanged. See `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]`.
