#!/usr/bin/env bash
# Tests for plugins/armory/scripts/slugify.sh

SLUGIFY="$PLUGIN_ROOT/scripts/slugify.sh"

# ---- basic transformation ----

test_basic_lowercase_and_dashes() {
    local out; out=$(bash "$SLUGIFY" "Some Title Here")
    assert_equal "some-title-here" "$out"
}

test_already_lowercase_passthrough() {
    local out; out=$(bash "$SLUGIFY" "already lowercase")
    assert_equal "already-lowercase" "$out"
}

test_all_caps_lowercases() {
    local out; out=$(bash "$SLUGIFY" "ALL CAPS HERE")
    assert_equal "all-caps-here" "$out"
}

# ---- collapse and trim ----

test_collapses_consecutive_dashes() {
    local out; out=$(bash "$SLUGIFY" "foo!!  bar")
    assert_equal "foo-bar" "$out"
}

test_trims_leading_trailing_dashes() {
    local out; out=$(bash "$SLUGIFY" "  leading and trailing  ")
    assert_equal "leading-and-trailing" "$out"
}

test_trims_punctuation_at_edges() {
    local out; out=$(bash "$SLUGIFY" "...edge punctuation!!!")
    assert_equal "edge-punctuation" "$out"
}

# ---- edge cases ----

test_apostrophe_becomes_dash() {
    local out; out=$(bash "$SLUGIFY" "Anticipate the reader's question")
    assert_equal "anticipate-the-reader-s-question" "$out"
}

test_hyphenated_compound_preserved() {
    local out; out=$(bash "$SLUGIFY" "Strong verbs over verb-plus-adverb")
    assert_equal "strong-verbs-over-verb-plus-adverb" "$out"
}

test_special_characters_become_dashes() {
    local out; out=$(bash "$SLUGIFY" "C++ & Java")
    assert_equal "c-java" "$out"
}

test_numbers_preserved() {
    local out; out=$(bash "$SLUGIFY" "Section 1.2 of RFC 2119")
    assert_equal "section-1-2-of-rfc-2119" "$out"
}

test_empty_input() {
    local out; out=$(bash "$SLUGIFY" "")
    assert_equal "" "$out"
}

test_whitespace_only_input() {
    local out; out=$(bash "$SLUGIFY" "   ")
    assert_equal "" "$out"
}

test_only_punctuation() {
    local out; out=$(bash "$SLUGIFY" "!!!???")
    assert_equal "" "$out"
}

# ---- length cap ----

test_caps_at_80_characters() {
    local long; long=$(printf 'a%.0s' {1..100})
    local out; out=$(bash "$SLUGIFY" "$long")
    assert_equal 80 "${#out}"
}

# ---- input modes ----

test_reads_from_stdin() {
    local out; out=$(printf '%s' "Stdin Input" | bash "$SLUGIFY")
    assert_equal "stdin-input" "$out"
}

test_argument_takes_precedence_over_stdin() {
    local out; out=$(printf '%s' "ignored" | bash "$SLUGIFY" "From Argument")
    assert_equal "from-argument" "$out"
}

# ---- help flag ----

test_help_flag_long() {
    local out; out=$(bash "$SLUGIFY" --help)
    assert_contains "$out" "slugify.sh"
}

test_help_flag_short() {
    local out; out=$(bash "$SLUGIFY" -h)
    assert_contains "$out" "slugify.sh"
}

# ---- writing-prose principles round-trip ----

test_principle_source_is_the_authority() {
    local out; out=$(bash "$SLUGIFY" "Source is the authority")
    assert_equal "source-is-the-authority" "$out"
}

test_principle_em_dash_usage() {
    local out; out=$(bash "$SLUGIFY" "Em-dash usage")
    assert_equal "em-dash-usage" "$out"
}

test_principle_first_page_sets_the_pattern() {
    local out; out=$(bash "$SLUGIFY" "The first page sets the pattern")
    assert_equal "the-first-page-sets-the-pattern" "$out"
}
