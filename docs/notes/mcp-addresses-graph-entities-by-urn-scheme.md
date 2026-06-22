---
title: MCP addresses graph entities by a URN scheme
summary: "The tool-layer uri projection should address entities with URN-style schemes — node:<uri> and edge:<src-uri>:<dst-uri> — not URLs, since an entity is identified, never located."
tags: [note, todo, hoplite, mcp]
created: 2026-06-22
status: open
---

# MCP addresses graph entities by a URN scheme

Refines the addressing forms in [[uris-are-a-tool-layer-projection-over-relational-storage]] (`node/docs/foo.md`, `edge(src,dst)`) into proper URN schemes:

- `node:<uri>` — e.g. `node:docs/hoplite/glossary/property-graphs`.
- `edge:<src-uri>:<dst-uri>` — keyed by endpoints, the edge's `(src, dst)` identity ([[glossary/src-dst]]).

URN, not URL (`node://…`): an entity is identified, never located — there is no host. The colons parse because uris are colon-free (slashes only). Future work; the MCP is mid-refactor.
