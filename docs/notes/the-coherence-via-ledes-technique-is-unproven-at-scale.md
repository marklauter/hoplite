# The Coherence-via-ledes technique is unproven at scale

Tags: todo,skills,reviewing,wiki,audit-mode-followup
The whole-wiki Coherence pass technique (read structural files + every page lede + build terminology map) has not been validated on a real audit.

## Observation

- reviewing-wiki/SKILL.md and writing-wiki/SKILL.md document the technique: read `_Sidebar.md` and `Home.md` in full, read the lede of every other page, deep-read only in-scope pages and their immediate neighbors. The reviewer builds a one-time terminology and section-ownership map from the structural pass.
- Asserted context budget in the skill: "fits comfortably for 10-50 page wikis." No measurements taken.
- Plumber's wiki has ~20 pages. DynamoDbLite (where the original no-diff incident happened on 2026-05-15) was similar size.

## Interpretation

- The technique is plausible for the typical software-project wiki size (10-50 pages) and likely fits one context window.
- Hypothesis: at 100+ pages, lede-only reads still fit but the synthesized terminology map gets unwieldy. Unclear if Claude can hold a 100-entry term-ownership index in working memory while evaluating Coherence findings.
- Hypothesis: the technique degrades gracefully — at scale, the reviewer reads fewer ledes and accepts coverage gaps rather than failing.

## Next

- Run a real wiki audit on Plumber or another mid-size wiki and observe whether the technique produces useful Coherence findings.
- If audits hit context limits, revisit options: persisted lede-summary cache, sub-section batching, or explicit scope flag (e.g. `--section <name>` on `changes.sh --all`).
