#!/usr/bin/env bash
# Tests for plugins/skills/skills/journaling/scripts/list-journal.sh

LIST="$PLUGIN_ROOT/skills/journaling/scripts/list-journal.sh"

# Helper: build a journal entry at a chosen date+time+slug with given fields.
make_entry() {
    local date="$1" time="$2" slug="$3" title="$4" tags="$5" summary="$6"
    mkdir -p docs/journal
    {
        printf '# %s\n\n' "$title"
        printf 'Date: %s %s:%s\n' "$date" "${time:0:2}" "${time:2:2}"
        printf 'Tags: %s\n' "$tags"
        printf '%s\n\n' "$summary"
        printf 'Body.\n'
    } > "docs/journal/${date}-${time}-${slug}.md"
}

setup() {
    make_entry "2026-05-01" "0900" "first-attempt" "First attempt"        "auth"        "First try at the auth flow."
    make_entry "2026-05-10" "1430" "cache-investigation" "Cache investigation" "auth,cache" "Followed the stale read."
    make_entry "2026-05-12" "1100" "decision-on-ttl"     "Decision on TTL"     "decision"   "Settled on 300s."
}

# ---- empty / missing ----

test_missing_directory_prints_no_entries() {
    rm -rf docs/journal
    local out; out=$("$LIST")
    assert_equal "no entries" "$out"
}

test_empty_directory_prints_no_entries() {
    rm -rf docs/journal
    mkdir -p docs/journal
    local out; out=$("$LIST")
    assert_equal "no entries" "$out"
}

# ---- no filter: all entries ----

test_lists_all_entries() {
    local out; out=$("$LIST")
    assert_contains "$out" "First attempt"
    assert_contains "$out" "Cache investigation"
    assert_contains "$out" "Decision on TTL"
}

test_output_includes_date() {
    local out; out=$("$LIST")
    assert_contains "$out" "  date: 2026-05-10 14:30"
}

test_output_includes_tags() {
    local out; out=$("$LIST")
    assert_contains "$out" "  tags: auth,cache"
}

test_output_includes_summary() {
    local out; out=$("$LIST")
    assert_contains "$out" "  Followed the stale read."
}

test_output_includes_filename_arrow() {
    local out; out=$("$LIST")
    assert_contains "$out" "  -> 2026-05-10-1430-cache-investigation.md"
}

# ---- date filter ----

test_date_filter_includes_on_or_after() {
    local out; out=$("$LIST" 2026-05-10)
    assert_contains "$out" "Cache investigation"
    assert_contains "$out" "Decision on TTL"
    assert_not_contains "$out" "First attempt"
}

test_date_filter_no_match_prints_message() {
    local out; out=$("$LIST" 2027-01-01)
    assert_equal "no entries on or after '2027-01-01'" "$out"
}

test_date_filter_includes_exact_match() {
    local out; out=$("$LIST" 2026-05-10)
    assert_contains "$out" "Cache investigation"
}

# ---- tag filter ----

test_tag_filter_matches() {
    local out; out=$("$LIST" cache)
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "First attempt"
    assert_not_contains "$out" "Decision on TTL"
}

test_tag_filter_no_match_prints_message() {
    local out; out=$("$LIST" nonexistent)
    assert_equal "no entries tagged 'nonexistent'" "$out"
}

test_tag_filter_requires_exact_match_not_substring() {
    local out; out=$("$LIST" auth-cache)
    assert_equal "no entries tagged 'auth-cache'" "$out"
}

# ---- chronological order ----

test_entries_listed_chronologically() {
    # Filenames sort chronologically since they are date-prefixed.
    local out; out=$("$LIST")
    local first_pos; first_pos=$(echo "$out" | grep -n "First attempt" | cut -d: -f1)
    local cache_pos; cache_pos=$(echo "$out" | grep -n "Cache investigation" | cut -d: -f1)
    local decision_pos; decision_pos=$(echo "$out" | grep -n "Decision on TTL" | cut -d: -f1)
    [ "$first_pos" -lt "$cache_pos" ]
    [ "$cache_pos" -lt "$decision_pos" ]
}

# ---- exit code ----

test_exit_zero_on_no_entries() {
    rm -rf docs/journal
    local rc=0
    "$LIST" >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}
