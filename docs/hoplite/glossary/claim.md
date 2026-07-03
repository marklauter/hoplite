---
title: claim
summary: "A statement asserted about a document in its frontmatter."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
retired: [property]
contrast: "[[predicate]]"
---

A statement asserted about a document in its frontmatter.

## Structure

The key is the claim's predicate — a member of the `claim` namespace (`claim:priority`), licensed for the predicate position. A scalar value makes the statement a claim; a wikilink value makes the key an [[edge]] instead. Value-routed keys parent their values (`priority:high`); literal-routed keys (`title`, `summary`) store out-of-line.
