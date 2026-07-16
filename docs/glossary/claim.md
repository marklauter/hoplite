---
title: claim
summary: "A statement asserted about a document."
tags: [glossary]
created: 2026-06-19
status: evolving
retired: [property, tags]
contrast: "[[relationship]]"
---

A statement asserted about a document.

## Structure

The key is the claim's predicate — a member of the `claim` namespace (`claim:priority`), licensed for the predicate position. A claim states a value about one document; a [[relationship]] relates two resources. Claims arrive from more than one hand: the author asserts through [[frontmatter]] — the value's shape signals which is which, a scalar making a claim and a wikilink a relationship — and the importer computes its own (`content_hash`, `minhash`). Value-routed keys parent their values (`priority:high`); literal-routed keys (`title`, `summary`, `content_hash`) store out-of-line. A bag claim carries a set of labels: `tags` is the frontmatter form — the bag as authored — and the importer decomposes it into one statement per label under the singular key (`tag:note`, `tag:design`). Repeated assertion yields one statement, so bags are sets.

## Contrasts

- `relationship` — a claim states a value about one document; a relationship relates two resources.
