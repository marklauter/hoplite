# Default rhetorical context

Defaults for the ten rhetorical-context slots, used when a downstream skill is silent on a slot. Downstream skills override per-slot in their own `## Rhetorical context` section in SKILL.md; unmentioned slots fall back to the values here.

- Writer: contributor — someone with stake in the project, presumed knowledgeable about the subject.
- Voice: declarative, terse — direct claims without hedging.
- Ethos: expert — the writer is presumed authoritative within the subject's scope.
- Stance: neutral — describes rather than advocates, except in vision and design genres where position-taking is the point.
- Audience: another engineer — developer-facing by default; downstream may narrow to learner, operator, oncall, end user, etc.
- Subject: varies by artifact type — downstream must declare.
- Genre: reference — the most general technical-writing default; downstream may pick tutorial, how-to, explanation, vision or design, specification, ADR, note, or journal.
- Tone: professional, even-keeled — neither warm nor cold; addresses the reader as a colleague.
- Register: authoritative-declarative-terse — direct, position-taking, no hedging.
- Intent: varies by artifact type — downstream must declare.

Two slots (subject, intent) have no universal default and must be declared by every downstream — the value is too artifact-specific to default usefully.
