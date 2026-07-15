---
title: Open Knowledge Format (OKF) v0.1 — specification
summary: "Google's OKF: markdown concept documents with YAML frontmatter in a directory tree, distributed as a bundle. One required key (`type`), untyped markdown links, and two reserved filenames (`index.md`, `log.md`). The interchange format Hoplite claims native support for."
tags: [note, reference, okf, frontmatter, interchange]
created: 2026-07-14
---

# Open Knowledge Format (OKF) v0.1 — specification

Google's OKF: markdown concept documents with YAML frontmatter in a directory tree, distributed as a bundle. One required key (`type`), untyped markdown links, and two reserved filenames (`index.md`, `log.md`). The interchange format Hoplite claims native support for.

## Links

- SPEC.md (raw) — the normative v0.1 spec: [SPEC.md](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
- Repository: [github.com/GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog)
- Announcement blog post — the source of the README's OKF paragraph: [How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/)

## Notes

- **Bundle** is the distribution unit: a self-contained directory tree of markdown concept documents. **Concept** is one document. The concept id is the file path minus `.md` — `tables/users.md` is `tables/users`. This matches Hoplite's path-derived document identity.
- `type` is the only required key, and it is an open vocabulary with no central registry — `BigQuery Table`, `Metric`, `Playbook`. Consumers must tolerate unknown values.
- Recommended keys: `title`, `description` (one-sentence summary), `resource` (a URI for the underlying asset), `tags` (a YAML list), `timestamp` (ISO 8601 last-modified).
- Producers may add arbitrary keys, and consumers must preserve unknown keys when round-tripping. The frontmatter model is flat and open, the same shape as Hoplite's.
- Cross-links are markdown links only — no wikilinks. Two forms: bundle-relative absolute, `[customers](/tables/customers.md)`, and ordinary relative, `[other](./other.md)`. Links are untyped; the spec says relationship semantics come from the surrounding prose. Consumers must tolerate broken links.
- Two reserved filenames. `index.md` is a directory listing and carries **no** frontmatter — except the root `index.md`, the only place a bundle may declare `okf_version: "0.1"`. `log.md` is a change history grouped under ISO 8601 date headings. Every other `.md` file is a concept.
- Conformance is thin: parseable frontmatter on every non-reserved file, a non-empty `type` on each, and the reserved files shaped as specified. A consumer must not reject a bundle for missing optional fields, unknown types or keys, broken links, or a missing `index.md`.
- Body sections are conventional, not normative: `# Schema`, `# Examples`, `# Citations`.

## Used by

- [[docs/hoplite/frontmatter.md]] — Hoplite's frontmatter standard. OKF's keys land as claims under the open-vocabulary rule; `type` is not a Hoplite special key.
- [[docs/hoplite/expressing-edges.md]] — Hoplite's edge grammar. OKF's untyped markdown links are exactly Hoplite's `links-to` default.
