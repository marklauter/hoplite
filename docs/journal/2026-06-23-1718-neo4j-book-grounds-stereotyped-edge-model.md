---
title: Neo4j's book grounds the stereotyped-edge model
summary: "The Graph Databases (2e) labeled-property-graph definition makes a relationship a named, directed, first-class connection — confirming relationship = stereotyped edge, and raising a node+edge vs node+relationship tension."
tags: [journal, glossary, graph]
created: 2026-06-23
---

## Context going in

Mid-pass through the glossary lock work: after locking [[corpus]], we stopped
locking term-by-term and started firming up the *edges between* the already-locked
terms. That ran straight into the [[edge]] / [[relationship]] pair.

The working model from the session was:

- [[document]] **is-a** [[node]] — a node enriched with the document facet, properties, and a body.
- [[relationship]] **is-a** [[edge]] — a *stereotyped* edge; the edge is the bare graph attachment, the [[stereotype]] names what kind.

I briefly talked myself out of "stereotyped edge" with this argument: two
documents joined by a bare `[[wikilink]]` (no stereotype) are *obviously* related,
so demanding a stereotype would mean they have no relationship — absurd. So I
rewrote [[relationship]] as "the link alone is the relationship; the stereotype
only types it." Mark told me to revert it — "that's onto something and I don't
want to lose it" — and asked what a real graph company does: does Neo4j say
*edge* or *relationship*, and is it consistent?

## What I tried

1. Web search on the Neo4j property-graph model and edge-vs-relationship terminology.
2. Then read the authority Mark dropped in: `docs/Graph_Databases_2e_Neo4j.pdf`
   (Robinson, Webber & Eifrem, *Graph Databases*, 2nd ed.), "The Labeled Property
   Graph Model" section. (No `pdftoppm` in this env, so I extracted text with
   `pdftotext` rather than the Read tool's page renderer.)

## What I expected

Confirmation that "relationship = typed/stereotyped edge" is the mainstream
property-graph model, plus a ruling on which word is canonical.

## What I learned

The book's definition of a labeled property graph:

- It contains **nodes and relationships**.
- Nodes contain properties (key-value pairs).
- Nodes can be labeled with one or more labels.
- **Relationships are named and directed**, and always have a start and end node.
- Relationships can also contain properties.

Plus: "Relationships are **first-class citizens** of the graph data model."

Three things fall out:

1. **The canonical pair is `node` + `relationship`, not `node` + `edge`.** The
   book never uses "edge" or "vertex" as model terms — they stay in graph theory.
   Neo4j elevates *relationship* to the primitive and has no separate "edge"
   concept.
2. **"Relationships are named and directed" is the stereotyped-edge model.** The
   name *is* the [[stereotype]]; namedness is built into the definition, so an
   *unnamed* connection isn't a relationship in this model. This is the grounding
   for the instinct I almost discarded.
3. **The label/type split maps onto hoplite's schema.** Node labels ↔ [[tags]]
   (the schema comment already says "tags is the node-side counterpart to
   stereotype"); relationship name ↔ stereotype. Neo4j requires *exactly one*
   type per relationship; hoplite's `edge_stereotype` junction allows zero-or-many.

## The open tension (not resolved here)

Hoplite runs **two altitudes** — graph theory ([[node]]/[[edge]]) and ontology
([[document]]/[[relationship]]) — where the book runs **one** (node +
relationship). That two-altitude split is the deliberate hoplite departure, and
it's what makes "edge" earn its keep as a distinct term.

Two decisions queued behind this:

- **Untyped relationships?** Follow the book (every relationship is named ⇒ a bare
  wikilink gets a default name — a `references` floor — or isn't a relationship)
  vs diverge (keep untyped relationships, keep the edge/relationship altitude split).
- **Stereotype arity.** Neo4j: exactly one type per relationship. Hoplite's
  junction currently implies zero-or-many. Pick one deliberately.

See the prior turn in the edge model's history:
[[2026-06-22-0039-obsidian-compatibility-replaces-the-wikimedia-edge-model]].
</content>
