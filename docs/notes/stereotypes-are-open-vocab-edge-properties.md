---
title: Stereotypes are open-vocab edge properties
summary: A stereotype is an open-vocabulary label attached to an edge (or document property), stored EAV-style in edge_property parallel to how tags work in document_property. Two authoring surfaces — inline wikilink and class-prefixed frontmatter — materialize identical storage; authors pick by whether the assertion is rhetorical-in-context or categorical.
tags: [note, hoplite, edges, stereotypes, design, todo]
created: 2026-05-27
aliases: []
---

# Stereotypes are open-vocab edge properties

A stereotype is an open-vocabulary label attached to an edge (or document property), stored EAV-style in `edge_property` parallel to how tags work in `document_property`. Two authoring surfaces — inline wikilink and class-prefixed frontmatter — materialize identical storage; authors pick by whether the assertion is rhetorical-in-context or categorical.

## Why this abstraction

[Inference] Two design proposals from this session — `contradicts` and `not-related` — each looked like a new edge kind. Both collapse into one mechanism under the stereotype framing. `contradicts` is a stereotype labeling a `mentions` edge that argues against its target. `not-related` is a stereotype labeling a `mentions` edge that declines an inferred similarity. Neither adds to the closed enum of edge kinds; both are open-vocab labels on the existing `mentions` kind.

[Inference] Once the abstraction lands, new stereotypes are parser-and-doc changes only. No schema migration per new label. Authors extend the vocabulary as use cases emerge, the same way tags work today.

## Schema

[Observation] Edge kinds stay a closed enum of three structural roles:

- `mentions` — authored document → document.
- `cites` — authored document → URL.
- `related` — inferred document ↔ document from MinHash similarity above threshold.

[Observation] `Edge.confidence` is already a first-class column (shipped earlier this cycle — see [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]]). `mentions` and `cites` carry `1.0`; `related` carries its similarity score.

[Inference] Stereotypes do not extend the `Edge` schema. They live as `edge_property` rows with the shape `(src, dst, kind, "stereotype", <value>)`. Same EAV layout as document tags, which sit in `document_property` as `(path, "tags", <value>)`.

[Inference] The primary key on `Edge` stays `(src, dst, kind)`. Multiple stereotype rows per edge are allowed and expected — an author saying `[[supports:B]]` in one paragraph and `[[questions:B]]` in another produces one edge plus two stereotype property rows.

## Authoring surfaces

Two surfaces inject identical rows. The author picks based on whether the assertion is rhetorical-in-context (lives next to the prose making the claim) or categorical (a document-level fact independent of any paragraph).

### Inline wikilink

`[[<stereotype>:<path>]]` — colon-namespace prefix on the wikilink target. Sample shapes (in backticks so the resolver does not emit edges from this note):

- `[[contradicts:docs/notes/foo.md]]` — disagreement with a specific document.
- `[[supports:docs/notes/foo.md|short reason]]` — endorsement; pipe-alias still works as the human-readable label.
- `[[not-related:ghost/some-slug]]` — assertion against an unwritten document; composes with ghost targets.

[Inference] The resolver change is localized to the warning gate at `plugins/hoplite/mcp/src/hoplite/graph.py:327-329`, which currently accepts `docs/` or `ghost/` prefixes. Extending it to recognize `<stereotype>:<path>` shapes and dispatch into the stereotype-emit branch is a single parser change.

### Frontmatter with class prefix

Every frontmatter key gains a mandatory dot-separated class prefix — `document.` or `edge.` — declaring which side of the property graph the key affects. Uniform across scalars and lists:

```yaml
document.title: Stereotypes are open-vocab edge properties
document.summary: A stereotype is an open-vocabulary label...
document.tags: [note, hoplite, edges, stereotypes]
document.created: 2026-05-27
edge.contradicts: [docs/notes/foo.md, docs/notes/bar.md]
edge.supports: [docs/notes/baz.md]
edge.not-related: [docs/notes/qux.md]
```

[Observation] The dot separator avoids the YAML escape pain a colon would cause (a colon inside a plain scalar key disagrees across parsers and linters). Authors write the dotted form without quoting.

[Inference] Each path in an `edge.<stereotype>: [paths]` list materializes one edge (`src` = this document, `dst` = path, `kind` = `mentions`) plus one stereotype property row in `edge_property`. The inline and frontmatter parsers converge on the same writes.

The frontmatter parser also accepts the equivalent nested form, which can read better when a document declares many stereotypes under one class:

```yaml
edge:
  contradicts: [docs/notes/foo.md]
  supports: [docs/notes/bar.md]
  not-related: [docs/notes/baz.md]
```

[Inference] Both shapes normalize to identical `edge_property` rows. If a document mixes shapes that declare the same `edge.<stereotype>`, the parser merges the path lists; silent overwrite is not the behavior.

[Inference] Inline wikilinks keep the colon (`[[stereotype:path]]`), not the dot. The asymmetry exists because filesystem paths contain dots (`docs/notes/foo.md`) — a dot in the inline form would collide with file extensions. Filesystem paths cannot contain colons (Windows enforces that), so the colon is an unambiguous splitter inside the wikilink.

## Canonical seed vocabulary

[Inference] The v1 canonical set, documented in `plugins/hoplite/components/hoplite/mcp-reference.md` next to the edge-kind enumeration:

- `supports` — endorses a claim or framing.
- `contradicts` — argues against a claim or framing. See [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]].
- `not-related` — declares topical disjointness despite vocabulary overlap. See [[docs/notes/add-not-related-as-a-structural-negative-edge-kind.md]].
- `supersedes` — replaces a specific claim or section.

[Inference] `writing-prose.md` covers the inline and frontmatter syntax with a one-line pointer to the vocabulary list. The vocabulary lives in one place to prevent drift between the authoring guide and the tool reference.

## Open-vocab policy

[Inference] The parser does not warn on unknown stereotype values. Emergent vocabulary surfaces by use — if `questions` or `derives-from` gets used fifty times across the corpus, it earns canonical status. The same pattern governs tags today.

[Inference] Authoring discipline: check existing usage before inventing a new stereotype. An audit affordance — a `where` predicate for stereotype usage or a SQL view against the dump — is future work. Without one, synonym drift (`supports` vs `endorses` vs `agrees-with`) accumulates undetected.

## Mention-skip implications

[Inference] Today's `_emit_related_edges` skip-set at `plugins/hoplite/mcp/src/hoplite/graph.py` already excludes any `(src, dst)` pair connected by a `mentions` edge from the inferred-related pass. The logic does not inspect stereotypes — every `mentions` edge counts.

[Inference] `not-related` therefore gets its suppression behavior for free under this model. An author writing `[[not-related:B]]` materializes a `mentions` edge with `stereotype = not-related`, and the existing skip-set logic excludes the pair from the inferred related pass. No code change needed for the suppression mechanism.

## Cites stay neutral

[Inference] Markdown URL links (`[text](https://...)`) produce un-stereotyped `cites` edges. Link text remains free-form for readability; reserving canonical stereotype words as link text would collide with descriptive use.

[Inference] For a stereotyped URL reference, write a proxy note at `docs/proxies/<slug>.md` carrying the URL plus context, then stereotype an inline wikilink to the proxy or list it under `edge.<stereotype>:` in frontmatter. Reuses the existing proxy pattern.

## Out of scope

Two adjacent design problems sit outside the v1 stereotype proposal:

- Migration. Every existing document carries unprefixed frontmatter (`title:`, `summary:`, `tags:`, `created:`). Adopting the class-prefixed shape is a breaking format change requiring a corpus-wide rewrite pass. Tracked for a separate session.
- Edge-level properties beyond stereotype. A frontmatter shape like `edge.tags: [important]` runs into an addressing problem — which edge gets the tags? The flat `edge.<key>: [values]` form maps cleanly when `<values>` are target paths (the stereotype case), and breaks down when `<values>` are property values for an already-existing edge. Defer until a concrete use case forces the design.

## Open questions

- Default traversal behavior for stereotyped mentions in `relatives()`. When an agent walks a neighborhood, do stereotyped edges follow by default? Deferred to the upcoming expression-language redesign — the right answer may land there rather than as a Pydantic field on `TraversePredicate`.
- Audit affordance for stereotype usage. Authors need a way to see the histogram of stereotype values across the corpus to spot synonym drift before it accumulates. Could be a `where` predicate extension, a dedicated tool, or a SQL view against the dump.

## See also

- [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]] — the contradicts stereotype, one instance of the model.
- [[docs/notes/add-not-related-as-a-structural-negative-edge-kind.md]] — the not-related stereotype, the structural-negative case.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle where `confidence` was promoted to a first-class `Edge` column, the precedent for first-class column vs. property treatment.
- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — adjacent edge-quality work; stereotypes are independent of how `related` confidence gets computed.
