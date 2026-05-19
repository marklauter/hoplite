## Philosophy

Notes are the durable layer beneath the conversation. The conversation compacts; the notes do not. The next session reads what this one wrote.

Notes represent the current state of an idea; the journal tells the story of how we got there. The two artifacts are siblings — a wiki page and an engineering notebook — and the taking-notes skill produces only the former. The journal — dated entries, append-only, ordered by time — is a separate skill with a separate shape.

### Externalize to survive compaction

A fact that lives only in the conversation evaporates the moment the context window does. The note is the persistence layer. Anything worth remembering past the next compaction — a hypothesis, a measurement, a dead end, a decision, a reference — is worth a note.

### One topic per note

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
