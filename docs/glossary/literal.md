---
title: literal
summary: "An out-of-line value — freeform text or a blob — stored in the literal table and projected as a resource on demand."
tags: [hoplite, glossary]
created: 2026-07-03
status: evolving
---

An out-of-line value — freeform text or a blob — stored in the literal table and projected as a resource on demand.

## Notes

- The address derives from key and subject (`summary:<doc-uri>`), so the projection is never stored.
- One value per document per key — the functional constraint, enforced by the store's key.
- RDF's literal may only end a statement; Hoplite's projects as a resource, so it can be addressed and cited.
