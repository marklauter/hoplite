---
name: domain-modeling
description: Use when designing hoplite itself — reducing a term, concept, or decision to its irreducible kernel: resolving terminology against the glossary, stress-testing concept boundaries against the spec, or recording a design decision. The active discipline of changing the model, not reading the corpus for vocabulary.
---

# Domain modeling

Actively build and sharpen hoplite's domain model by reducing each concept to its irreducible kernel as we design — challenging terms and inventing edge cases until only one reading survives — then write it down the moment it crystallises. A leaf concept reduces to a glossary term plus the smallest phrase that unpacks it in the domain. A composite concept reduces to a spec document built from those terms. (Merely *reading* the corpus is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

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

Capture greedily, lock lazily — write a term the moment it's contested with `document.status: evolving`, and let the drift sweep reconcile it; promote to `locked` only when it resolves. Decisions stay lazy: offer a `decision` note only when one is earned.

## During design

Interview me relentlessly about every concept until we reach a shared understanding of its irreducible kernel. For each question, share your recommended answer.

Ask the questions one at a time, waiting for feedback on each before continuing. Asking multiple questions at once is bewildering.

If a question can be answered by exploring the corpus or codebase, then explore before asking.

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

When a kernel resolves, hand it to the skill that owns its form:

- **Term** — a word plus its smallest phrase → the `/glossary` skill.
- **Concept** — composed from locked terms → the `/spec` skill.
- **Decision** — a hard-to-reverse trade-off → the `/decision` skill.
