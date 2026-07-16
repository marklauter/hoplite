---
title: A local encoder adds semantic search without leaving the process
summary: The semantic-similarity channel needs a sentence encoder, and a small one runs fully in-process — fastembed (onnxruntime, no torch) for the model, sqlite-vec or a brute-force numpy scan for storage, fused with the existing BM25 via reciprocal rank fusion. No daemon, no network, no API. The standing cost is re-embedding on every write, not disk.
tags: [note, hoplite, mcp, python, semantic-search, embeddings, design]
created: 2026-06-07
status: open
---

# A local encoder adds semantic search without leaving the process

The semantic-similarity channel needs a sentence encoder, and a small one runs fully in-process — fastembed for the model, sqlite-vec or a brute-force numpy scan for storage, fused with the existing BM25 via reciprocal rank fusion. No daemon, no network, no API. The standing cost is re-embedding on every write, not disk.

## What it answers

BM25 and MinHash are lexical: they match shared tokens. Neither catches paraphrase or synonymy. A query for "avoid recomputing" misses a note titled "caching strategy" with no shared words. [[docs/notes/relatedness-signals.md]] names this the semantic-similarity channel and lists semantic embeddings under "needs new capability." This note pins the concrete tool.

An encoder maps each document to a dense vector positioned so meaning maps to geometry. Paraphrases land near each other, and sense-distinct uses of a word separate by context. Nearest-neighbor by cosine over those vectors is semantic search.

## The local stack

The model is weights on disk. After a one-time download from the HuggingFace CDN, it loads from the local cache and runs offline forever. The files can be vendored and pointed at by path so the server never reaches out. Inference is matrix multiplies on CPU; nothing about note content is transmitted.

- encoder — `fastembed` (onnxruntime plus quantized models, no torch) keeps the venv light versus `sentence-transformers`, which pulls in a few hundred MB of torch. A small model (`bge-small-en-v1.5`, ~130MB) embeds hundreds of short docs/sec on CPU.
- storage — vectors live in SQLite alongside the FTS, either as blobs scanned brute-force (cosine over a few thousand vectors is milliseconds) or indexed via the `sqlite-vec` extension. Either keeps the single-file, no-external-service property the rest of Hoplite has.
- fusion — semantic and lexical are complementary, not competing. Embeddings miss exact tokens (identifiers, rare names, exact phrases); BM25 misses paraphrase. Run both and merge rankings with reciprocal rank fusion.

## Quality

Small open encoders score in the high-50s/low-60s on MTEB retrieval, where the best hosted models (Voyage, OpenAI, Cohere) sit mid-60s. For a personal markdown corpus, `small` or `base` is past the point of diminishing returns.

Two limits bite here specifically. The models train on general web/QA text, so project jargon (`smart-zone`, Hoplite internals) gets weaker intuitions than everyday language, though context still clusters it sensibly. The `e5`/`bge` family also wants a `query:`/`passage:` prefix to hit its best numbers; skipping it leaves quality on the table.

The bottleneck won't be model quality. It will be chunking and whether the fusion with FTS is done well. A hosted model isn't worth reaching for until a measured shortfall appears.

## The real cost

Embeddings add a re-embed-on-write obligation: every note edit recomputes its vector, where FTS today reindexes text cheaply. That ongoing compute, not the ~130MB of weights, is the cost to weigh. Cold start adds a second or two of model load, paid once per session lazily on first semantic query, since the server spawns per session.

## See also

- [[docs/notes/relatedness-signals.md]] — the channel taxonomy; semantic similarity is the channel this capability delivers.
- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — the lexical-similarity score for `discovered` edges; semantic vectors are a second, complementary similarity the same fusion could blend.
- [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]] — the rerank pattern `where` already wants; semantic score is another rerank signal.
