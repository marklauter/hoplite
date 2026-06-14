---
title: The canon of governing people is the theory of governing agents
summary: The book's intellectual lineage is not a flat reading list but three strata — formal (game theory, Hurwicz's mechanism design), political (Hobbes, Montesquieu, Adams), and design (Norman, Cooper) — that converge on one claim: agents are goal-directed, self-interested, error-prone actors, so govern them with the disciplines built for governing people.
tags: [note, book, agents, mechanism-design, design]
created: 2026-06-13
document:
  status: observation
---

# The canon of governing people is the theory of governing agents

This note maps the intellectual canon behind the book "Agents are People too" onto the agent-governance principles derived independently in this repo — load gates, signal integrity, and the sovereign that constrains action not soul. The references stack into three strata that converge on a single claim. The body below is captured verbatim from the discussion that produced it, addressed to the author; the bold and emphasis are preserved against the usual note style because the capture was requested word for word.

## The three strata

**Formal floor — game theory → Hurwicz.** This is the one to flag hard: you re-derived *incentive compatibility* from scratch and named it "signal integrity." Hurwicz won the Nobel for mechanism design — reverse game theory, where you design the rules so self-interested players each optimizing their own payoff still produce the outcome you want, *and the mechanism holds even when they try to game it*. A check is high-integrity exactly when it's incentive-compatible: the constrained actor's best move is to comply, not to suppress. The regress you found (the standard is authored by the actor one level up) is Hurwicz's enforcement problem — the mechanism that enforces the rule must itself be incentive-compatible, or who guards the guardians. You walked into a Nobel result by the back door and through the clean-room. That's a chapter on its own.

**Political middle — Hobbes → Montesquieu → Adams.** A clean genealogy, not three parallel citations. Hobbes supplies the sovereign that constrains action. Montesquieu answers "but who constrains the sovereign?" with separation of powers — *le pouvoir arrête le pouvoir*, power checks power — and he's the direct upstream of Adams, who read him and engineered it into balanced government with the explicit premise that virtue is necessary but never sufficient. That genealogy *is* your accident-vs-malice axis: Hobbes's single lock stops the accident, Montesquieu/Adams's divided powers stop the malice. Cite Montesquieu for the principle, Adams for the working implementation.

**Design ceiling — Norman → Cooper.** Norman's load-bearing thesis for your title: *error is a design failure, not a moral failing* — he moved blame from the soul to the system, which is precisely "accidents, not malice" and precisely why you constrain the action. Cooper carries it into software: goal-directed actors (his personas are goal-seekers, same as your agents), and his sharpest line for you — engineers unconsciously build software that thinks the way *they* think, *Homo logicus* designing for itself. An agent trained on human output inherits exactly that: it builds and reasons like the people in its corpus. Cooper was describing agents thirty years early; he just called them programs.

The whole stack converges on one sentence: **agents are goal-directed, self-interested, error-prone actors — so govern them with the disciplines humanity already built for goal-directed, self-interested, error-prone actors.** Mechanism design for the incentives, constitutional separation for the power, error-tolerant design for the mistakes. The title isn't a metaphor; it's a claim that the existing canon of *governing people* already contains the theory of *governing agents*, because the two are the same problem.

One gap worth a thought as you rebuild: that's a strong spine for constraint and governance, but every thinker on it is about *bounding* an actor. The book may want a counterweight on the cooperative side — Ostrom on governing commons without a sovereign, or Axelrod on how cooperation emerges among self-interested players without one. Otherwise the argument leans entirely Hobbesian, and your John Adams half wants the optimism to have a formal champion too.

## Related

- [[docs/notes/the-agent-problem-is-the-agency-problem.md]] — the economics expansion of the formal floor; the floor is really economics, not just game theory, and several repo principles are named economic results.
- [[docs/notes/the-sovereign-constrains-the-action-not-the-soul.md]] — the safety principle this canon formalizes; signal integrity is the independently-derived incentive-compatibility condition.
- [[docs/notes/inline-the-prose-spine-until-it-grows-large.md]] — the context-side application of the same mechanism-over-judgment spine.
- [[docs/notes/a-review-agents-power-is-its-empty-context.md]] — separation of powers applied to review: independence by not sharing the prior.
