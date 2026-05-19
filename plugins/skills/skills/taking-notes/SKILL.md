---
name: taking-notes
description: Use when the user asks to write something down, save something for later, record something, take a note, or capture an open question. Produces atomic, titled wiki pages under docs/notes/ — discoveries and unresolved questions are equally first-class — that always represent the latest state of the idea; git keeps the history.
---

# Taking notes

Note-authoring knowledge for markdown notes. Loads alongside `writing-prose` and specializes the rhetorical context for the note artifact: audience is the next session, intent is to externalize one idea per file so the work outlives the conversation. Each note represents the current state of an idea; git carries the history. Read the patterns below as the form the note artifact takes under those constraints — the template is the default shape, the discipline is the durable rule.

## Instructions

Ensure the `writing-prose` skill has been load before composing any notes.

## Philosophy

Notes are the durable layer beneath the conversation. The conversation compacts; the notes do not. The next session reads what this one wrote.

Notes represent the current state of an idea; the journal tells the story of how we got there. The two artifacts are siblings — a wiki page and an engineering notebook — and the taking-notes skill produces only the former. The journal — dated entries, append-only, ordered by time — is a separate skill with a separate shape.

### Externalize to survive compaction

A fact that lives only in the conversation evaporates the moment the context window does. The note is the persistence layer. Anything worth remembering past the next compaction — a hypothesis, a measurement, a dead end, a decision, a reference — is worth a note.

### One topic, one page

Each note covers one topic. The title names it; the slug is the file. Two topics get two notes, linked. Stuffing a second topic into an existing note breaks dedup, breaks scan, and breaks the link graph — the second topic has no title of its own and cannot be found by it.

### Title is identity

The title is what the note is, not what it is about. "Cache TTL is 300s" is a title; "Cache investigation" is a topic header pretending to be a title. The slug derives from the title, so the title is also the URL. Renaming the title means renaming the file and updating inbound links; treat it like renaming a function.

### Observation before interpretation

Record the observable fact before the meaning assigned to it. "Endpoint returned 503 at 14:22" is observation; "the service is overloaded" is interpretation. Conflating them poisons later analysis — the interpretation gets cited as if it were the measurement. Two separate sentences, often two separate sections, keep the boundary visible.

### Label speculation

A hypothesis stated as fact is misinformation aimed at future self. The note labels what is observed, what is inferred, and what is guessed — and never lets the labels blur. "Maybe the cache is stale" belongs in an Interpretation section or under a "Hypothesis:" prefix; "the cache TTL is 300s per config" belongs in Observation. The labels are the contract.

### Negative results are notes

A dead end documented prevents the dead end being repeated. The next session, or the same session after compaction, does not see the reasoning that ruled out an approach — only the conclusion. Writing "tried X, did not work because Y" is the cheapest insurance against doing X again next week. A note titled for the dead end is as legitimate as a note titled for the answer.

### Open questions are notes too

A question that goes unrecorded gets re-asked next session. Writing it down — even with no answer yet — captures what is unknown, why it matters, and what would resolve it. The note's title states the question; the body holds partial knowledge and the path toward an answer. Discoveries and questions are peers: the discovery says "here is what is known," the question says "here is what is not known yet." When the answer arrives, the same note evolves to record it; the title may pivot from interrogative to declarative.

### Link liberally

Wiki notes earn their value from the graph. When a note references a concept that has — or could have — its own page, link to it. A dangling link to a page that does not yet exist is a feature, not a defect: it marks the topic as worth a page when the next session has the context to write one.

### Always the latest state; git is the history

Notes are totally mutable. A note represents the current understanding of its topic — not a record of prior belief. When the understanding changes, the note changes; the old text goes away. No "previously we thought X" sections, no `-v2.md` companion files, no superseded markers. The revision history lives in git. A new file is for a new topic; the same file evolves to reflect the current truth about its own topic.

### The note is the artifact

Once the note is written, the work of recording is done. The chat does not recite the note back; the file under `docs/notes/` is the deliverable.

## Guidance

Concrete patterns for taking notes against the principles above.

### Location and filename

- Notes live under `docs/notes/` at the repo root. The directory is committed to git; the revision history is the change log.
- Filename: `<slug>.md`. The slug is the title lowercased, non-alphanumerics replaced with dashes, leading and trailing dashes trimmed, capped at 80 characters.
- The slug is mechanically derived from the title — never hand-edited. Renaming a note means changing the title and regenerating the file.
- No date prefix. Notes are wiki pages, not journal entries. A dated diary belongs in a separate `journal` skill.

### The note template

```
# <one-line title — the H1>

Tags: <comma-separated, optional>
<one-line summary>

## Observation
<observable facts, measurements, references>

## Interpretation
<inferences, hypotheses, guesses, labeled as such>

## Next
<the next concrete action, or `none` if the topic is settled>
```

Line 1 is the H1. Line 2 is blank. Lines 3-4 are the scannable head — tags, summary. Line 5 is blank, then the body sections. `list-notes.sh` reads the head; the body is for humans and future sessions.

The Observation/Interpretation/Next split is the default shape for investigation notes. Reference notes and decision notes use the sections that fit the topic — the template is a starting point, not a straightjacket. Question notes use the same default sections with a different reading: Observation = what is known so far, Interpretation = current guesses, Next = what would answer the question. The scannable head is non-negotiable; the body shape adapts.

### When to write a note

Notes are user-directed, not agent-autonomous. The trigger is an explicit request from the user. Watch for phrases like:

Discovery-shaped triggers:

- "write this down"
- "save this for later"
- "record this"
- "take a note"
- "note that..."
- "let's not forget..."
- "remember this for the repo" (distinct from memory — see below)

Question-shaped triggers:

- "open question:"
- "we should figure out..."
- "we don't know X yet"
- "track this as a question"
- "park this for later"
- "outstanding question:"

The content to capture is whatever the user just said, observed, decided, or wondered — the request points back to it. When the request is ambiguous, ask once: "as one note titled X, or split across topics?" The user's framing is the title; do not invent a title that abstracts away from what they said. For a question, the title is the question itself, phrased interrogatively.

### When not to write a note

- The user did not ask. Notes are explicit-request artifacts. The autonomous version of this is the memory system — different scope, different mechanism.
- Information already documented in the code, CLAUDE.md, or git history. Notes do not duplicate authoritative sources; they link to them.
- Information that belongs in long-term memory (user profile, persistent feedback, cross-project preferences). The memory system is for facts that span repos and sessions; notes are repo-scoped and shared via git.
- Conversational ephemera — recap of what was just said, summary of what was just tried. The note captures the durable finding, not the transcript leading to it.

### Dedup before writing

- `list-notes.sh` or `query.sh` is the first stop. Scan for an existing note on the topic before opening a new one — `query.sh` lets you intersect title, tag, and summary predicates.
- A note on the same topic exists: open it and update it. Wiki pages evolve; do not write `cache-ttl-300s-v2.md`.
- A note on an adjacent topic exists: write the new note and link the two. Adjacent is not same.
- The topic does not warrant its own page: link from the existing note to the underlying source instead.

### Linking notes

- Reference another note by filename in prose: `see [cache-ttl-300s](cache-ttl-300s.md)`.
- Use `Tags:` for thread membership: a tag like `auth-investigation` lets `list-notes.sh` filter all notes on the thread.
- Dangling links to pages that do not yet exist are acceptable — they mark candidates for future notes.

## Validation

"What gets measured gets managed" (Drucker, in spirit). The note set is the measurement of what this codebase has learned about itself. Validation here is the discipline that keeps the set scannable — head fields present, titles unique, link graph intact.

### The script set

Three scripts ship under `${CLAUDE_PLUGIN_ROOT}/skills/taking-notes/scripts/`. Portable POSIX bash; runs on Linux, macOS, and Windows (Git Bash, WSL).

- `take-note.sh [--force] <title> <tags> <summary>` — body piped on stdin. Slugifies the title, refuses to overwrite without `--force`, writes `docs/notes/<slug>.md`. The slug is mechanically derived; the writer does not choose it.
- `list-notes.sh [<tag>]` — reads the head of each `docs/notes/*.md` and emits one block per note: title, tags, summary, filename. With a tag argument, filters to notes whose `Tags:` line contains that tag.
- `query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]` — multi-predicate scan. Each flag is optional; flags AND together. Title and summary match substring case-insensitive; `--tag` matches exactly within the comma-separated `Tags:` line; `--xtag` excludes notes where the named tag is present. Output mirrors `list-notes.sh`.

### Output discipline

- `take-note.sh`: success is silent — the file is the artifact. Failure prints the validation error to stderr and exits non-zero.
- `list-notes.sh`: success prints the formatted note list, or `no notes` when `docs/notes/` is empty or missing. Tag filter prints only matches; no matches prints an explanatory line.
- `query.sh`: success prints the formatted matches in the same block format as `list-notes.sh`, or `no matches` when nothing satisfies the predicates. Exit code is 0 in both cases — a clean empty result is success.

### Gate policies

When a note is malformed, the rule is: fix the note.

- A note without a one-line summary in the head is a defect. The summary is what the scanner reads.
- A note whose body restates the summary verbatim is a defect. The summary is the head; the body is the evidence and reasoning.
- A note whose title and slug disagree (manual rename without regenerating the slug) is a defect. The title and the filename are one fact in two places; they agree.
- A note that covers two topics is a defect. Split it.
- A note that duplicates an existing note is a defect. Merge them.
