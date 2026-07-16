---
title: Authoring — declare relationships, describe documents
summary: The write half of the affordances — how an author asserts features by declaring relationships (inline wikilinks) and describing documents and edges (frontmatter properties, summaries, stereotypes). Express-only; the model it expresses lives in the graph canon.
tags: [spec, affordances, authoring]
created: 2026-05-31
status: stub
---

# Authoring — declare relationships, describe documents

Stub. Authoring is the write half of the affordances ([[docs/specs/hoplite-affordances.md]]) — the moves the author uses to assert features ([[docs/specs/hoplite-feature-taxonomy.md]]) into the corpus, across two mechanisms: declare and describe. This document expresses the model defined in [[docs/specs/hoplite-graph.md]]; when the two disagree, the canon wins.

## Declare — inline wikilinks

To be written. How `[[docs/<path>.md]]`, `[[ghost/<slug>]]`, and markdown URL links declare edges.

## Describe — frontmatter

To be written. Absorbs the express-only contract currently in [[docs/specs/hoplite-frontmatter.md]] (held pending the data-model spec): namespaced keys, bare `title`/`summary`, mandatory and optional fields, the spelling axes, malformed-block handling, Obsidian compatibility.

# from hoplite.md vision document

Prose lifted verbatim from the `hoplite.md` vision draft when the vision doc was cut back to problem-plus-solution. Mining stock, not yet locked; integrate into the sections above when the model settles.

## Declare and describe — applying explicit structure

The author asserts what the bytes can't yield: a relationship that lives only in a link, a title that isn't the filename, a summary the document never states. This is explicit structure — supplied, not inferred — and the graph treats it as fact.

A wikilink declares a relationship grep can't see: a directed edge from one document to another. A markdown link declares one too, reaching content outside the corpus — the graph's edges don't stop at its own files. Declared once, an edge reads both ways; the backlink, who points here, is free structure. Whether the tie is symmetric is the stereotype's call — `supersedes` runs one way, a `related` or `not-related` tie reads both. A ghost link declares an open loop: not-yet-written content made explicit rather than lost.

Description annotates the structure. A title and summary are asserted, not extracted — a filename is not a title, and a document carries no summary of itself. The summary is the lede the agent reads to decide whether to open the document or follow the edge. Properties — tags, status — classify a document and crosscut the folder it is filed in. A stereotype labels an edge with the kind of relationship it carries: cites, supports, supersedes, contradicts. Describe an edge inline beside the claim it makes, or in frontmatter as a document-level fact — same structure either way. The vocabulary is open: the author coins a label and it earns canonical status by use, the way tags do.
