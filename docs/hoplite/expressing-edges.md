---
title: Expressing edges
summary: "The three ways to express an edge: an inline wikilink, a frontmatter property whose value is a wikilink, and a markdown link for external content — Obsidian-native, with the target grammar the two internal forms share."
tags: [hoplite, edges, authoring]
created: 2026-06-20
document.status: evolving
---

# Expressing edges

An [[edge]] links one document to another, and three forms express it: in the body, a [[wikilink]] (untyped) or a markdown link to a URL (external); in frontmatter, a property whose value is a wikilink — typed, the key naming the [[stereotype]]. The two internal forms share one target grammar; a markdown link carries only display text and a URL.

The grammar is Obsidian-native: every target resolves in Obsidian and joins its graph and backlinks. Obsidian draws each edge untyped — it has no edge labels — so Hoplite reads the stereotype from the frontmatter key, the typed layer over the same links Obsidian sees.

## Wikilinks

Internal references, Obsidian-native — every target form below resolves in Obsidian.

### Target

The target is a page path. A segment is `SEG = [A-Za-z0-9._-]` (strict ASCII filename characters; the `.md` extension is optional — just dots in a name). The folder is the [[namespace]]: `/` separates path segments, exactly as Obsidian addresses notes.

- **By name** — `[[circle]]`: resolves to the unique page of that name anywhere in the vault.
- **Path-qualified** — `[[lib/shapes/circle]]`, `[[docs/hoplite/glossary/term]]`: the folder path disambiguates when a name repeats. Obsidian needs only the shortest unique path; the full path always resolves.

There are no colons — the folder path is the only namespace mechanism. `[[docs/hoplite/term]]` is valid and addresses `term` under `docs/hoplite/`.

### Sections and blocks

- **Section** — `[[circle#properties]]`; same page `[[#properties]]`; subheading `[[circle#properties#radius]]`. A section label is the heading text, spaces and all: `[[circle#cross sections]]`.
- **Block** — `[[circle#^radius-def]]`: a single block, finer than a heading. The block id is letters, numbers, and dashes.

### Rendering

- **Display text** — `[[circle|shown text]]`: target first, display text second.
- **Embedding** — `![[circle]]`: transcludes the target's content in place.

### Ghosts

A link whose target has no backing file is a [[ghost]] — Obsidian renders it as an unresolved link, and it surfaces as creatable backlog. No special syntax: a ghost is an ordinary `[[slug]]` that does not resolve yet.

### Grammar

The forms above reduce to one regular grammar:

```
SEG      = [A-Za-z0-9._-]+        # one path segment
HEADING  = [^#^|[]]+              # a section label — heading text, spaces allowed
BLOCKID  = [A-Za-z0-9-]+          # an Obsidian block id
path     = SEG ("/" SEG)*         # folder path; the folder is the namespace
anchor   = "#^" BLOCKID | ("#" HEADING)+
target   = path anchor?           # a page path, optionally anchored
         | anchor                 # OR a same-page anchor
```

As the `TARGET_RE` regex (`re.VERBOSE`):

```
^
(?:
    [A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*               # page path — folder = namespace
    (?:\#\^[A-Za-z0-9-]+|(?:\#[^#^|\[\]]+)+)?           # optional anchor
  | (?:\#\^[A-Za-z0-9-]+|(?:\#[^#^|\[\]]+)+)             # same-page anchor only
)
$
```

There are no colons: `/` is the only separator, so `docs/hoplite/term` parses as a folder path and resolves — the form Obsidian itself uses. A section label is permissive (heading text, spaces included) so links to real headings resolve; a block id is letters, numbers, and dashes, matching Obsidian. Rendering features never appear inside a target: `SEG` excludes `|` and `!`, so a frontmatter edge bearing either fails the match; inline, display text after `|` and a leading `!` embed marker are stripped before matching. The executable form — `TARGET_RE` plus a `validate_target` checker and the frontmatter/inline extractors, with `test_edge_grammar.py` exercising the regex independently — is `plugins/hoplite/hooks/edge_grammar.py`. The `check-frontmatter` hook applies it to every in-body `[[wikilink]]` and every frontmatter `edge.<stereotype>` wikilink value at write time.

## Frontmatter edges

A typed internal edge is a frontmatter property whose value is a wikilink — the key names the relationship, the value points at the target:

```yaml
cites: ["[[shape]]"]          # flow sequence — compact, one line
contrast:                     # block sequence — same value, hyphen per line
  - "[[square]]"
  - "[[triangle]]"
```

- **The key is the stereotype.** Properties are one flat open vocabulary — `title`, `summary`, `tags`, `created`, `status` are the recognized keys; any other key is yours to coin. There is no `edge.` or `document.` namespace; a property named `cites` *is* the `cites` stereotype. Hoplite reads the key as the edge's stereotype.
- **Edge or property, decided by value.** The value's shape assigns the role: a wikilink makes the key a stereotype and the property an edge; a scalar (`status: draft`) makes it a node property. One vocabulary, two roles, no prefix to choose.
- **Value is a quoted wikilink.** The quotes are required — Obsidian indexes a link into its graph and backlinks only from a quoted `[[ ]]` value, and bare `cites: [[shape]]` is not valid YAML (the `[[ ]]` parses as a nested list). Past that it is standard YAML: the two sequences above — flow (`["[[a]]", "[[b]]"]`) and block (a hyphen per line) — are the same value to any YAML parser, so use whichever reads better; a bare scalar `"[[a]]"` works for a single edge. Obsidian reads them all.
- **Typed for Hoplite, connected for Obsidian.** Both read the same edge: Hoplite types it by the key, Obsidian draws it untyped.
- **No rendering features.** Display text (`|`) and embedding (`!`) are inline-only; a frontmatter edge is data, not rendered.
- **Untyped edges are inline.** A bare body `[[target]]` is an untyped edge; to type it, give it a stereotype key in frontmatter.

## Markdown links

External content only: `[text](https://example.com)`. The wikilink feature set does not apply — a markdown link is display text plus a URL.

- The walker indexes the URL as a graph node, joined by an edge, so external references are backlink-discoverable like any other node.
- A durable or reused external reference earns a proxy note under `docs/proxies/`, then is wikilinked like any internal document.
