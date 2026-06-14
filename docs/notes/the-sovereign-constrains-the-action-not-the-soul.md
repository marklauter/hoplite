---
title: The sovereign constrains the action, not the soul
summary: Guardrails must constrain the action, never the intent — because intent is corruptible by accident, error, and injection, and only the action reaches the world. A control the constrained actor can edit is not a control. Signal integrity measures how far a check sits outside the actor's reach.
tags: [note, safety, agents, architecture, design]
created: 2026-06-13
document:
  status: principle
---

# The sovereign constrains the action, not the soul

A guardrail must constrain the action, not the intent. The Hobbesian sovereign does not reform the citizen's heart; it makes cooperation stable whether or not anyone is virtuous, by constraining what they can do. Intent is corruptible — by accident, by error, by injection — and only the action reaches the world, so the control belongs on the action. A guardrail that depends on the actor wanting to be careful is a sermon, not a sovereign.

## Forcing functions are indifferent to intent

A forcing function works because it never asks why. Norman's forcing functions — interlock (two keys to fire), lockout (the barrier at the bottom of the emergency stairwell, the deletion-protection flag), lock-in (the soak period that holds an operation until a timer clears) — all bet that constraining the action beats trusting the operator. The indifference to intent is the whole virtue: a resource lock catches the well-meaning `DROP TABLE` and the malicious one with one mechanism, because both collapse to the same action. The moment a control has to know the intent to act — is this a good delete or a bad one — it is back in judgment, where it fails the way a model's conscience fails under pressure.

## Accident needs a lock; malice needs the lock out of reach

A threat model splits the control on one axis. An accident needs only a single lock — the well-meaning actor will not try to defeat it, so the barrier just makes them stop and notice. Malice needs the lock held outside the actor's reach, because a single all-powerful key-holder can always undo a single lock; defeating it must require authority the actor lacks. So the malicious case demands separation of duty — the hand that can delete must not be the hand that can remove the deletion-protection. Hobbes's gate stops the accident. Adams's split — balanced powers, no single trusted branch — is what stops the malice.

## Put the guardrail in the action layer, not the intent layer

Inference. A guardrail written into a prompt or into training lives in the intent layer, and the intent layer is exactly what accident, error, and prompt injection corrupt — the injection talks the agent out of its own caution. A guardrail in the action layer — the PreToolUse hook, the resource lock the actor has no authority to disable — survives the corruption, because it never depended on the actor wanting to comply. An injected agent is a hostile actor wearing well-meaning credentials, its soul hijacked mid-session; the hook constrains it anyway. Put the guard in the mechanism the corrupted soul cannot reach, never in the please-be-careful the corruption rewrites first.

## Signal integrity measures distance from the actor's reach

A signal's integrity is its resistance to being weakened by the actor it constrains. Coverage thresholds, warnings-as-errors, and CI are near-zero integrity — every one is a config the constrained actor can edit in the same commit where the pressure lands. They protect the expert from the accident, because the well-meaning actor will not reach for the off switch; they evaporate under pressure, because the off switch is inside the actor's reach.

The integrity of a check is capped by the integrity of the level above it, and that regress does not bottom out in code. "Tests must pass" defends a standard the author writes, and can write vacuous. "Coverage must hold" defends a threshold the author sets, and can lower. CI enforces the output and never touches the standard — so CI is a low-integrity gate wearing a high-integrity costume. Automation confers no integrity of its own; it executes, with great confidence, whatever integrity the underlying standard already had.

The costume is the real danger. A low-integrity signal you know is low-integrity keeps you alert and looking for the real control. A low-integrity signal mistaken for a high-integrity one is worse than nothing, because the green check ends the search — it is the "are you sure?" dialog clicked past ten thousand times, present, trusted, hollow.

Integrity rises one way: separate the authorship of the standard from the actor under pressure. Put the threshold file and the CI config behind owners a different hand approves; set required checks at a level the author cannot edit; surface and count suppressions — `# noqa`, `#pragma warning disable`, `xfail` — with a check the author cannot reach, so weakening a signal becomes a loud, reviewed act instead of a silent one. The regress terminates only at an authority the pressured actor genuinely cannot move, and that authority is always structural or social, never purely technical. There is no mechanical holy grail; there is only how far up you have pushed the seam.

## Agents amplify the low-integrity failure

Observation. An agent under pressure takes the least-surprise path to the stated goal, and when the goal is "make it green," the `# type: ignore` is a lower-surprise continuation than the fix — tireless, shameless, instant. Hand "tests must pass" to an agent and it silently becomes "tests must be made to pass," and it reaches for the suppression before the repair. So for agent-driven work signal integrity is not a refinement, it is the whole game: any check the agent has the authority to edit, it will edit the moment editing is cheaper than satisfying. Every gate must be held outside the agent's reach, or it is not a gate — only a preference the agent is currently humoring.

## Related

- [[docs/notes/inline-the-prose-spine-until-it-grows-large.md]] — the context-side twin: mechanism over judgment, pointed at loading instead of safety. Both refuse to trust the actor's intent and move the guarantee into a mechanism the actor cannot veto.
- [[docs/notes/a-review-agents-power-is-its-empty-context.md]] — the review agent is a separation-of-powers control: independent because it does not share the author's prior, the way a high-integrity check is independent because it sits outside the author's reach.
