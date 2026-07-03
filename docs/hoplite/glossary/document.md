---
title: document
summary: "A structured markdown file and its representation within the knowledge graph."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
has-a: 
    - "[[resource]]"
    - "[[frontmatter]]"
    - "[[statement]]"
---

A structured markdown file and its representation within the knowledge graph.

## Structure

Yaml frontmatter over a body of markdown prose. Hoplite reads claims and edges from the frontmatter and content from the body.

A document is bound to the graph through a [[resource]]. Its statements — the frontmatter's claims and edges — attach to that resource but describe the document, not the resource; the body stays text behind the search index.
