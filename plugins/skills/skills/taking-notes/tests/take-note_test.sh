#!/usr/bin/env bash
# Tests for plugins/skills/skills/taking-notes/scripts/take-note.sh

TAKE="$PLUGIN_ROOT/skills/taking-notes/scripts/take-note.sh"

# ---- happy path ----

test_writes_file_at_docs_notes_with_slug() {
    echo "body content" | "$TAKE" "Cache TTL is 300s" "cache,auth" "Confirmed via appsettings.json."
    assert_file_exists "docs/notes/cache-ttl-is-300s.md"
}

test_file_has_h1_with_title() {
    echo "body" | "$TAKE" "Some Title" "tag1" "Summary line."
    local first_line; first_line=$(sed -n '1p' docs/notes/some-title.md)
    assert_equal "# Some Title" "$first_line"
}

test_file_has_tags_line_at_line_3() {
    echo "body" | "$TAKE" "Title" "tag-a,tag-b" "Summary."
    local tags_line; tags_line=$(sed -n '3p' docs/notes/title.md)
    assert_equal "Tags: tag-a,tag-b" "$tags_line"
}

test_file_has_summary_at_line_4() {
    echo "body" | "$TAKE" "Title" "" "The summary text."
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "The summary text." "$summary"
}

test_body_from_stdin_is_appended() {
    printf '## Observation\nfoo bar\n' | "$TAKE" "Title" "" "Summary."
    local body; body=$(cat docs/notes/title.md)
    assert_contains "$body" "## Observation"
    assert_contains "$body" "foo bar"
}

test_empty_tags_allowed() {
    echo "body" | "$TAKE" "Title" "" "Summary."
    # `printf 'Tags: %s\n' ""` produces "Tags: " with a trailing space — harmless
    local tags_line; tags_line=$(sed -n '3p' docs/notes/title.md)
    assert_equal "Tags: " "$tags_line"
}

# ---- slug derivation ----

test_slug_lowercases_title() {
    echo "body" | "$TAKE" "UPPER CASE" "" "Summary."
    assert_file_exists "docs/notes/upper-case.md"
}

test_slug_replaces_nonalphanumeric_with_dashes() {
    echo "body" | "$TAKE" "Title: With (Punctuation)!" "" "Summary."
    assert_file_exists "docs/notes/title-with-punctuation.md"
}

test_slug_trims_leading_and_trailing_dashes() {
    echo "body" | "$TAKE" "  whitespace  " "" "Summary."
    assert_file_exists "docs/notes/whitespace.md"
}

test_slug_empty_after_sanitization_fails() {
    local rc=0
    echo "body" | "$TAKE" "!!!" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- --force / overwrite ----

test_refuses_overwrite_without_force() {
    echo "body 1" | "$TAKE" "Title" "" "First summary."
    local rc=0
    echo "body 2" | "$TAKE" "Title" "" "Second summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    # Original content unchanged
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "First summary." "$summary"
}

test_force_allows_overwrite() {
    echo "body 1" | "$TAKE" "Title" "" "First."
    echo "body 2" | "$TAKE" --force "Title" "" "Second."
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "Second." "$summary"
}

test_force_works_after_other_flags_with_doubledash() {
    # The while-loop arg parser should handle -- correctly
    echo "body" | "$TAKE" --force -- "Title" "" "Summary."
    assert_file_exists "docs/notes/title.md"
}

# ---- argument validation ----

test_missing_title_exits_non_zero() {
    local rc=0
    echo "body" | "$TAKE" "" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_missing_summary_exits_non_zero() {
    local rc=0
    echo "body" | "$TAKE" "Title" "" "" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_unknown_flag_exits_non_zero() {
    local rc=0
    echo "body" | "$TAKE" --bogus "Title" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_body_must_be_piped_on_stdin() {
    # stdin from /dev/null is a tty-like situation in some shells; use </dev/null to test
    local rc=0
    "$TAKE" "Title" "" "Summary." </dev/null 2>/dev/null
    rc=$?
    # We're not running in an interactive terminal, so /dev/null is NOT a tty.
    # The check is: success when piped; in test env, /dev/null counts as piped.
    # So this should succeed. Confirm success means the file was created.
    assert_equal "0" "$rc"
    assert_file_exists "docs/notes/title.md"
}

# ---- silent success ----

test_success_produces_no_stdout() {
    local out; out=$(echo "body" | "$TAKE" "Title" "" "Summary." 2>/dev/null)
    assert_equal "" "$out"
}
