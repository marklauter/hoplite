---
name: domain-modeling
description: Use when designing hoplite itself — resolving terminology against the glossary, stress-testing concept boundaries against the spec or the MCP source, or recording a design decision. The active discipline of changing the model, not reading the corpus for vocabulary.
---

# Domain modeling

Actively build and sharpen hoplite's domain model as you design: challenge terms, invent edge-case scenarios, reduce each concept to its irreducible kernel — a leaf concept to a glossary term plus the smallest phrase that unpacks it in the domain, a composite concept to a spec document built from those terms — and write it down the moment it crystallises. (Merely *reading* the corpus is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

The model lives in the corpus, addressed by path:

```
docs/hoplite/             ← the spec corpus
├── glossary/             ← leaf kernels: one term each
│   ├── README.md         ← hand-maintained index
│   └── <term>.md         ← title, summary, status, category, aliases, edge.contrast
└── *.md                  ← composite kernels: concepts built from the terms (affordances, frontmatter, graph)
docs/journal/             ← the why: the design path, each tradeoff and its reasoning
docs/notes/               ← current state: findings, decisions, scratch (mixed bag)
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

### Narrow to one

More than one definition survives → apply the next constraint — a scenario, the code, a contrast — to kill one, and repeat until a single reading is left. "Two senses of *X* are live — what case admits only one?"

### Defer the decision

A term or boundary being pinned before the information exists to decide well → hold it open as `evolving` and name the trigger that will force the choice. "We won't lock the stereotype vocabulary into an enum yet — keep it open, and let real edges show which stereotypes earn a definition."

### Sweep for drift

`relatives(from_, edge_types=["discovered"], tagged="glossary")` finds terms the engine reads as adjacent with no `declared` link between them — unreconciled overlap. Merge, alias, or draw the contrast. This is the deadline on deferral: when staying open costs more than deciding, lock it.

## Record

Each kernel leads with discipline here; the mechanics live in a companion file, read it when you write.

- **Term** → the kernel is the term plus the smallest phrase that resolves it against its `document.category`; reduce by collapsing synonyms into `aliases`, stripping mechanism out to the term it belongs to, and splitting an overloaded word into separate entries; locked when the next cut costs meaning. How: read `term-mechanism.md`.
- **Concept** → the kernel is a concept composed from locked terms, reduced to the smallest spec that still carries it; locked by the same cut test. How: read `concept-mechanism.md`.
- **Decision** → record only what is hard to reverse, surprising without context, and a genuine trade-off — absent any one, it's noise:
  1. **Hard to reverse** — changing your mind later costs.
  2. **Surprising without context** — a future reader asks "why this way?"
  3. **A real trade-off** — genuine alternatives, one chosen for reasons.

  How: read `decision-mechanism.md`.
