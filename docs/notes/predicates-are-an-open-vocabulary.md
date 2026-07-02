---
title: Predicates are an open vocabulary
summary: "A predicate is an open-vocabulary label naming what an edge asserts — never predefined, never warned on; a new label is a doc change, not a schema migration. Hoplite ships the mechanism and surveys the vocabulary; it does not govern it. Two authoring surfaces — inline wikilink and frontmatter property — materialize identical storage; authors pick by whether the assertion is rhetorical-in-context or categorical. The mechanism sections predate the predicate rename and the triple reversal; read them as history."
tags: [note, hoplite, edges, predicates, design, todo]
aliases: [stereotypes-are-open-vocab-edge-properties]
created: 2026-05-27
status: evolving
---

# Predicates are an open vocabulary

A predicate — recorded through most of this note under its retired name, stereotype — is an open-vocabulary label naming what an edge asserts. The vocabulary is never predefined and never warned on: a new predicate is a doc change, not a schema migration. Hoplite ships the mechanism and surveys the vocabulary so an agent can find the labels in use; it does not govern them — label conventions belong to each corpus's own skills and templates. Two authoring surfaces — inline wikilink and frontmatter property — materialize identical storage; authors pick by whether the assertion is rhetorical-in-context or categorical.

The mechanism sections below predate the stereotype→predicate rename and the triple reversal — `edge_property`, edge kinds, and junction storage are historical. The current model is [[docs/notes/every-triple-position-is-a-node.md]] and [[docs/hoplite/schema.md]].

## Why this abstraction

Two design proposals from this session — `contradicts` and `not-related` — each looked like a new edge provenance. Both collapse into one mechanism under the stereotype framing. `contradicts` is a stereotype labeling a `mentions` edge that argues against its target. `not-related` is a stereotype labeling a `mentions` edge that declines an inferred similarity. Neither adds to the closed enum of edge provenance; both are open-vocab labels on a `declared` edge.

Once the abstraction lands, new stereotypes are parser-and-doc changes only. No schema migration per new label. Authors extend the vocabulary as use cases emerge, the same way tags work today.

## Schema

<!-- caution contains obsolete: superseded by the bare-graph rework. An edge is now a bare attachment + confidence with no "kind"; provenance is a feature concept (intrinsic vs asserted), and the claim leaves are declared (author) vs inferred (engine), not declared/discovered. -->
Edge kind is a closed enum of two, by provenance:

- `declared` — the author asserted the edge: a `[[wikilink]]`, or a markdown link to a URL node.
- `discovered` — the engine inferred it from a shared feature (similarity, co-citation, proximity).

`Edge.confidence` is already a first-class column (shipped earlier this cycle — see [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]]). `declared` carries `1.0`; `discovered` carries its inference score.
<!-- end obsolete -->

Stereotypes do not extend the `edge` schema. They live as `edge_property` rows with the shape `(edge_id, "stereotype", <value>)`, where `edge_id` is the integer `edge.id` of the labeled edge. Same EAV layout as node tags, which sit in `node_property` as `(node_id, "tags", <value>)`.

The `edge` table has an integer `id` primary key and `UNIQUE (src, dst)` — at most one edge per ordered pair, regardless of kind. Since stereotypes label the single `mentions` edge between a pair, multiple stereotype rows per edge are allowed and expected: an author writing `[[B]]<!--supports-->` in one paragraph and `[[B]]<!--questions-->` in another produces one `mentions` edge plus two `edge_property` rows keyed by that edge's `id`.

## Authoring surfaces

Two surfaces inject identical rows. The author picks based on whether the assertion is rhetorical-in-context (lives next to the prose making the claim) or categorical (a document-level fact independent of any paragraph).

### Inline wikilink

A bare inline link defaults to the `links-to` stereotype. To type it, attach the stereotype in a comment beside the link — an HTML comment is the default form (invisible in every renderer); see [[docs/hoplite/expressing-edges.md]] for all three. Sample shapes (in backticks so the resolver does not emit edges from this note):

- `[[docs/notes/foo.md]]<!--contradicts-->` — disagreement with a specific document.
- `[[docs/notes/foo.md|short reason]]<!--supports-->` — endorsement; pipe-alias still works as the human-readable label.
- `[[ghost/some-slug]]<!--not-related-->` — assertion against an unwritten document; composes with ghost targets.

The link itself is untouched, so Obsidian still resolves it and draws the edge; the walker reads the adjacent comment to override the default `links-to` stereotype, then materializes the `mentions` edge plus the `edge_property` row. Parsing the comment beside an already-validated wikilink is a localized change (see [[docs/notes/walker-py-design.md]] "Wikilink mentions edges").

### Frontmatter property

A frontmatter edge is a property whose value is a wikilink: the key is the stereotype, the value is the target. Keys are a flat, open vocabulary — no `document.` or `edge.` prefix (see [[docs/hoplite/frontmatter.md]]). A scalar or list of plain scalars is a node property; a wikilink value is an edge:

```yaml
title: Stereotypes are open-vocab edge properties
summary: A stereotype is an open-vocabulary label...
tags: [note, hoplite, edges, stereotypes]
created: 2026-05-27
contradicts: ["[[foo]]", "[[bar]]"]
supports: "[[baz]]"
not-related: "[[qux]]"
```

Quote the wikilink. Obsidian indexes a link in a property only when it is quoted, and a bare `[[ ]]` is not valid YAML. Use a scalar for one target, a list for several.

Each wikilink value materializes one edge (`src` = this document, `dst` = target, `kind` = `declared`) plus one stereotype property row in `edge_property`. The inline and frontmatter parsers converge on the same writes.

The two surfaces split the stereotype differently: frontmatter carries it as the property key, while an inline link carries it in an adjacent comment and leaves the link bare. Both reduce to the same `edge_property` row, so an author picks by whether the assertion is a document-level fact (frontmatter) or rhetorical-in-context (inline).

## Canonical seed vocabulary

The v1 canonical set, documented in `templates/components/hoplite/mcp-reference.md` next to the edge-kind enumeration:

- `supports` — endorses a claim or framing.
- `contradicts` — argues against a claim or framing. See [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]].
- `not-related` — asserts topical disjointness despite vocabulary overlap. See [[docs/notes/add-not-related-as-a-structural-negative-edge-kind.md]].
- `supersedes` — replaces a specific claim or section.
- `cites` — references an external source; the optional reading of a markdown link to a URL node.

`writing-prose.md` covers the inline and frontmatter syntax with a one-line pointer to the vocabulary list. The vocabulary lives in one place to prevent drift between the authoring guide and the tool reference.

## Open-vocab policy

The parser does not warn on unknown stereotype values. Emergent vocabulary surfaces by use — if `questions` or `derives-from` gets used fifty times across the corpus, it earns canonical status. The same pattern governs tags today.

Authoring discipline: check existing usage before inventing a new stereotype. An audit affordance — a `where` predicate for stereotype usage or a SQL view against the dump — is future work. Without one, synonym drift (`supports` vs `endorses` vs `agrees-with`) accumulates undetected.

## Mention-skip implications

The related-edge aggregate pass already excludes any `(src, dst)` pair connected by a `mentions` edge from the inferred-related pass (the mentions skip-set — see [[docs/notes/walker-py-design.md]] "Aggregate pass: related edges"). The logic does not inspect stereotypes — every `mentions` edge counts.

`not-related` therefore gets its suppression behavior for free under this model. An author writing `[[B]]<!--not-related-->` materializes a `mentions` edge with `stereotype = not-related`, and the existing skip-set logic excludes the pair from the inferred related pass. No code change needed for the suppression mechanism.

## Markdown links stay neutral

Markdown URL links (`[text](https://...)`) produce un-stereotyped `declared` edges to URL nodes — citation is a stereotype now, not a kind, and a bare link asserts none. Link text remains free-form for readability; reserving canonical stereotype words as link text would collide with descriptive use.

For a stereotyped URL reference (an explicit `cites`, say), write a proxy note at `docs/proxies/<slug>.md` carrying the URL plus context, then stereotype an inline wikilink to the proxy or list it as a `<stereotype>: "[[proxy]]"` frontmatter edge. Reuses the existing proxy pattern.

## Out of scope

Two adjacent design problems sit outside the v1 stereotype proposal:

- Migration. The corpus-wide property-key rewrites are done — the keys settled on the flat, Obsidian-native contract in [[docs/hoplite/frontmatter.md]] (`tags`/`created` bare, edges as `<stereotype>: "[[target]]"`). What remains for this stereotype epic is only the *emit path* (parser + walker writing the `edge_property` rows), not any key rename.
- Edge-level properties beyond stereotype. Tagging an existing edge (say, marking it `important`) runs into an addressing problem — which edge gets the property? A stereotype key maps cleanly because its wikilink values name the target documents; a property meant to annotate an already-existing edge has no such handle. Defer until a concrete use case forces the design.

## Open questions

- Default traversal behavior for stereotyped mentions in `relatives()`. When an agent walks a neighborhood, do stereotyped edges follow by default? Deferred to the upcoming expression-language redesign — the right answer may land there rather than as a Pydantic field on `TraversePredicate`.
- Audit affordance for stereotype usage. Authors need a way to see the histogram of stereotype values across the corpus to spot synonym drift before it accumulates. Could be a `where` predicate extension, a dedicated tool, or a SQL view against the dump.

## See also

- [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]] — the contradicts stereotype, one instance of the model.
- [[docs/notes/add-not-related-as-a-structural-negative-edge-kind.md]] — the not-related stereotype, the structural-negative case.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle where `confidence` was promoted to a first-class `Edge` column, the precedent for first-class column vs. property treatment.
- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — adjacent edge-quality work; stereotypes are independent of how `related` confidence gets computed.
- [[docs/notes/properties-subsume-first-class-columns]] — revisits the "title and summary are first-class fields, not properties" claim above: in the current model summary is a property and title is the slug, and the first-class columns collapse into the property concept.
