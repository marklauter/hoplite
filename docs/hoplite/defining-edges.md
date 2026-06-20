---
title: Defining edges
summary: "The three ways to declare an edge: an inline wikilink, a frontmatter edge stereotype, and a markdown link for external content — with the target grammar the two internal forms share."
tags: [hoplite, edges, authoring]
created: 2026-06-20
document.status: evolving
---

# Defining edges

An edge between documents is declared three ways. In the body, a [[wikilink]] declares an internal edge and a markdown link declares an external one (to a URL node). In frontmatter, `edge.<stereotype>` declares an internal edge, structured. Wikilinks and frontmatter edges share one target grammar; markdown links carry only display text and a URL.

## Wikilinks

Internal references, following the standard wiki conventions (MediaWiki, Obsidian) rather than reinventing them.

### Target

The target is a page name, optionally qualified by its [[namespace]]. No `.md` extension.

- **By name** — `[[assert]]`: the resolver finds the unique page.
- **Namespace-qualified** — a namespace is a path; a colon divides namespace from page: `[[docs/hoplite/glossary:assert]]`. Qualify only when the bare name would be ambiguous.

### Subpages

`/` divides subpages, `:` divides namespace from page, so the two never collide: `[[docs/hoplite/glossary:assert/example]]` is page `assert`, subpage `example`. Relative forms: `[[/child]]`, `[[../parent]]`.

### Sections and blocks

- **Section** — `[[assert#heading]]`; same page `[[#heading]]`; subheading `[[assert#heading#subheading]]`.
- **Block** — `[[assert#^block-id]]`: a single block, finer than a heading.

### Stereotype

A bare wikilink makes an untyped edge. Prefix a stereotype with `::` (Semantic MediaWiki's property syntax) to type it — `[[contrast::assert]]`. The single colon stays the namespace separator, so the two never collide: `[[contrast::docs/hoplite/glossary:assert]]`.

### Display text

`[[assert|shown text]]` — target first, display text second.

### Embedding

`![[assert]]` transcludes the target's content in place — a spec embeds a locked term's definition rather than restating it.

### Ghosts

A link whose target does not exist is a [[ghost]] — the wiki redlink: it surfaces as backlog and is creatable. Authored explicitly as `[[ghost/<slug>]]`.

## Frontmatter edges

A wikilink declares an edge inline; frontmatter declares the same edge, structured. `edge.<stereotype>: [<target>, ...]` lists typed edges.

- **Shared target grammar.** Each `<target>` is a wikilink target — name, `namespace:page`, `/subpage`, `#section`, `#^block`, `ghost/<slug>`.
- **No rendering features.** Display text (`|`) and embedding (`!`) are inline-only; a frontmatter edge is data, not rendered.
- **Equivalence.** `[[contrast::assert]]` and `edge.contrast: [assert]` declare the same edge — inline versus structured.

## Markdown links

External content only: `[text](https://example.com)`. The wikilink feature set does not apply — a markdown link is display text plus a URL.

- The walker indexes the URL as a graph node, joined by a declared edge, so external references are backlink-discoverable like any other node.
- A durable or reused external reference earns a proxy note under `docs/proxies/`, then is wikilinked like any internal document.
