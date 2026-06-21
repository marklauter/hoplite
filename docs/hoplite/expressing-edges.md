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

The target is a page name — `NAME = [A-Za-z0-9._-]` (strict ASCII filename characters; the `.md` extension is just dots in a name, nothing special). Optionally qualify it with a [[namespace]].

- **By name** — `[[circle]]`: the resolver finds the unique page.
- **Namespace-qualified** — a namespace is a directory path, and a colon divides it from the page: `[[lib/shapes:circle]]`, `[[docs/hoplite/glossary:term]]`. Inside a namespace `/` is an ordinary character, not a parsed separator.

There are no subpages, so `/` appears *only* inside a namespace — a colon is mandatory the moment a directory path is involved. `[[docs/hoplite/term]]` is invalid; it must be `[[docs/hoplite:term]]`.

### Sections and blocks

- **Section** — `[[circle#properties]]`; same page `[[#properties]]`; subheading `[[circle#properties#radius]]`.
- **Block** — `[[circle#^radius-def]]`: a single block, finer than a heading.

### Stereotype

A bare wikilink expresses an untyped edge. Lead the target with a `stereotype::` prefix to type it — `[[refines::circle]]`. The single colon stays the namespace separator, so the two never collide: `[[refines::lib/shapes:circle]]`.

### Rendering

- **Display text** — `[[circle|shown text]]`: target first, display text second.
- **Embedding** — `![[circle]]`: transcludes the target's content in place.

### Ghosts

A link whose target does not exist is a [[ghost]] — the wiki redlink: it surfaces as backlog and is creatable. A ghost lives in the mandatory `ghost` namespace: `[[ghost:<slug>]]`, or with a stereotype `[[<stereotype>::ghost:<slug>]]`.

### Grammar

The forms above reduce to one regular grammar over two character classes — `NAME` for a page, stereotype, and anchor label, and `NS` for a namespace (the same set plus `/`, an ordinary character here):

```
NAME   = [A-Za-z0-9._-]+
NS     = [A-Za-z0-9._/-]+
anchor = "#^" NAME | ("#" NAME)+
target = (NAME "::")?  (NS ":")?  NAME  anchor?    # (stereotyped?) (namespaced?) page
       | anchor                                      # OR a same-page anchor
```

As the `TARGET_RE` regex (`re.VERBOSE`):

```
^
(?:
    (?:[A-Za-z0-9._-]+::)?                            # stereotype
    (?:[A-Za-z0-9._/-]+:)?                            # namespace
    [A-Za-z0-9._-]+                                   # page — one filename, no '/'
    (?:\#\^[A-Za-z0-9._-]+|(?:\#[A-Za-z0-9._-]+)+)?   # anchor
  | (?:\#\^[A-Za-z0-9._-]+|(?:\#[A-Za-z0-9._-]+)+)    # same-page anchor only
)
$
```

There are no subpages: `/` is a namespace character only, so a slash-bearing target without a `:` has no parseable page and is rejected — `docs/hoplite/term` fails, `docs/hoplite:term` passes. Rendering features never appear inside a target: `NAME` excludes `|` and `!`, so a frontmatter edge bearing either fails the match; inline, display text after `|` is stripped before matching. The executable form — `TARGET_RE` plus a `validate_target` checker and the frontmatter/inline extractors, with `test_edge_grammar.py` exercising the regex independently — is `plugins/hoplite/hooks/edge_grammar.py`. The `check-frontmatter` hook applies it to every `edges` entry and in-body `[[wikilink]]` at write time.

## Frontmatter edges

`edges: [<target>, ...]` expresses edges in frontmatter. Each `<target>` is exactly a wikilink target — the same string you would write inside `[[ ]]`, `stereotype::` prefix and all.

- **Identical grammar.** `name`, `namespace:page`, `/subpage`, `#section`, `#^block`, `stereotype::target`, `ghost/<slug>` — every form carries over verbatim; a bare target is an untyped edge.
- **No rendering features.** Display text (`|`) and embedding (`!`) are inline-only; a frontmatter edge is data, not rendered.
- **Equivalence.** `[[refines::circle]]` and `edges: [refines::circle]` are the same edge — the target string is identical, inline versus structured.

## Markdown links

External content only: `[text](https://example.com)`. The wikilink feature set does not apply — a markdown link is display text plus a URL.

- The walker indexes the URL as a graph node, joined by an edge, so external references are backlink-discoverable like any other node.
- A durable or reused external reference earns a proxy note under `docs/proxies/`, then is wikilinked like any internal document.
