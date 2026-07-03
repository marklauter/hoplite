---
title: document
summary: "A structured markdown file and its representation within the knowledge graph."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
has-a: 
    - "[[resource]]"
    - "[[frontmatter]]"
    - "[[feature]]"
---

A structured markdown file and its representation within the knowledge graph.

## Structure

Yaml frontmatter over a body of markdown prose. Hoplite reads metadata features from the frontmatter and content features from the body.

A document is bound to the graph through a [[resource]]. Its features — frontmatter metadata and body content — attach to that resource but describe the document, not the resource.
