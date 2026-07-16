---
title: uri
summary: "A resource's identity."
tags: [glossary]
created: 2026-06-19
status: locked
has-a: "[[slug]]"
---

A resource's identity.

## Details

A case-insensitive name, unique within its namespace; the presented address is the namespace chain, resolved shortest-unique (see [[docs/specs/schema.md]]). Corpus and vocabulary uris are relative references — RDF resolves relative references against a base, the vault in the cross-repo model; url resources are absolute. For a document, the uri is its folder path and [[slug]]: `docs/glossary/uri`.
