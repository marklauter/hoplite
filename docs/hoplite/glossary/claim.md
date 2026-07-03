---
title: claim
summary: "A statement asserted about a document."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
retired: [property]
---

A statement asserted about a document.

## Structure

The key is the claim's predicate — a member of the `claim` namespace (`claim:priority`), licensed for the predicate position. A claim states a value about one document; an [[edge]] relates two resources. Claims arrive from more than one hand: the author asserts through [[frontmatter]] — the value's shape signals which is which, a scalar making a claim and a wikilink an edge — and the importer computes its own (`content_hash`, `minhash`). Value-routed keys parent their values (`priority:high`); literal-routed keys (`title`, `summary`, `content_hash`) store out-of-line.
