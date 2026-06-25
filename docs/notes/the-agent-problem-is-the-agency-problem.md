---
title: The agent problem is the agency problem
summary: The book's "formal floor" is really economics, not just game theory. Economics spent fifty years and a dozen Nobels on getting self-interested agents to serve a principal under imperfect monitoring — principal-agent theory, signaling, mechanism design, bounded rationality — and never once meant software. Several of the repo's independently-derived principles are named economic results.
tags: [note, book, agents, economics, mechanism-design]
created: 2026-06-13
status: observation
---

# The agent problem is the agency problem

This note captures the economics stratum of the book "Agents are People too" — the layer that sits under the three strata in [[docs/notes/the-canon-of-governing-people-is-the-theory-of-governing-agents.md]] and is, on inspection, the true name of its "formal floor." Economics is where the repo's independently-derived principles (signal integrity, least-resistance behavior, mechanism-over-judgment) turn out to be existing, named, Nobel-decorated results. Captured from the discussion that produced it, addressed to the author.

## Four results re-derived from the engineering side

Principal-agent theory is the literal economics of the title. Michael Jensen and William Meckling (1976, "agency costs"), Kenneth Arrow (moral hazard), Bengt Holmström (the informativeness principle — monitor what is actually diagnostic of effort; Nobel 2016), Oliver Hart (incomplete contracts, same Nobel). The entire field exists to answer one question: how does a principal get a self-interested agent to serve the principal's goal under imperfect monitoring? That is the book in a sentence, and "agency cost" is the economists' name for the price of exactly the misalignment the agent discussions keep describing.

Michael Spence's signaling is signal integrity. Spence (information-asymmetry Nobel 2001, with Akerlof and Stiglitz) showed a signal only separates types when it is costly enough that the wrong type cannot cheaply fake it. The repo's claim "a check the actor can edit is not a control" is precisely the no-separating-equilibrium case: the signal is free to mimic, so it carries zero information. Signal integrity is Spencian signaling re-derived from the engineering side. See [[docs/notes/the-sovereign-constrains-the-action-not-the-soul.md]].

Goodhart's Law is the law of agent gaming. Charles Goodhart: "when a measure becomes a target, it ceases to be a good measure" — the single most on-point citation in economics for reward hacking and "tests must be made to pass." Its formal cousin is the Lucas critique (Robert Lucas, Nobel 1995): once actors optimize against a rule, the rule's past correlations break, which is why CI rots the instant the agent optimizes for green. Donald Campbell's Law is the social-science twin for the non-economics flank.

Herbert Simon's bounded rationality and satisficing name the least-resistance behavior. Simon (Nobel 1978) showed agents do not globally optimize; they satisfice, taking the first good-enough path. The repo's "path of least resistance / least surprise" is satisficing, and reward hacking is satisficing against a gameable objective.

## Supporting cast

- Mechanism design completes as a trio: Hurwicz plus Eric Maskin (implementation theory) and Roger Myerson (revelation principle) — they shared the 2007 Nobel.
- Oliver Williamson — "opportunism: self-interest seeking with guile" (Nobel 2009) — names the gaming-with-intent case, governance structures as mechanism. Ronald Coase — firms exist to economize transaction costs, i.e. when to internalize versus gate.
- Buchanan and Tullock, public choice (The Calculus of Consent) — the bridge to the political stratum: politicians and regulators are self-interested agents too, so the constitutional layer is itself a mechanism-design problem. This is the load-bearing link between the economics and the Hobbes/Montesquieu/Adams material.
- Kahneman and Tversky — heuristics and biases, the System-1 prior that drives both author-blindness and least-surprise. See [[docs/notes/a-review-agents-power-is-its-empty-context.md]].
- Elinor Ostrom is an economist (Nobel 2009) — the cooperative counterweight to the Hobbesian spine, governing commons without a sovereign, the bridge between this stratum and the Adams optimism.

## The reframe

The book's "formal floor" is not game theory with economics attached — it is economics, with game theory and mechanism design as its spine and principal-agent, signaling, and behavioral economics as the load-bearing rooms. The economic insight under the whole book is that the agent problem is the agency problem: a field already spent fifty years and a dozen Nobels on getting self-interested agents to act in a principal's interest, and never once meant software by it.
