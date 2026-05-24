"""Wall-clock feel: MinHash signature() over docs/**/*.md."""

from __future__ import annotations

import statistics
import time
from pathlib import Path

from hoplite.minhash import signature

REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS = sorted((REPO_ROOT / "docs").rglob("*.md"))


def main() -> None:
    bodies = [(path, path.read_text(encoding="utf-8")) for path in CORPUS]
    total_bytes = sum(len(body.encode("utf-8")) for _, body in bodies)
    total_words = sum(len(body.split()) for _, body in bodies)

    # Warm the (a_i, b_i) cache so the first measured doc isn't penalized.
    signature("warm up text for the ab table cache" * 3)

    per_doc_ns: list[int] = []
    overall_start = time.perf_counter_ns()
    for _, body in bodies:
        t0 = time.perf_counter_ns()
        signature(body)
        per_doc_ns.append(time.perf_counter_ns() - t0)
    overall_ns = time.perf_counter_ns() - overall_start

    per_doc_us = [ns / 1_000 for ns in per_doc_ns]
    per_doc_us.sort()
    n = len(per_doc_us)
    p50 = per_doc_us[n // 2]
    p95 = per_doc_us[min(n - 1, int(n * 0.95))]

    print(f"corpus:           {n} files, {total_words:,} words, {total_bytes:,} bytes")
    print(f"wall clock total: {overall_ns / 1e6:8.2f} ms")
    print(f"per-doc mean:     {statistics.mean(per_doc_us):8.2f} us")
    print(f"per-doc median:   {p50:8.2f} us")
    print(f"per-doc p95:      {p95:8.2f} us")
    print(f"per-doc max:      {max(per_doc_us):8.2f} us")
    print(f"per-doc min:      {min(per_doc_us):8.2f} us")
    print(f"throughput:       {n / (overall_ns / 1e9):8.1f} docs/sec")
    print(f"throughput:       {total_words / (overall_ns / 1e9) / 1000:8.1f} kwords/sec")

    # Extrapolation to the spec's "personal corpus" scale.
    avg_doc_ms = overall_ns / 1e6 / n
    print()
    print("extrapolated:")
    print(f"  500 docs:    ~{500 * avg_doc_ms:7.1f} ms")
    print(f"  5,000 docs:  ~{5_000 * avg_doc_ms:7.1f} ms")
    print(f"  50,000 docs: ~{50_000 * avg_doc_ms / 1000:7.1f}  s")


if __name__ == "__main__":
    main()
