---
title: ids.py deletion — 91 lines retired in one commit
summary: The ids module — path-as-id validator, wikilink resolver, slugify_text — built the previous afternoon and committed at 19:15. Deleted at 00:45 the next morning when identity collapsed from three-tier (ULID + filename + integer-PK) to single-tier (path). 128 lines of tests retired alongside.
tags: [journal, hoplite, refactor, identity, dead-end]
created: 2026-05-25
aliases: []
---

# ids.py deletion — 91 lines retired in one commit

The `ids` module — path-as-id validator, wikilink resolver, `slugify_text` — built the previous afternoon and committed at 19:15. Deleted at 00:45 the next morning when identity collapsed from three-tier (ULID + filename + integer-PK) to single-tier (path). 128 lines of tests retired alongside.

## What ids.py did

Built across the late-afternoon module work ([[journal/2026-05-24-1918-first-hoplite-modules]]):

- A validator confirming a path was well-shaped for use as an id (no leading slash, no parent-directory traversal, length bounds).
- A resolver mapping wikilink text to an id. Handled aliases (an explicit alias in frontmatter took precedence) and the shortest-unique-prefix rule for ambiguous matches.
- `slugify_text` — moved from its previous home to live alongside the resolver since both fell under "id handling."

Companion `test_ids.py` carried 128 lines of unit tests across the validator, the resolver, and the slugify rule.

The total surface was a clean leaf module — pure functions, no I/O, full test coverage. Exactly the shape the toolchain decision was meant to produce.

## What killed it

The morning redesign ([[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]) collapsed identity. The previous shape:

- ULID — domain identifier. Edges store ULIDs. Wikilinks resolve to ULIDs.
- Filename — presentation property. Mutable.
- Integer-PK — SQLite join key. Internal storage.

The new shape:

- Path — domain identifier. Edges store paths. Wikilinks resolve to paths. Filename and id are the same thing.

The validator's job (confirming a path is well-shaped) survived as a one-liner inside the walker. The resolver's job (mapping wikilink text to id) survived as a one-liner inside the wikilink-edge emitter — given the corpus has the wikilink target as a doc, the path IS the id, no lookup. The slugify rule survived but moved back to a general-purpose location since it was no longer specific to identity.

The module as a coherent unit had no remaining work. Three functions, each with one caller, none needing the others' help. The cleanest move was deletion: each function rehomed to where its caller lived; the module file disappeared.

## What "dead" looks like in the commit

The redesign commit on 2026-05-25 00:45 had several deletion stats:

- `plugins/skills/mcp/src/hoplite/ids.py` — 91 lines deleted.
- `plugins/skills/mcp/tests/test_ids.py` — 128 lines deleted.
- 1 line touched on `plugins/skills/mcp/src/hoplite/server.py` (import removed).
- 10 lines touched on `plugins/skills/mcp/src/hoplite/tools.py` (callers updated).
- 12 lines touched on `plugins/skills/mcp/tests/test_smoke.py` (assertions updated).

The 91 + 128 line deletion ratio sits in proportion to how much of the surface area moved: about a fifth of the day's previous-afternoon Python work retired in a single commit.

## Decisions captured

- A clean leaf module is not protection against architectural change. ids.py was well-tested, well-shaped, and well-documented. None of that mattered when the architecture above it stopped needing the abstraction the module embodied. Build cleanly, but don't mistake cleanliness for permanence.
- Delete in one commit. The retirement is one commit with the deletion + every caller's update. Leaving an unused module behind invites confusion: a future reader assumes the module is load-bearing because it sits there with tests. A clean deletion is a cleaner signal than a deprecation marker.
- 24-hour reversibility. ids.py existed for ~6 hours of active work and was deleted ~5 hours after its last commit. The decision-log captures the supersession trail; git history holds the actual code. Resurrection costs ~10 minutes if the surrogate-key model ever comes back into fashion.

## What this is a piece of

The bigger move was identity collapsing to path. That decision touched the data model, the tool API, the agent surface, and the walker — not just the ids module. ids.py was the most concentrated artifact of the supersession; deleting it was symbolic and load-bearing at once.

The accompanying `[[refactor-ids-and-metadata]]` note captured the intermediate position where ULIDs were still alive. That note is the snapshot from after the body-shape problem surfaced but before the identity-collapse decision settled. It captures the moment before the deletion.

## Cross-references

- `[[journal/2026-05-24-1918-first-hoplite-modules]]` — where ids.py was built.
- `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]` — the redesign that retired it.
- `[[refactor-ids-and-metadata]]` — the intermediate-snapshot note.
