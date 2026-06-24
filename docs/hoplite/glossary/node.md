---
title: node
summary: "A resource's addressable point in the graph — identity, and nothing more."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
has-a: "[[uri]]"
---

A resource's addressable point in the graph — identity, and nothing more.

## Structure

A node is the bare vertex: an addressable point identified by a [[uri]]. It holds identity only. Everything specific to a resolved document — title, summary, fingerprints, body — hangs off it on the [[document]], not on the node. A node exists for every addressable resource, written or not: a document, a [[ghost]], or an external url.
