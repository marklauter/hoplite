---
title: things I know
summary: assertions on the code base
document:
  tags: [note, hoplite, architecture]
  created: 2026-05-28
  status: design
---

# things I know

asserstions on the code base

## schema.sql

- schema.sql is higly optimized
- schema.sql is pure graph storage - no document or domain noise
- ready to ship

## migrations.py

- no versioning - but not required for disposable data store
- idempotent
- ready to ship

## db.py

- models SQLite's real concurrency correctly
- deliberate, coherent transaction model
- Properly decoupled behind a Protocol
- ready to ship

## graph.py

## frontmatter.py

- created
- extracted from walker which lived in graph.py
- unreviewed