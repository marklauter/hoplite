---
title: Kingo PDL — Zanzibar rewrite calculus source
summary: Mark Lauter's Kingo is a Zanzibar-style ACL engine implementing PDL (policy description language), the rewrite calculus HQL inherits. Holds canonical URLs for the README (PDL syntax and semantics) and the AclReader/AclWriter source (a working userset evaluator and writer).
tags: [note, reference, kingo, pdl, hql, zanzibar, acl]
created: 2026-05-27
---

# Kingo PDL — Zanzibar rewrite calculus source

Mark Lauter's Kingo is a Zanzibar-style ACL engine implementing PDL (policy description language), the rewrite calculus HQL inherits. Holds canonical URLs for the README (PDL syntax and semantics) and the AclReader/AclWriter source (a working userset evaluator and writer).

## Links

- Repository: [github.com/marklauter/kingo](https://github.com/marklauter/kingo)
- README — introduces PDL syntax and semantics: [README.md (raw)](https://raw.githubusercontent.com/marklauter/kingo/refs/heads/main/README.md)
- AclReader.cs — read-side userset evaluation against the rewrite expressions: [AclReader.cs (raw)](https://raw.githubusercontent.com/marklauter/kingo/refs/heads/main/src/Kingo.Acl/AclReader.cs)
- AclWriter.cs — write-side tuple authoring and relation maintenance: [AclWriter.cs (raw)](https://raw.githubusercontent.com/marklauter/kingo/refs/heads/main/src/Kingo.Acl/AclWriter.cs)

## Used by

- [[docs/notes/hoplite-predicates-are-hql-rewrites-over-typed-relations.md]] — HQL's source calculus. The operator skeleton (`!`, `&`, `|`, `direct`, `computed`, `tuple`) is what HQL inherits from PDL; the C# implementation shows how a userset rewrite engine binds to tuple storage.
