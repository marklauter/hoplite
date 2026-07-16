---
title: A links-to default stereotype turns markdown links into edges
summary: "Naming the default inline stereotype `links-to` removed the only reason markdown links were excluded from the graph, so every inline link — wikilink or markdown — is now an edge. expressing-edges.md reopened to evolving."
tags: [journal, edges, spec]
created: 2026-06-23
---

## Context going in

Straight after [[2026-06-23-1718-neo4j-book-grounds-stereotyped-edge-model]], we
were settling the last open piece of the edge model: what does a *bare* inline
link mean — a `[[circle]]` with no stereotype attached?

The locked spec `docs/specs/expressing-edges.md` called that an "untyped edge,"
and went further: its summary said "A markdown link is plain hypertext, **not an
edge**." Markdown links were excluded from the graph entirely.

## What I tried / the path

We needed a name for the implicit stereotype. Three candidates: `knows`, `links`,
`references`. I killed `knows` immediately — it's Neo4j's *social-graph example*
type (`:KNOWS`), wrong domain for a document graph.

That left `links` vs `references`. Mark leaned `links`; I argued for `references`
on two grounds: (1) the spec already spends the word "link" on the *non-edge*
case ("a markdown link is plain hypertext"), so a stereotype named `links` would
step on exactly the line the spec draws; (2) grammar — "document references
document" reads, "document links document" wants "links *to*". I offered
`links-to` as the grammar-fixed variant of `links`.

Mark took `links-to`, and then made the move that mattered: naming the stereotype
`links-to` (a *name*, not the bare word "link") **dissolves** the ambiguity
between markdown links and wikilinks. It's no longer "is this a link or an edge?"
— it's a [[stereotype]] called `links-to`, and the link syntax is irrelevant.

## What I learned / the unlock

The reason markdown links had been excluded was never principled — it was that we
didn't know how to stereotype them. Naming a default stereotype solves that. So:

- **Every inline link is an [[edge]]** — a `[[wikilink]]` or a markdown
  `[text](target)`. There is no plain-hypertext link in a corpus anymore.
- **The default inline stereotype is `links-to`.** An adjacent comment
  (`<!--cites-->`, `%%cites%%`, `[cites:: ...]`) overrides it.
- **Markdown links are full first-class edges** — same stereotype-comment
  grammar, e.g. `[circle](circle)<!--cites-->`.

## What changed, and what's still open

Rewrote `expressing-edges.md`: new summary, "two places (body, frontmatter)"
instead of "two ways," a `links-to` default throughout, and a new `## Markdown
links` section. I flipped it from `locked` to **`evolving`**, because one piece is
genuinely unspecified: the **markdown-link target grammar**. A markdown target can
be an external URL, a relative path, or an anchor — a superset of the wikilink
`TARGET_RE` — and external URLs resolve to `url` nodes. That grammar isn't pinned,
and `plugins/hoplite/hooks/edge_grammar.py` doesn't extract markdown links at all
yet, nor does the `check-frontmatter` hook validate them. Those are the follow-ups
that have to land before this can lock again.

One earlier wrong turn worth recording: mid-discussion I briefly rewrote
[[relationship]] to drop "stereotyped edge" (arguing the link alone is the
relationship). Mark reverted it — "that's onto something" — and the Neo4j book
later confirmed the stereotyped-edge model. The detour is in the prior entry.
</content>
