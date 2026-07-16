---
title: Inline the prose spine until it grows large
summary: Markdown-authoring skills mail-merge the shared prose spine into each skill (the template model) rather than shipping it modular or behind a referenced file, because every deferred load is unreliable — inline is the only model that guarantees the spine is present once the skill loads. Revisit the inlining only if spine size times co-load count grows large; never revisit it toward lazy loading.
tags: [note, decision, skills, architecture, hoplite]
created: 2026-06-13
status: decided
---

# Inline the prose spine until it grows large

The markdown-authoring skills keep the build-time template model — the shared prose spine is a component mail-merged into each consuming skill, so the spine is present in the body the moment the skill loads. The rejected alternatives are the armory additive model (spine ships once, consumers load as deltas that depend on it being already loaded) and progressive disclosure (a thin skill points to a reference file the model reads on demand). Both lose for one reason: every load they defer to a model decision is unreliable.

## Every deferred load is the same unreliable gate

Observation. Three mechanisms defer a load to the model choosing to pull content into context, and all three fail the same way:

- Auto-trigger — description-match deciding "is there a skill for this request?"
- Sibling invoke — the armory additive model, where "the model will invoke them if installed" (Anthropic's own framing; dependency management is not a first-class skill mechanism).
- Progressive disclosure — a skill body saying "read xyz.md before doing abc."

Each puts a gate between the content and the context, and the gate is the model's judgment. Empirically the gate leaks: skills under-trigger across operators, sibling skills go uninvoked, and a "read the C# guidance first" pointer gets skipped because the model reads its own prior as sufficient.

The failure is worst exactly where the content matters most. Inference. The content most worth loading is content that corrects a confident-but-wrong default — "here is how we do C#, against your instincts." That content looks obvious to the model that needs it, so the model skips fetching it. Corrective value is inversely correlated with the model's willingness to lazily load it: the more a file is worth pulling, the less likely deferred loading pulls it. Anthropic's "don't state the obvious" guidance misses this corollary — the non-obvious corrective reads as obvious to the model whose default it corrects.

The rule that falls out: for corrective content, eager-inline or it will not be there. Lazy loading is only safe for content the model reliably chooses to pull, and corrective content is by definition not that.

## Inline collapses two gates into one

Inference. This is the load-bearing argument for inlining, stronger than any failure-mode or token-cost comparison.

Getting any skill into context is already one unreliable gate — a human has to invoke it, and humans forget. Inline makes the spine ride that single gate: once the skill is in, the spine is already present, with no second decision. Modular and progressive disclosure each bolt a second unreliable gate onto the first, so reliability multiplies — two judgment calls in series, not one. The only reliable load is an eager one: content mechanically present before the model acts, not fetched on a judgment the model's wrong prior will veto.

So the inline-vs-modular choice is not "template system vs additive model" — the mail-merge build is orthogonal to inline-vs-reference. It is: put the spine through one gate (inline) or two (modular, progressive disclosure). One gate wins.

## Two cost pools — the scarce one is not body tokens

Observation. Skill cost splits into two pools that are easy to conflate:

- Listing tokens — at session start Claude builds a listing of every registered skill's name and summary and scans it to decide what to trigger. Always-on, one slot per registered skill, against a small fixed budget. This budget is the real scarcity — roughly 30 skills exhausts it in practice.
- Body tokens — the skill body, paid only on load, against the full ~1M-token window. Cheap; a 75-line spine duplicated across a few skills is rounding error there.

The consequence reorders the decisions. Inline-vs-modular lives entirely in the body pool, the cheap one, so spine duplication is near-free and the inlining decision rests on the gate argument above, not on tokens. The scarce pool is touched by a different lever: how many things you register as skills at all. Registering a skill spends a listing slot; reference content that is not a registered skill spends none. This is why staging the markdown-authoring tools in `quary/` rather than as skills is the load-bearing budget decision — it dodges the pool that is actually full. Modular and inline both register the same skills, so neither helps the listing budget; only not-registering does.

## The threshold that flips inlining — and the one that does not

Inline while the spine stays small. The trigger to re-evaluate is spine size times co-load count: a roughly 500-line spine routinely co-loaded four or five at once makes body-pool duplication real in both tokens and attention, and shipping the spine once could win. Record what the spine grows to.

The escape hatch at that threshold is not progressive disclosure. Inference. A large spine behind an on-demand file read is still a deferred load through the unreliable gate, and the larger it is the more it tends to carry exactly the corrective content the model will skip. If the threshold ever forces the spine out of every body, the replacement must stay eager — load it once at session start by deliberate human invocation, not lazily by model decision.

## Discipline if the spine ever ships modular

If the threshold flips and the spine ships once with delta consumers, two rules hold. Deltas must stay pure deltas — armory's `reviewing-wiki` already failed this by self-containing instead of layering on `reviewing-prose`, which voids the share-once benefit the moment it happens; enforce purity in the build. And name the dependency in the delta's own body ("assumes the prose spine is loaded") — one line, no body-pool cost, the cheap insurance for when the agent fires a delta standalone.

## Loading is human-driven — why the gate argument holds

Observation that grounds the whole note. Ambient skills do not auto-trigger reliably: description tuning is fragile, varies by operator, and humans forget to invoke. In practice the operator hand-loads the two or three skills they know they need at session start. This is why the gate framing is the right one — there is no reliable automatic load to design around, only the single deliberate human invocation, and the design goal is to make everything the skill needs ride that one invocation rather than a second model decision.

## Related

- [[docs/todos/refactor-taking-notes-to-ambient-instructions-model.md]] — taking-notes and journaling already migrated off the armory additive model to the template system; this note records why that direction is right, where it would reverse, and the gate principle behind it.
- The prose spine component lives at `plugins/hoplite/components/prose/writing-prose.md`; `quary/` holds the armory source skills (`writing-prose`, `reviewing-prose`, `writing-wiki`, `reviewing-wiki`) staged for factoring into the template system.
