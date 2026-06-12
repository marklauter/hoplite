---
title: Affordances for the agent — survey, filter, walk, project, read
summary: The five read moves the graph structure affords an agent — survey the vocabulary, filter the corpus by predicate, walk the edges, project the result, read the survivors. The query surface that replaces the glob-grep-read loop.
tags: [hoplite, affordances, spec]
created: 2026-06-04
document.status: wip
---

  Perceived vs. real affordances — an affordance only helps if the actor perceives it. A possibility no one discovers is dead. - A Donald Norman idea.

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

# from hoplite.md vision document

Prose lifted verbatim from the `hoplite.md` vision draft when the vision doc was cut back to problem-plus-solution. Mining stock, not yet locked; integrate into the sections above when the model settles. Note this copy still says "filter by meaning" / "semantic search matches by meaning" — the sections above are already lexically honest (BM25 over the `fts` projection), so reconcile that on merge.

## Read — navigating mapped relationships

Affordances emerge from the mapped structure: survey the vocabulary, filter by meaning, walk relationships, project and read the results.

1. Survey — retrieve the schema vocabulary, properties and stereotypes, before composing a predicate over the corpus.
2. Filter — narrow the corpus to the subset a Boolean predicate admits (`note & mcp & !draft`): semantic search matches by meaning, not literal string or path; properties crosscut folders, so filtering by one gathers a concept wherever it lives.
3. Walk — traverse declared and discovered edges from a node to gather a neighborhood the tree can't show: a relationship declared once reads both ways (inbound and outbound edges); ghosts keep open loops enumerable.
4. Project — organize the resultset: sort it by score or distance, shape what each hit returns (the lede and tags, never the body), and cap the hops and result set size. Hoplite hands back a projection, not a document — so the agent judges relevance from the summary the author asserted before spending a token to open the file.
5. Read — the built-in Read tool. Hoplite ends at the projection; the agent crosses to full content only for the hits that survive.
