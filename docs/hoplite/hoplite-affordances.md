---
title: Affordances for the agent — survey, filter, walk, project, read
summary: The five read moves the graph structure affords an agent — survey the vocabulary, filter the corpus by predicate, walk the edges, project the result, read the survivors. The query surface that replaces the glob-grep-read loop.
document:
  tags: [hoplite, affordances, spec]
  created: 2026-06-04
---

# Affordances for the agent — survey, filter, walk, project, read

The structure ([[docs/hoplite/hoplite-graph.md]]) affords five moves against the graph: survey the vocabulary, filter the corpus, walk the edges, project the result, read the survivors. The agent reads only what survives the projection, spending its context on the subset that bears on the task.

## Survey

Survey reads the schema vocabulary before a predicate is composed — the keys and labels available to filter on. It is the read graph's `match` shape applied to the schema: find and walk.

Find reads the namespace — `property_key` on the document side, `stereotype` on the edge side, each a small interned list (see [[docs/hoplite/hoplite-graph.md]]).

Walk descends a key to its values: the distinct `value` rows under one `keyid`, served by the `(keyid, value)` reverse index. The keys are the nodes of a vocabulary graph, `key → value` the edge, the values the reachable set. A key's categorical-or-scalar nature resolves in the walk — a key reaching a handful of values is categorical (`tags`, `status`), one reaching thousands of near-unique values is scalar (a timestamp, a score). The distinction is empirical: the index carries the walk, and the agent reads it off the result.

The edge side has a single description dimension, so its survey is the find alone — a direct read of `stereotype`.

## Filter

Filter narrows the corpus to the subset a Boolean predicate admits — `note & mcp & !draft`. Two predicate kinds compose. A text predicate ranks documents by topical relevance: BM25 over the `fts` projection of title, summary, and body, so `caching strategy` surfaces documents about caching rather than lines carrying the token. A property predicate filters by tag or property expression; properties crosscut the folder tree, so filtering by one gathers a concept wherever it is filed.

## Walk

Walk traverses edges from a starting node to gather a neighborhood the directory tree leaves invisible. It follows `declared` and `discovered` edges outward or inward — a relationship declared once reads both ways, so the backlink comes free. Ghost nodes keep the corpus's open loops enumerable along the walk. Depth, edge kind, direction, and a confidence-ranked cap on discovered neighbors per node bound the traversal.

## Project

Project shapes the result before it returns. It sorts by relevance score or traversal distance, caps the hop count and the result size, and returns a projection of each hit — the uri, the authored summary, and the tags. Hoplite hands back the projection, so the agent judges relevance from the summary before spending a token to open the file.

## Read

Read is the handoff. Hoplite ends at the projection; the agent crosses to full content with the built-in `Read` tool, and only for the hits that survive.
