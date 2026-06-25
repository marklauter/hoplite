---
title: Navigation — survey, filter, walk, project, read
summary: The five read moves the graph affords an agent — survey the vocabulary, filter the corpus by predicate, walk the edges, project the result, read the survivors. The read half of the affordances, and the query surface that replaces the glob-grep-read loop.
tags: [hoplite, affordances, navigation, spec]
created: 2026-06-12
status: wip
---

# Navigation — survey, filter, walk, project, read

Navigation is the read half of the affordances ([[docs/hoplite/hoplite-affordances.md]]): the moves that query features rather than assert them. The agent surveys the vocabulary, filters the corpus, walks the edges, projects the result, and reads the survivors — spending its context on the subset that bears on the task.

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

## open questions

1. Anchor on features, not structure. The lede should open on the move querying features, not "the structure affords five moves" — affordances arise from features; the graph is the mechanism beneath them ([[docs/hoplite/hoplite-feature-taxonomy.md]]). Read affordances range over the whole feature set.
2. State each move mechanism-free first. Every section dives straight into mechanism — the `(keyid, value)` reverse index, BM25, the `fts` projection. Name what the move lets the agent do, then how the index affords it (concept-first; the MOVIEFONE rule).
3. Collapse the mining-stock tail. The "from hoplite.md vision document" section duplicates the five moves and still says "filter by meaning" where these sections are lexically honest. Fold its surviving detail into the sections above, then delete it.
4. Reconcile the move taxonomy with the Map. Here: survey / filter / walk / project / read. README Map: survey / search / filter / walk / projection. Keep "read" (the handoff is a real move); decide whether "search" stays folded into filter.
