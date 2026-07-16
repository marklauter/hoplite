---
title: namespace
summary: "A resource that parents other resources — the structure of the address space."
tags: [hoplite, glossary]
created: 2026-07-03
status: evolving
---

A resource that parents other resources — the structure of the address space.

## Structure

A resource is a namespace exactly when resources live under it. Addresses are chains of namespace names; short forms resolve shortest-unique. The recursion grounds at `meta:meta` — meta, the fixed point, is its own namespace and parents the four structural namespaces: `relationship`, `claim`, `document`, `url`. Keys parent their values; namespace membership carries a resource's kind and its predicate-licensing.
