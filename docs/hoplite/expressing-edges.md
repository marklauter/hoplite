---
title: Expressing edges
summary: "The three ways to express an edge: an inline wikilink, a frontmatter edge stereotype, and a markdown link for external content — with the target grammar the two internal forms share."
tags: [hoplite, edges, authoring]
created: 2026-06-20
document.status: locked
---

# Expressing edges

There are three ways to express an edge between documents. In the body, a [[wikilink]] expresses an internal edge and a markdown link expresses an external one (to a URL node). In frontmatter, an `edges` list expresses internal edges, structured. Wikilinks and frontmatter edges share one target grammar; markdown links carry only display text and a URL.

## Wikilinks

Internal references, following the standard wiki conventions (MediaWiki, Obsidian).

### Target

The target is a page name, optionally qualified by its [[namespace]]. No `.md` extension.

- **By name** — `[[circle]]`: the resolver finds the unique page.
- **Namespace-qualified** — a namespace is a path; a colon divides namespace from page: `[[lib/shapes:circle]]`. Qualify only when the bare name would be ambiguous.

### Subpages

`/` divides subpages, `:` divides namespace from page, so the two never collide: `[[lib/shapes:circle/area]]` is page `circle`, subpage `area`. Relative forms: `[[/child]]`, `[[../parent]]`.

### Sections and blocks

- **Section** — `[[circle#properties]]`; same page `[[#properties]]`; subheading `[[circle#properties#radius]]`.
- **Block** — `[[circle#^radius-def]]`: a single block, finer than a heading.

### Stereotype

A bare wikilink expresses an untyped edge. Lead the target with a `stereotype::` prefix to type it — `[[refines::circle]]`. The single colon stays the namespace separator, so the two never collide: `[[refines::lib/shapes:circle]]`.

### Rendering

- **Display text** — `[[circle|shown text]]`: target first, display text second.
- **Embedding** — `![[circle]]`: transcludes the target's content in place.

### Ghosts

A link whose target does not exist is a [[ghost]] — the wiki redlink: it surfaces as backlog and is creatable. Expressed explicitly as `[[ghost/<slug>]]`.

## Frontmatter edges

`edges: [<target>, ...]` expresses edges in frontmatter. Each `<target>` is exactly a wikilink target — the same string you would write inside `[[ ]]`, `stereotype::` prefix and all.

- **Identical grammar.** `name`, `namespace:page`, `/subpage`, `#section`, `#^block`, `stereotype::target`, `ghost/<slug>` — every form carries over verbatim; a bare target is an untyped edge.
- **No rendering features.** Display text (`|`) and embedding (`!`) are inline-only; a frontmatter edge is data, not rendered.
- **Equivalence.** `[[refines::circle]]` and `edges: [refines::circle]` are the same edge — the target string is identical, inline versus structured.

## Markdown links

External content only: `[text](https://example.com)`. The wikilink feature set does not apply — a markdown link is display text plus a URL.

- The walker indexes the URL as a graph node, joined by an edge, so external references are backlink-discoverable like any other node.
- A durable or reused external reference earns a proxy note under `docs/proxies/`, then is wikilinked like any internal document.
