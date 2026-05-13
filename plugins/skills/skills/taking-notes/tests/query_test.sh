#!/usr/bin/env bash
# Tests for plugins/skills/skills/taking-notes/scripts/query.sh
#
# Sourced by run-tests.sh; each test_* runs in a subshell with cwd at a fresh
# tmpdir and $PLUGIN_ROOT pointing at the plugin root.

QUERY="$PLUGIN_ROOT/skills/taking-notes/scripts/query.sh"

# Build a fixture note at docs/notes/<slug>.md with the canonical head shape.
make_note() {
    local slug="$1" title="$2" tags="$3" summary="$4" body="${5:-}"
    mkdir -p docs/notes
    {
        printf '# %s\n\n' "$title"
        printf 'Tags: %s\n' "$tags"
        printf '%s\n\n' "$summary"
        printf '%s\n' "${body:-Body content.}"
    } > "docs/notes/${slug}.md"
}

setup() {
    make_note "cache-ttl"     "Cache TTL is 300s"            "auth,cache"         "Confirmed via appsettings.json."
    make_note "redirect-loop" "Redirect loop on logout"      "auth,bug"           "Caused by stale session cookie."
    make_note "draft-idea"    "Caching strategy spike"       "cache,draft"        "Possible LRU eviction approach."
    make_note "untagged"      "Untagged note"                ""                   "No tags on this one."
}

# ---- no flags ----

test_no_flags_returns_every_note() {
    local out; out=$("$QUERY")
    assert_contains "$out" "Cache TTL is 300s"
    assert_contains "$out" "Redirect loop on logout"
    assert_contains "$out" "Caching strategy spike"
    assert_contains "$out" "Untagged note"
}

# ---- --tag (positive) ----

test_tag_matches_when_tag_present() {
    local out; out=$("$QUERY" --tag cache)
    assert_contains "$out" "Cache TTL is 300s"
    assert_contains "$out" "Caching strategy spike"
    assert_not_contains "$out" "Redirect loop on logout"
    assert_not_contains "$out" "Untagged note"
}

test_tag_misses_when_tag_absent() {
    local out; out=$("$QUERY" --tag nonexistent)
    assert_equal "no matches" "$out"
}

test_tag_does_not_match_partial() {
    # 'cach' should not match 'cache' — --tag is exact match within the comma list
    local out; out=$("$QUERY" --tag cach)
    assert_equal "no matches" "$out"
}

# ---- --xtag (exclude) ----

test_xtag_excludes_notes_with_that_tag() {
    local out; out=$("$QUERY" --xtag cache)
    assert_not_contains "$out" "Cache TTL is 300s"
    assert_not_contains "$out" "Caching strategy spike"
    assert_contains "$out" "Redirect loop on logout"
    assert_contains "$out" "Untagged note"
}

test_xtag_treats_missing_tags_as_satisfied() {
    # An untagged note has the tag "missing" — exclusion is trivially satisfied.
    local out; out=$("$QUERY" --xtag missing)
    assert_contains "$out" "Untagged note"
}

test_tag_and_xtag_compose() {
    # --tag cache --xtag draft → notes tagged cache but not draft
    local out; out=$("$QUERY" --tag cache --xtag draft)
    assert_contains "$out" "Cache TTL is 300s"
    assert_not_contains "$out" "Caching strategy spike"
}

# ---- --title (substring, case-insensitive) ----

test_title_substring_match() {
    # 'cach' is a substring of both 'Cache' and 'Caching'
    local out; out=$("$QUERY" --title cach)
    assert_contains "$out" "Cache TTL is 300s"
    assert_contains "$out" "Caching strategy spike"
    assert_not_contains "$out" "Redirect loop on logout"
}

test_title_match_is_case_insensitive() {
    local out; out=$("$QUERY" --title CACHE)
    assert_contains "$out" "Cache TTL is 300s"
}

# ---- --summary (substring, case-insensitive) ----

test_summary_substring_match() {
    local out; out=$("$QUERY" --summary appsettings)
    assert_contains "$out" "Cache TTL is 300s"
    assert_not_contains "$out" "Caching strategy spike"
}

# ---- AND combination ----

test_multiple_flags_and_together() {
    local out; out=$("$QUERY" --tag cache --title TTL)
    assert_contains "$out" "Cache TTL is 300s"
    assert_not_contains "$out" "Caching strategy spike"
}

# ---- empty / missing directory ----

test_missing_docs_notes_prints_no_notes() {
    rm -rf docs/notes
    local out; out=$("$QUERY")
    assert_equal "no notes" "$out"
}

test_empty_docs_notes_prints_no_notes() {
    rm -rf docs/notes
    mkdir -p docs/notes
    local out; out=$("$QUERY")
    assert_equal "no notes" "$out"
}

# ---- argument validation ----

test_unknown_flag_exits_non_zero() {
    local rc=0
    "$QUERY" --bogus 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_flag_without_value_exits_non_zero() {
    local rc=0
    "$QUERY" --tag 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- exit code ----

test_exit_code_is_zero_on_no_match() {
    local rc=0
    "$QUERY" --tag nonexistent >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}
