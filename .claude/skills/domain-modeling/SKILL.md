---
name: domain-modeling
description: Use when designing hoplite itself — resolving terminology against the glossary, stress-testing concept boundaries against the spec or the MCP source, or recording a design decision. The active discipline of changing the model, not reading the corpus for vocabulary.
---

# Domain modeling

Actively build and sharpen hoplite's domain model as you design: challenge terms, invent edge-case scenarios, write the glossary and decisions down the moment they crystallise. (Merely *reading* the glossary for vocabulary is not this skill — any skill does that. This is for when you change the model.)

The model lives in the corpus, addressed by path:

```
docs/hoplite/
├── glossary/             ← the domain model: one node per term
│   ├── README.md         ← hand-maintained index + entry format
│   └── <term>.md         ← title, summary, status, category, aliases, edge.contrast
└── *.md                  ← spec prose that depends on the terms
docs/journal/             ← design decisions (ADR-equivalent)
plugins/hoplite/mcp/src/  ← ground truth
```

Capture greedily, lock lazily — write a term the moment it's contested with `document.status: evolving`, and let the drift sweep reconcile it; promote to `locked` only when it resolves. Decisions stay lazy: a journal entry only when one is earned.

## During design

Probe the model before asserting: `where({"tagged": "glossary", "text": "<term>"})` ranks entries; `relatives(...)` walks a term's neighborhood.

### Challenge the term
Conflicts with a glossary entry or its `aliases` → call it out. "You said *kind*, but the glossary locks `kind` and `stereotype` as distinct — which do you mean?"

### Sharpen fuzzy language
Vague or overloaded term → propose the canonical one. "You're saying *link* — the declared edge, or the rendered markdown? Different things."

### Stress-test a boundary
Probe a relationship with a concrete case, not the abstraction. "A `[[...]]` to a URL — declared edge or discovered?"

### Cross-reference the source
A stated behavior → check `plugins/hoplite/mcp/src/` agrees. "`discovered.md` calls edges symmetric, but the walker emits one direction — which is right?"

### Sweep for drift
`relatives(from_, edge_types=["discovered"], tagged="glossary")` finds terms the engine reads as adjacent with no `declared` link between them — unreconciled overlap. Merge, alias, or draw the contrast.

## Record

- **Resolved term** → write `docs/hoplite/glossary/<term>.md` in the format documented in `docs/hoplite/glossary/README.md` (exemplar: `kind.md`); add it to the README `## Terms` index; record any boundary as reciprocal `edge.contrast`. The one-line `summary` is the probe — if it won't write, the term isn't grasped yet. No implementation detail.
- **Decision** → invoke the `journaling` skill, but only when all three hold:
  1. **Hard to reverse** — changing your mind later costs.
  2. **Surprising without context** — a future reader asks "why this way?"
  3. **A real trade-off** — genuine alternatives, one chosen for reasons.

Call `refresh()` after any write so later queries see it.
