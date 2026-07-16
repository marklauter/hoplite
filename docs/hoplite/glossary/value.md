---
title: value
summary: "A resource whose uri carries the value itself, shared by every subject that asserts it."
tags: [hoplite, glossary]
created: 2026-07-03
status: evolving
---

A resource whose uri carries the value itself (`priority:high`, `created:2026-06-30`), shared by every subject that asserts it.

## Notes

- The sharing is what makes values walkable — who else carries this value.
- Ordered scans ride the address: ISO-8601 dates sort, so ranges are index scans.
- Enumerable values intern as resources; freeform text and blobs go out-of-line as [[literal]]s.
