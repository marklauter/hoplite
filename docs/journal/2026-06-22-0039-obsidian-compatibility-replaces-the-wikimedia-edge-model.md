---
title: Obsidian compatibility replaces the WikiMedia edge model
summary: Formalizing the wikilink edge syntax on a rich WikiMedia format broke Obsidian; the fix was to drop the colons and sub-pages and rebuild on Obsidian's own Properties model, which already covered what we needed.
tags: [journal, obsidian, edges, frontmatter, milestone]
created: 2026-06-22
---

# Obsidian compatibility replaces the WikiMedia edge model

## Context

We set out to formalize the wikilink edge syntax — how an edge from one document to another is written. The plan leaned on wiki convention: a rich WikiMedia / Semantic-MediaWiki format with `:` namespace separators, `::` stereotype prefixes, and sub-pages. Obsidian was a partial, best-effort compatibility target, and we believed the richer model was worth the asymmetry.

## What happened

We built the rich format first — `[[stereotype::namespace:page]]`, sub-pages and all — and the cracks showed under validation before they showed in Obsidian. With sub-pages, `/` carried two meanings at once: a separator between namespace path segments, and a separator between a page and its sub-page. A target like `a/b` was ambiguous — an invalid namespace path missing its colon, or a valid page with a sub-page? The grammar couldn't tell them apart, so neither could a validator. We dropped sub-pages as soon as we saw it, which made `/` mean one thing. This ran alongside the glossary reduction — the `property` term and its neighbors — where the same over-complication was surfacing from the other direction.

Then we checked the format against Obsidian, and it broke outright: Obsidian forbids `:` in link targets and addresses notes by folder path, not colon-namespaces. The rich model and Obsidian were structurally opposed, not partially compatible.

The wrong turn was building the format before confirming it could be validated or live in Obsidian. The cost was a refactor.

## Decision

Refactor toward total Obsidian compatibility. We dropped the colons and sub-pages, made the folder path the namespace, and moved the stereotype out of the target into a frontmatter key (`cites: "[[shape]]"`).

That move cost us inline stereotypes. With `:` and `::` gone from the target, a body `[[wikilink]]` could only be untyped — there is no Obsidian-legal way to say `refines` inside the link. We accepted it as a tradeoff: typed edges in frontmatter, untyped links in the body.

It turned out not to be necessary. The "hidden content" idea — put the stereotype in text that lives in the file but doesn't render — reopened the question and surfaced three forms that all work: an HTML comment (`[[circle]]<!--refines-->`), an Obsidian comment (`%%refines%%`), and a Dataview inline field (`[refines:: [[circle]]]`). Inline stereotypes came back, none of them rendering in Obsidian.

The larger surprise was that Obsidian had already solved most of this. We read their Properties reference and used it as the foundation rather than inventing our own — plainer than WikiMedia, but everything we needed was expressible. It landed as two locked specs, [[expressing-edges]] and [[hoplite/frontmatter]], plus a stdlib `check-frontmatter` hook and `edge_grammar.py` that enforce the grammar.

## What we learned

The governing rule out of this: Obsidian-compatible, never Obsidian-dependent. The corpus is a valid Obsidian vault — shareable, and a pleasure to use at home with Obsidian as a lens — but Hoplite reads the plain files directly and must run headless in SSH'd Linux work containers with no Obsidian, GUI, or plugins. So the load-bearing path is always "plain files Hoplite parses anywhere"; anything that needs Obsidian's runtime is a nicety, never required. That test — does it need Obsidian running? — is why the hook is stdlib bare-`python3` and inline stereotypes are comments, not a plugin format.
