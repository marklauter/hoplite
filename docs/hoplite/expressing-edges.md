---
title: Expressing edges
summary: "The ways to express an edge — an inline link (wikilink or markdown) or a frontmatter property whose value is a wikilink — Obsidian-native. Any inline link is an edge: an adjacent comment types it, otherwise it defaults to the `links-to` predicate."
tags: [hoplite, edges, spec]
created: 2026-06-20
status: locked
---

# Expressing edges

Hoplite supports the full Obsidian wikilink and property grammar.

There are two places to express edges within a markdown document — the body and the frontmatter:

- In the body, an inline link: a wikilink like `[[circle]]`, or a markdown link like `[circle](circle)`. Either is an edge. A predicate comment beside it types the edge; without one, the edge defaults to the `links-to` predicate (see Inline predicates below).
- In frontmatter, a property whose value is a wikilink, like `cites: "[[circle]]"`. This is a typed edge, and the key (`cites`) is the predicate.

Every inline link is an edge — there is no plain-hypertext link in a Hoplite corpus. `links-to` is what an untyped link means; an explicit predicate overrides it.

## Wikilinks

Edges are created by declaring wikilinks from one document to another.

### Source

The source is the document containing the wikilink declaration.

### Target

The target is the document referenced by the wikilink — a required slug, with an optional path prefix and an optional anchor:

- Slug (required) — the document's filename, like `circle`. A slug alone resolves to that page anywhere in the vault.
- Path prefix (optional) — folders before the slug, joined by `/`, like `lib/shapes/circle`. A namespace that disambiguates same-named pages; the shortest unique path works.
- Anchor (optional) — a section or block within the page: `circle#properties`, a block `circle#^radius-def`, or same-page `#properties`. Section labels are the heading text, spaces included; block ids are letters, numbers, and dashes.

Slug and path segments use the characters `A-Z a-z 0-9 . _ -`. The `.md` extension is optional: `circle` and `circle.md` are the same target.

### Rendering

- Display text — `[[circle|shown text]]`: target first, display text second.
- Embedding — `![[circle]]`: transcludes the target's content in place.

### Inline predicates

A bare inline link defaults to the `links-to` predicate. To type it, attach a predicate in a comment beside the link. Hoplite reads three forms:

- HTML comment — `[[circle]]<!--refines-->`. The default: invisible in Obsidian, on GitHub, and in any renderer.
- Obsidian comment — `[[circle]]%%refines%%`. Invisible in Obsidian only.
- Dataview field — `[refines:: [[circle]]]`. Visible, and renders as literal brackets without the Dataview plugin.

The same comment forms attach to a markdown link: `[circle](circle)<!--refines-->`.

The predicate is a slug (`[A-Za-z0-9._-]`), and the comment sits on the same line, immediately beside the link. The link is untouched in every form, so Obsidian still resolves it and draws the edge — `links-to` by default — while Hoplite reads the predicate. The parser accepts all three; authors emit the HTML comment. (A future setting will choose the emitted form.)

### Ghosts

A ghost is a wikilink whose target has no file yet — an ordinary `[[slug]]`, no special syntax. Obsidian shows it as an unresolved link.

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

`plugins/hoplite/hooks/edge_grammar.py` implements this grammar:

- `TARGET_RE` — the regex above.
- `validate_target` — validates a single target.
- Frontmatter and inline extractors — pull edge targets and inline predicates from a document.

`test_edge_grammar.py` tests the regex directly. The `check-frontmatter` hook runs the validator on every body wikilink and every frontmatter wikilink value at write time.

## Markdown links

A markdown link `[text](target)` is an edge, the same as a wikilink. It defaults to the `links-to` predicate and accepts the same inline predicate comments (`[text](target)<!--cites-->`). A markdown link is just another link syntax.

A markdown target is a CommonMark link destination. An external URL resolves to a `url` node, a relative path to a `document`, and a fragment like `#section` to a same-page anchor.

## Frontmatter edges

A frontmatter edge is a property whose value is a wikilink — the key is the predicate, the value is the target:

```yaml
refines: "[[pi]]"               # scalar — one edge
cites: ["[[shape]]", "[[pi]]"]  # flow list — several, on one line
contrast:                       # block list — several, one per line
  - "[[square]]"
  - "[[triangle]]"
```

- Key — the predicate, like `cites` or `refines`. Keys are one flat open vocabulary: a few are special (read by meaning), and any other key is a predicate.
- Value — a quoted wikilink. Quote it: Obsidian indexes the link only when it's quoted, and unquoted `[[ ]]` isn't valid YAML. Use a scalar for one edge, a list for several.
- Edge or property, decided by value. A wikilink value makes the property an edge; a scalar value like `status: draft` makes it a node property.
- No rendering. Display text (`|`) and embedding (`!`) work only in the body; a frontmatter edge is data.

## Portability

The wikilink grammar is Obsidian-native. Other renderers read the same syntax differently:

- GitHub wiki (Gollum) reverses the pipe order. Obsidian writes `[[target|display]]`, but Gollum reads the first field as the display text and the second as the target — `[[display|target]]`. An aliased wikilink resolves backwards there: Gollum treats the display text as the page name. A bare `[[slug]]` carries no pipe, so it ports unchanged.
