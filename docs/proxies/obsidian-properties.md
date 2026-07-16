---
title: Obsidian Properties — frontmatter parity reference
summary: "Obsidian's Properties help page — the canonical syntax for YAML frontmatter properties: supported types, internal links in properties (quoted `[[ ]]`), and the characters invalid in link targets. The reference Hoplite's edge and property model targets for parity."
tags: [note, reference, obsidian, properties, frontmatter]
created: 2026-06-21
---

# Obsidian Properties — frontmatter parity reference

Obsidian's Properties help page — the canonical syntax for YAML frontmatter properties: supported types, internal links in properties (quoted `[[ ]]`), and the characters invalid in link targets. The reference Hoplite's edge and property model targets for parity.

## Links

- Properties (help): [obsidian.md/help/properties](https://obsidian.md/help/properties)

## Notes

- Properties are a flat, open vocabulary; recognized types include Text and List. Internal links are supported in both — a text property `link: "[[Note]]"`, or a list property with `- "[[Note]]"` items.
- Internal links in properties must be surrounded with quotes. The quoting is what makes Obsidian index the link into the graph and backlinks; a bare path string is plain text to it.
- Invalid characters in link targets: `# | ^ : %% [[ ]]`. The barred colon is why Hoplite's target grammar is colon-free and addresses namespaces by folder path.

## Used by

- [[docs/specs/expressing-edges]] — Hoplite's edge grammar and frontmatter edge model, written for Obsidian parity.
