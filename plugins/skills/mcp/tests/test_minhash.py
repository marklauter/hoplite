"""Tests for hoplite.minhash."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hoplite.minhash import (
    DEFAULT_K,
    DEFAULT_SHINGLE_SIZE,
    Signature,
    from_bytes,
    jaccard,
    signature,
    to_bytes,
)

# --- example-based ------------------------------------------------------------


_TEXT_A = (
    "the quick brown fox jumps over the lazy dog while the sun rises "
    "above the silent valley and dew clings to every blade of grass"
)
_TEXT_B = (
    "an unrelated paragraph about distributed systems and write-ahead "
    "logs in databases that survive crashes by replaying their journal"
)


def test_identical_text_identical_signature() -> None:
    assert signature(_TEXT_A) == signature(_TEXT_A)


def test_determinism_across_calls() -> None:
    first = signature(_TEXT_A)
    second = signature(_TEXT_A)
    assert first.values == second.values


def test_different_text_low_jaccard() -> None:
    sig_a = signature(_TEXT_A)
    sig_b = signature(_TEXT_B)
    assert jaccard(sig_a, sig_b) < 0.5


def test_self_jaccard_is_one() -> None:
    sig = signature(_TEXT_A)
    assert jaccard(sig, sig) == 1.0


def test_jaccard_symmetric_example() -> None:
    sig_a = signature(_TEXT_A)
    sig_b = signature(_TEXT_B)
    assert jaccard(sig_a, sig_b) == jaccard(sig_b, sig_a)


def test_jaccard_in_unit_interval_example() -> None:
    sig_a = signature(_TEXT_A)
    sig_b = signature(_TEXT_B)
    score = jaccard(sig_a, sig_b)
    assert 0.0 <= score <= 1.0


def test_empty_and_too_short_share_sentinel_signature() -> None:
    # Empty and any text shorter than shingle_size produce the same
    # sentinel signature — uniform across positions.
    sig_empty = signature("")
    sig_short = signature("one two three four")  # four words; default shingle_size=5
    assert sig_empty == sig_short
    assert len(sig_empty.values) == DEFAULT_K
    assert all(v == sig_empty.values[0] for v in sig_empty.values)


def test_empty_jaccard_with_empty_is_one() -> None:
    assert jaccard(signature(""), signature("")) == 1.0


def test_empty_jaccard_with_real_is_zero() -> None:
    real_sig = signature(_TEXT_A)
    assert jaccard(signature(""), real_sig) == 0.0


def test_shingle_size_one_treats_short_text_as_real() -> None:
    # With shingle_size=1 a single word is enough to form a shingle, so
    # the result is not the sentinel signature.
    sentinel = signature("")
    sig = signature("hello", shingle_size=1)
    assert sig != sentinel


def test_realistic_overlap_estimate() -> None:
    # Constructed to give true Jaccard = 0.5. With a 10-word shared
    # prefix and 3 unique words on each side (shingle_size=5):
    #   - 6 fully-shared shingles (positions 0..5)
    #   - 3 unique shingles per doc (positions 6..8, spanning the
    #     prefix-suffix boundary)
    # Intersection=6, union=12, true Jaccard = 0.5. The k=128 MinHash
    # estimate is binomial(128, 0.5)/128; std ~ 0.044, well inside the
    # +/-0.15 tolerance the brief specifies.
    shared = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    doc_a = f"{shared} lambda mu nu"
    doc_b = f"{shared} xi omicron rho"
    estimate = jaccard(signature(doc_a), signature(doc_b))
    assert 0.35 <= estimate <= 0.65  # ±0.15 tolerance around the 0.5 true value


def test_jaccard_mismatched_length_raises() -> None:
    long_sig = signature(_TEXT_A)
    short_sig = Signature(values=(0,) * 64)
    with pytest.raises(ValueError, match="signature length mismatch"):
        jaccard(long_sig, short_sig)


def test_signature_zero_k_raises() -> None:
    with pytest.raises(ValueError, match="k must be >= 1"):
        signature(_TEXT_A, k=0)


def test_signature_zero_shingle_size_raises() -> None:
    with pytest.raises(ValueError, match="shingle_size must be >= 1"):
        signature(_TEXT_A, shingle_size=0)


def test_lowercase_tokenization() -> None:
    # Case-insensitive: uppercase variant produces the same signature.
    upper = _TEXT_A.upper()
    assert signature(_TEXT_A) == signature(upper)


# --- byte round-trip ----------------------------------------------------------


def test_to_bytes_length_matches_k_times_eight() -> None:
    sig = signature(_TEXT_A)
    assert len(to_bytes(sig)) == DEFAULT_K * 8


def test_round_trip_example() -> None:
    sig = signature(_TEXT_A)
    assert from_bytes(to_bytes(sig)) == sig


def test_round_trip_sentinel_signature() -> None:
    sig = signature("")
    assert from_bytes(to_bytes(sig)) == sig


def test_from_bytes_empty_returns_empty_signature() -> None:
    assert from_bytes(b"") == Signature(values=())


def test_from_bytes_bad_length_raises() -> None:
    with pytest.raises(ValueError, match="multiple of 8"):
        from_bytes(b"abc")


def test_default_constants_match_spec() -> None:
    # Day-one defaults from implementation-sqlite-hybrid.md#minhash-details.
    assert DEFAULT_K == 128
    assert DEFAULT_SHINGLE_SIZE == 5


# --- properties (hypothesis) --------------------------------------------------


@given(text=st.text())
def test_determinism_property(text: str) -> None:
    assert signature(text) == signature(text)


@given(a=st.text(), b=st.text())
def test_jaccard_symmetry_property(a: str, b: str) -> None:
    sig_a = signature(a)
    sig_b = signature(b)
    assert jaccard(sig_a, sig_b) == jaccard(sig_b, sig_a)


@given(a=st.text(), b=st.text())
def test_jaccard_bounded_property(a: str, b: str) -> None:
    score = jaccard(signature(a), signature(b))
    assert 0.0 <= score <= 1.0


@given(
    values=st.lists(
        st.integers(min_value=0, max_value=(1 << 64) - 1),
        min_size=1,
        max_size=256,
    ),
)
def test_round_trip_property(values: list[int]) -> None:
    # Range is the byte-format ceiling (uint64), broader than the
    # mod-M61 range signature() produces — exercises the serializer's
    # full domain.
    sig = Signature(values=tuple(values))
    assert from_bytes(to_bytes(sig)) == sig
