---
title: document
summary: "A structured markdown file and its representation within the knowledge graph."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
is-a:
    - "[[structured-markdown-file]]"
has-a: 
    - "[[node]]"
    - "[[frontmatter]]"
    - "[[feature]]"
---

A structured markdown file and its representation within the knowledge graph.

## Structure

Yaml frontmatter over a body of markdown prose. Hoplite reads metadata features from the frontmatter and content features from the body.

A document is bound to the graph through a node. Its features — frontmatter metadata and body content — attach to that node but describe the document, not the node.
