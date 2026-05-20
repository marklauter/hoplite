  New issues introduced by the edit

  - L47, L67 — stray literal bash outside the backticks: bash `record-note.sh` — save or extend a note. and bash `scan.sh`
  — list and filter notes by structured predicates. Looks like a half-applied fence-language change. Either delete the word
   bash here or delete these bullets entirely (still redundant with the H2 — my original suggestion).
  - L52, L72 — code fences open as ``` (no language) and then have bash  as the first token of the code body. Move bash
  into the fence info string: ```bash and drop the leading bash  inside the block. As-is, the renderer shows users a
  command starting with literal bash bash.
  - L43 anchor break — heading is now ## Record the note — record-note.sh reference, but L92 still links to
  #record-the-note--using-record-notesh. The link is dead. Update the anchor or, simpler, demote the link to plain text:
  Composed by `record-note.sh` from its args.
  - L63 dash inconsistency — ## Finding notes - scan.sh reference uses a hyphen; L43 uses an em-dash. Match L43.
  - L45 comma splice — "The script slugifies the title, saves docs/notes/<slug>.md." Needs and or a period.

  Newly visible (clearer now that the noise is gone)

  - L36 the Memory contrast is the only mention of cross-repo scope; it sits oddly mid-section. Consider promoting it to a
  single line near the top of "Compose the note" so the boundary is established before the exclusions list.
  - L86 → L130 cross-ref is now clean, but L86 itself runs four claims in one paragraph. If you want one more pass: split
  the "When a tag's value matches another note's slug…" sentence — it's the densest one in the doc and easy to gloss past.
