---
name: domain-modeling
description: Use when designing the domain model — reducing a term, concept, or decision to its irreducible kernel: resolving terminology against the glossary, stress-testing concept boundaries against the spec, or recording a design decision. The active discipline of changing the model, not reading the corpus for vocabulary.
---

# Domain modeling

Actively build and sharpen the domain model by reducing each term, concept, or decision to its irreducible kernel during design — challenging terms and inventing edge cases until only one reading survives — then write it down the moment it crystallises. A term reduces to a glossary entry: the word plus the smallest phrase that unpacks it in the domain. A concept reduces to a spec document built from those terms. A decision reduces to a note recording the trade-off. (Reading the corpus for vocabulary is not this skill; this is for changing the model.)

The model lives in the corpus, addressed by path:

```
docs/specs/               ← composite kernels: concepts built from the terms (affordances, frontmatter, graph)
docs/glossary/            ← the living domain model, one term per leaf
├── README.md             ← hand-maintained index
└── <term>.md             ← title, summary, status, aliases, and edge properties
docs/journal/             ← the why: the design path, each tradeoff and its reasoning
docs/notes/               ← current state: findings and scratch
docs/decisions/           ← hard-to-reverse trade-offs, ADR-equivalents
docs/todos/               ← action items the corpus tracks
```

Capture greedily, lock lazily — write a term the moment it's contested with `status: evolving`, and let the drift sweep reconcile it; promote to `locked` only when it resolves. Decisions stay lazy: offer a `decision` note only when one is earned.

## During design

Interview me relentlessly about every concept until we reach a shared understanding of its irreducible kernel. For each question, share your recommended answer.

Ask the questions one at a time, waiting for feedback on each before continuing. Asking multiple questions at once is bewildering.

If a question can be answered by exploring the corpus or codebase, then explore before asking.

### Challenge the term

Conflicts with a glossary entry or its `aliases` → call it out. "You said *bill*, but the glossary locks `invoice` (the request for payment) and `receipt` (the proof of it) as distinct — which do you mean?"

### Sharpen fuzzy language

Vague or overloaded term → propose the canonical one. "You're saying *link* — the declared edge, or the rendered markdown? Different things."

### Stress-test a boundary

Probe a relationship with a concrete case, not the abstraction. "A `[[...]]` to a URL — declared edge or discovered?"

### Cross-reference the source

A stated behavior → check the source agrees. "The spec calls edges symmetric, but the walker emits one direction — which is right?"

### Narrow to one

More than one definition survives → apply the next constraint — a scenario, the code, a contrast — to kill one, and repeat until a single reading is left. "Two senses of *X* are live — what case admits only one?"

### Defer the decision

A term or boundary being pinned before the information exists to decide well → hold it open as `evolving` and name the trigger that will force the choice. "We won't lock the edge vocabulary into an enum yet — keep it open, and let real edges show which relationships earn a definition."

### Sweep for drift

Reread the glossary for two entries that name the same idea or contradict each other — unreconciled overlap. Merge, alias, or draw the contrast. When staying open costs more than deciding, lock it.

## Durability - recording the kernel

Before recording a kernel, load the skill that owns its form:

- Term — a word plus its smallest phrase → the `hoplite-skills:glossary` skill.
- Concept — composed from locked terms → the `hoplite-skills:spec` skill.
- Decision — a hard-to-reverse trade-off → the `hoplite-skills:decision` skill.
- Note — more than a fleeting thought → the `hoplite-skills:taking-notes` skill.
- Todo — a task to be completed or a follow up needed → the `hoplite-skills:todo` skill.
