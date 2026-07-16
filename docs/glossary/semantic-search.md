---
title: semantic search
summary: "A scoring condition: it matches a field by meaning and attaches a relevance score to each hit."
tags: [glossary]
created: 2026-06-19
status: evolving
is-a: "[[condition]]"
---

A scoring condition: it matches a field by meaning, not literal text, and attaches a relevance score to each hit.

## Phases

The intent is fixed; the mechanism evolves. Phase 0 approximates meaning with full-text search — [[bm25]] over the FTS index. Phase 1 adds vector embeddings, scoring by distance in semantic space.
