---
title: Abstraction is summary-keyed random-access memory
summary: The mind compresses a vast concept into a single word and moves up and down abstraction layers at will — not lossy summarization but a compact key over retained content, faulted in on demand. The same architecture is the LLM long-context frontier (landmark attention) and the thing Hoplite implements over a corpus. The hard part is never storage; it is the index, and the index is judgment.
tags: [note, book, agents, memory, cognition]
created: 2026-06-13
status: observation
---

# Abstraction is summary-keyed random-access memory

The mind compresses a huge concept into a single word and moves up and down abstraction layers at will. That is not lossy summarization — the full concept is retained and the word is its key, faulted into working memory on demand. The same scheme is the LLM long-context frontier and the thing Hoplite already implements over a markdown corpus. Across all three the hard part is never storage; it is the index, and the index is judgment. This note captures the state of that thread for the book.

## The mechanism: a key over retained content, not a compressed copy

Two schemes must not be confused. Lossy summarization replaces content with a smaller copy and discards the original — irreversible loss. Summary-keying keeps the full content in cold storage and places only a compact key in the active working set; the key faults the full content back in when it is needed. Nothing is discarded, the working set stays small, and access is random rather than prefix-sequential. The objection that summarizing throws information away applies only to the first scheme; the second is what the mind and the frontier architectures actually do.

## The lossiness migrates, it does not vanish

Inference. Retaining everything moves the loss out of the stored data and into the retrieval cue. A detail still sitting in cold storage but not advertised by its key is unreachable, because a reader attending only to the key never gets the signal to fault it in — the page survives, the line in the index that points to it is gone. To write a key that surfaces exactly what an arbitrary future question will need, you would have to know the question. So the irreducible problem is never "what to keep" — keeping everything solves that — but "what to advertise," which is the same can't-predict-the-query problem relocated one level up. The index is judgment; the storage is mechanism. See [[docs/notes/the-sovereign-constrains-the-action-not-the-soul.md]] for the judgment-vs-mechanism and signal-integrity spine this rides on.

## The human mind runs this architecture

A word is the summary-key for a concept, and fluent thought is rapid traversal up and down the abstraction layers — collapsing detail into a token to reason at altitude, faulting it back in when a step needs the specifics. Expertise is richer keys: a chess master chunks a board into a few meaningful units where a novice sees thirty-two pieces, and recalls full positions from those chunks. High fluid intelligence looks like a good control policy over the layers — moving between abstract and concrete without losing the thread. And humans inherit the same failure mode the architecture predicts: tip-of-the-tongue is a faulted key with a broken pointer; you cannot recall what you never encoded a cue for, even though the experience is "in there." Forgetting is usually addressability loss, not storage loss.

## The LLM frontier runs it too

The published architecture is almost exactly the proposal. Landmark Attention (Mohtashami and Jaggi, 2023 — titled, without embellishment, "Random-Access Infinite Context Length for Transformers") gives each block a representative landmark token; attention scores landmarks first and faults in only the blocks whose landmark scores high. Memorizing Transformers keep old keys and values in an external store and pull the top-k back by similarity. MemGPT pages full content in and out of a small resident window by recall. The residual hard parts are where the research lives: causal and positional coherence when hot-swapping key for full content (the full block's vectors were computed at original positions against the original prefix), and the fault-in policy itself, which is chicken-and-egg — the model attends to the key to decide whether it needs the full content, so the key's fidelity bounds the decision, and the policy must be learned rather than hand-set.

## Hoplite is this architecture, externalized

Hoplite is summary-keyed random-access memory built at the corpus layer. Full documents sit in cold storage on disk; the `summary`, `tags`, and FTS index are the resident keys; `where()` scores those keys and faults in the few full documents that matter — landmark attention over a notebook. This reframes the editorial discipline: the note skill's insistence on a faithful, front-loaded lede is not style fussiness, it is the defense against addressability loss. A note whose summary fails to advertise the fact you will later search for is a landmark token that scores zero — on disk, never recalled. The economy and consistency rules are the indexing-and-eviction policy for an agent's long-term memory.

## The spine for the book

Memory's unsolved problem is not capacity, it is the cue-and-eviction policy: what to advertise and when to fault in, decided before you know what you will be asked. Keep-everything is the deterministic mechanism; the index over it is the probabilistic judgment. The book thread: agents need this memory architecture, humans already are it, and the same judgment-vs-mechanism tension that governs context loading and safety governs memory — the storage can be made lossless, but the index can never be made free of judgment.

## Related

- [[docs/notes/a-review-agents-power-is-its-empty-context.md]] — the prior problem from the other side: the author can't predict at write time which detail a future reader needs, the same blindness that makes the perfect index impossible.
- [[docs/notes/the-agent-problem-is-the-agency-problem.md]] — the economics stratum; a key that fails to advertise its content is a low-integrity signal in Spence's sense.
- [[docs/notes/the-canon-of-governing-people-is-the-theory-of-governing-agents.md]] — the book's lineage this thread joins.
