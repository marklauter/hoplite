---
title: fact
summary: "An intrinsic feature."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
is-a: "[[feature]]"
contrast: "[[claim]]"
---

An intrinsic feature.

## Examples

- The document's path and file name.
- Its word count, or that its body opens with an H1 — read straight off the file.
- Its file timestamp or git authorship — given by the file's history, not by anyone. (A `created:` or `author:` frontmatter value, by contrast, is a claim — the author typed it.)
- A fingerprint of its content, such as its MinHash — computed deterministically from the bytes, asserted by no one. (The *similarity edge* derived from comparing two fingerprints, by contrast, is inferred — a claim.)

## Contrasts

- `claim` — a fact is intrinsic, true by the document's own existence; a claim is advanced as true and can be contested.
