---
title: document
summary: "A structured markdown file."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
is-a: "[[node]]"
has-a: 
    - "[[frontmatter]]"
    - "[[feature]]"
---

A structured markdown file.

## Structure

Frontmatter — the YAML block — over a body of markdown prose. Hoplite reads metadata features from the frontmatter and content features from the body.

In the graph, a document is a [[node]] enriched: the bare node holds identity, and the document is the properties and body hanging off it — a labeled node plus a body of content.
