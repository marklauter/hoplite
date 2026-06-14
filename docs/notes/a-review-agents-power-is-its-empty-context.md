---
title: A review agent's power is its empty context
summary: A fresh review agent catches what a self-review misses because it lacks the author's prior, not because it is smarter — so withholding the author's reasoning is the feature. Hand the reviewer the generation trace and you reload the author's blindness into it.
tags: [note, agents, review, orchestration, design]
created: 2026-06-13
document:
  status: observation
---

# A review agent's power is its empty context

A fresh review agent catches what the author missed because its context is empty, not because it reasons better. Perception is prior plus evidence; the author who built an artifact holds an overwhelming prior over what it says, so the author reads intent into the page and the actual defect is suppressed. A reviewer with no generation trace has a flat prior and sees what is on the page. The reviewer's power is its ignorance of intent, so withholding the author's reasoning is the feature, not a compromise.

## The mistake people get backwards

Inference. The instinct in orchestration is to hand the reviewer everything — the plan, the rationale, "here is why I did it this way, now check it" — to help it understand. That is the precise error. Loading the author's reasoning into the reviewer reinstalls the author's prior, and the reviewer goes blind in exactly the same place the author did. A review by shared context is the judge and the defendant sharing one skull.

The design rule: give the reviewer the artifact and the spec as stated, and starve it of the generation trace. Less context is what makes the second pass independent. An independent branch is independent because it does not share the prior; the moment it shares, the independence is gone.

## Why an agent is worse at self-review than a rested human

Observation. A human recovers from author blindness by forgetting — sleep on it, the prior decays overnight, and you return with flatter eyes that see the page. An agent's context does not decay; it sits at full fidelity until cleared. So an agent reviewing its own output in the same window is worse off than a human who waited, because the human eventually loses the prior and the agent never does on its own. Clearing context is the agent's only sleep, and a fresh subagent is that sleep made instant and total — amnesia by construction. This is the mechanism reason a separate review agent is required for every important artifact, not a redundancy nicety.

## The false positives are a signal, not noise

Inference. The cold reviewer trades false negatives for false positives: the author suppresses real errors, while the fresh agent over-flags, calling an intentional choice a mistake because it lacks the context that was withheld. That over-flagging is diagnostic. The fresh reviewer is the same cold reader the artifact's real audience will be — the next agent after compaction, the user months later. When it misreads an intentional choice, the artifact is not carrying its own context, which is the standalone-section bar the note-writing discipline already demands. The reviewer is the first reader who actually tests it.

## Related

- [[docs/notes/inline-the-prose-spine-until-it-grows-large.md]] — same prior-following spine: a model takes the highest-prior continuation, which suppresses the on-page defect here and skips the corrective context file there. Both argue for designing around the prior rather than asking the model to override it.
