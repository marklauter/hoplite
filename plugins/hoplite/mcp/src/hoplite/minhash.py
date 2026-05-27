"""MinHash signatures and Jaccard similarity over node bodies.

Pure, I/O-free module the write flow calls when materializing `:related`
edges (see docs/hoplite/architecture.md#minhash-signatures).
Contract: text-in / structured-value-out / structured-value-in /
float-out. No SQLite, no file I/O, no edge logic — those live in the
write flow.

Algorithm
---------
1. Tokenize the text on Unicode whitespace, lowercased.
2. Build word n-grams of width `shingle_size` (joined on single spaces).
   Bodies shorter than `shingle_size` words produce zero shingles and
   yield the sentinel signature defined below.
3. For each shingle, compute one 64-bit base hash via blake2b.
4. Derive `k` independent hashes via the universal-hashing linear
   transform `h_i(x) = (a_i * x + b_i) mod M61`, where M61 = 2**61 - 1
   is a Mersenne prime and the `(a_i, b_i)` table is derived
   deterministically from a hardcoded salt.
5. The signature is the per-position minimum across all shingles.

Edge cases
----------
- Empty or too-short text (fewer than `shingle_size` words) yields a
  signature of all-`_MAX_HASH` sentinel values. This keeps Jaccard's
  identity property (`jaccard(empty, empty) == 1.0`) while making
  `jaccard(empty, anything_real) == 0.0` with overwhelming probability
  — no real hash will collide with the sentinel.
- Mismatched signature lengths in `jaccard` raise `ValueError`. This
  is a programmer bug, not a domain failure.

On-disk format
--------------
`to_bytes` packs the signature as `k * 8` bytes, little-endian unsigned
64-bit integers (`<Q` format). `from_bytes` inverts. Matches
docs/hoplite/architecture.md#minhash-signatures (k 64-bit
hashes, ~1024 B blob). The `_SALT` constant carries a `v1` suffix as
the format version marker; bumping it invalidates all stored
signatures.

Determinism
-----------
The `(a_i, b_i)` table is derived once per `k` value from a hardcoded
salt and cached. Signatures are bit-identical across process
invocations.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from functools import cache
from hashlib import blake2b
from typing import Final

__all__ = [
    "DEFAULT_K",
    "DEFAULT_SHINGLE_SIZE",
    "DEFAULT_THRESHOLD",
    "Signature",
    "from_bytes",
    "jaccard",
    "signature",
    "to_bytes",
]


DEFAULT_K: Final[int] = 128
DEFAULT_SHINGLE_SIZE: Final[int] = 5
DEFAULT_THRESHOLD: Final[float] = 0.10


_M61: Final[int] = (1 << 61) - 1
# Sentinel sits one past the universal-hash output range. Real hashes
# are produced by `% _M61` so they're strictly less than _M61; the
# sentinel can never collide with a real hash. Fits in uint64 for
# `struct.pack("<Q")`.
_MAX_HASH: Final[int] = _M61
_SALT: Final[bytes] = b"hoplite-minhash-v1"


@dataclass(frozen=True, slots=True)
class Signature:
    """A MinHash signature: a fixed-length vector of 64-bit values.

    Values lie in `[0, _M61]` for signatures produced by `signature()`,
    with `_M61` reserved as the sentinel for empty / too-short text.
    Real hash positions are always strictly less than `_M61`, so the
    sentinel never collides with a real hash. Construct directly only
    when round-tripping through bytes or building test fixtures;
    normal callers go through `signature()`.
    """

    values: tuple[int, ...]


@cache
def _derive_ab_table(k: int) -> tuple[tuple[int, int], ...]:
    """Derive `k` pairs `(a_i, b_i)` for the universal-hashing transform.

    Each pair is generated deterministically from `_SALT` plus the
    index. `a_i` is forced odd and non-zero so the transform stays
    invertible under any odd modulus; `b_i` is reduced mod `_M61`.
    """
    pairs: list[tuple[int, int]] = []
    for i in range(k):
        a_seed = blake2b(_SALT + struct.pack("<I", 2 * i), digest_size=8).digest()
        b_seed = blake2b(_SALT + struct.pack("<I", 2 * i + 1), digest_size=8).digest()
        a_raw = int.from_bytes(a_seed, "little")
        b_raw = int.from_bytes(b_seed, "little")
        a_i = (a_raw % (_M61 - 1)) | 1
        b_i = b_raw % _M61
        pairs.append((a_i, b_i))
    return tuple(pairs)


def _base_hash(shingle: str) -> int:
    return int.from_bytes(blake2b(shingle.encode("utf-8"), digest_size=8).digest(), "little")


def signature(
    text: str,
    *,
    k: int = DEFAULT_K,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
) -> Signature:
    """Compute the MinHash signature of `text`.

    Tokenizes lowercase-then-whitespace-split, builds word n-grams of
    width `shingle_size`, and reduces to `k` per-position minimums of
    the universally-hashed shingle values. Returns the sentinel
    all-`_MAX_HASH` signature when the body has fewer than
    `shingle_size` words.
    """
    if k < 1:
        raise ValueError(f"k must be >= 1; got {k}")
    if shingle_size < 1:
        raise ValueError(f"shingle_size must be >= 1; got {shingle_size}")

    tokens = text.lower().split()
    if len(tokens) < shingle_size:
        return Signature(values=(_MAX_HASH,) * k)

    ab_table = _derive_ab_table(k)
    mins = [_MAX_HASH] * k

    for start in range(len(tokens) - shingle_size + 1):
        shingle = " ".join(tokens[start : start + shingle_size])
        base = _base_hash(shingle)
        for i, (a_i, b_i) in enumerate(ab_table):
            h = (a_i * base + b_i) % _M61
            if h < mins[i]:
                mins[i] = h

    return Signature(values=tuple(mins))


def jaccard(a: Signature, b: Signature) -> float:
    """Estimate Jaccard similarity from two equal-length signatures.

    Returns the fraction of positions at which the two signatures
    agree. Identical signatures score 1.0; signatures with no agreeing
    positions score 0.0. Raises `ValueError` when the signatures differ
    in length — that's a programmer bug, not a domain failure.

    Two empty (`len == 0`) signatures score 1.0 by convention; they
    can't be produced by `signature()` but can arise from
    `from_bytes(b"")`.
    """
    if len(a.values) != len(b.values):
        raise ValueError(
            f"signature length mismatch: {len(a.values)} vs {len(b.values)}",
        )
    if len(a.values) == 0:
        return 1.0
    agreements = sum(1 for x, y in zip(a.values, b.values, strict=True) if x == y)
    return agreements / len(a.values)


def to_bytes(sig: Signature) -> bytes:
    """Pack a signature as `len(sig.values) * 8` little-endian uint64 bytes."""
    return struct.pack(f"<{len(sig.values)}Q", *sig.values)


def from_bytes(data: bytes) -> Signature:
    """Unpack a signature from `to_bytes` output.

    Raises `ValueError` if `data` is not a whole multiple of 8 bytes —
    corrupt blob, can't be salvaged here. The write-flow boundary will
    reframe as a domain error when it adopts this module.
    """
    if len(data) % 8 != 0:
        raise ValueError(
            f"signature byte length must be a multiple of 8; got {len(data)}",
        )
    count = len(data) // 8
    if count == 0:
        return Signature(values=())
    return Signature(values=struct.unpack(f"<{count}Q", data))
