#!/usr/bin/env bash
# Tests for plugins/skills/skills/journaling/scripts/scan.sh

SCAN="$PLUGIN_ROOT/skills/journaling/scripts/scan.sh"

make_entry() {
    local date="$1" time="$2" slug="$3" title="$4" tags="$5" summary="$6"
    mkdir -p docs/journal
    {
        printf '# %s\n\n' "$title"
        printf 'date: %s %s:%s\n' "$date" "${time:0:2}" "${time:2:2}"
        printf 'tags: %s\n' "$tags"
        printf '%s\n\n' "$summary"
        printf 'Body.\n'
    } > "docs/journal/${date}-${time}-${slug}.md"
}

setup() {
    make_entry "2026-05-01" "0900" "first-attempt"       "First attempt"        "auth"          "First try at auth flow."
    make_entry "2026-05-10" "1430" "cache-investigation" "Cache investigation"  "auth,cache"    "Followed the stale read."
    make_entry "2026-05-12" "1100" "decision-on-ttl"     "Decision on TTL"      "decision"      "Settled on 300s."
    make_entry "2026-05-13" "0915" "retrospective"       "Sprint retrospective" "retrospective" "Notes from the cycle."
}

# ---- no flags ----

test_no_flags_returns_every_entry() {
    local out; out=$("$SCAN")
    assert_contains "$out" "First attempt"
    assert_contains "$out" "Cache investigation"
    assert_contains "$out" "Decision on TTL"
    assert_contains "$out" "Sprint retrospective"
}

# ---- --title ----

test_title_substring_case_insensitive() {
    local out; out=$("$SCAN" --title CACHE)
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "First attempt"
}

# ---- --tag ----

test_tag_exact_match() {
    local out; out=$("$SCAN" --tag cache)
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "First attempt"
    assert_not_contains "$out" "Decision on TTL"
}

# ---- --xtag ----

test_xtag_excludes_entries() {
    local out; out=$("$SCAN" --xtag retrospective)
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "Sprint retrospective"
}

# ---- --summary ----

test_summary_substring_case_insensitive() {
    local out; out=$("$SCAN" --summary "stale read")
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "First attempt"
}

# ---- --since / --until ----

test_since_includes_on_or_after() {
    local out; out=$("$SCAN" --since 2026-05-10)
    assert_contains "$out" "Cache investigation"
    assert_contains "$out" "Decision on TTL"
    assert_not_contains "$out" "First attempt"
}

test_until_includes_on_or_before() {
    local out; out=$("$SCAN" --until 2026-05-10)
    assert_contains "$out" "First attempt"
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "Decision on TTL"
}

test_since_and_until_compose_range() {
    local out; out=$("$SCAN" --since 2026-05-10 --until 2026-05-12)
    assert_contains "$out" "Cache investigation"
    assert_contains "$out" "Decision on TTL"
    assert_not_contains "$out" "First attempt"
    assert_not_contains "$out" "Sprint retrospective"
}

test_since_invalid_date_format_fails() {
    local rc=0
    "$SCAN" --since 2026-5-1 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_until_invalid_date_format_fails() {
    local rc=0
    "$SCAN" --until "yesterday" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- AND combination ----

test_multiple_flags_and_together() {
    local out; out=$("$SCAN" --tag auth --since 2026-05-10)
    assert_contains "$out" "Cache investigation"
    assert_not_contains "$out" "First attempt"
}

# ---- empty / missing ----

test_missing_docs_journal_prints_no_entries() {
    rm -rf docs/journal
    local out; out=$("$SCAN")
    assert_equal "no entries" "$out"
}

test_no_match_echoes_predicates() {
    local out; out=$("$SCAN" --tag nonexistent)
    assert_equal "no entries matching --tag 'nonexistent'" "$out"
}

test_no_match_echoes_multiple_predicates() {
    local out; out=$("$SCAN" --tag nonexistent --since 2026-05-10)
    assert_contains "$out" "--tag 'nonexistent'"
    assert_contains "$out" "--since '2026-05-10'"
}

# ---- argument validation ----

test_unknown_flag_exits_non_zero() {
    local rc=0
    "$SCAN" --bogus 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- exit code ----

test_exit_zero_on_no_match() {
    local rc=0
    "$SCAN" --tag nonexistent >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}
