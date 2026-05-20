#!/usr/bin/env bash
# Tests for plugins/skills/skills/taking-notes/scripts/record-note.sh

RECORD="$PLUGIN_ROOT/skills/taking-notes/scripts/record-note.sh"

# ---- happy path ----

test_writes_file_at_docs_notes_with_slug() {
    echo "body content" | "$RECORD" "Cache TTL is 300s" "cache,auth" "Confirmed via appsettings.json."
    assert_file_exists "docs/notes/cache-ttl-is-300s.md"
}

test_file_has_h1_with_title() {
    echo "body" | "$RECORD" "Some Title" "tag1" "Summary line."
    local first_line; first_line=$(sed -n '1p' docs/notes/some-title.md)
    assert_equal "# Some Title" "$first_line"
}

test_file_has_tags_line_at_line_3() {
    echo "body" | "$RECORD" "Title" "tag-a,tag-b" "Summary."
    local tags_line; tags_line=$(sed -n '3p' docs/notes/title.md)
    assert_equal "tags: tag-a,tag-b" "$tags_line"
}

test_file_has_summary_at_line_4() {
    echo "body" | "$RECORD" "Title" "" "The summary text."
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "The summary text." "$summary"
}

test_body_from_stdin_is_appended() {
    printf '## Observation\nfoo bar\n' | "$RECORD" "Title" "" "Summary."
    local body; body=$(cat docs/notes/title.md)
    assert_contains "$body" "## Observation"
    assert_contains "$body" "foo bar"
}

test_empty_tags_allowed() {
    echo "body" | "$RECORD" "Title" "" "Summary."
    # `printf 'tags: %s\n' ""` produces "tags: " with a trailing space — harmless
    local tags_line; tags_line=$(sed -n '3p' docs/notes/title.md)
    assert_equal "tags: " "$tags_line"
}

# ---- slug derivation ----

test_slug_lowercases_title() {
    echo "body" | "$RECORD" "UPPER CASE" "" "Summary."
    assert_file_exists "docs/notes/upper-case.md"
}

test_slug_replaces_nonalphanumeric_with_dashes() {
    echo "body" | "$RECORD" "Title: With (Punctuation)!" "" "Summary."
    assert_file_exists "docs/notes/title-with-punctuation.md"
}

test_slug_trims_leading_and_trailing_dashes() {
    echo "body" | "$RECORD" "  whitespace  " "" "Summary."
    assert_file_exists "docs/notes/whitespace.md"
}

test_slug_empty_after_sanitization_fails() {
    local rc=0
    echo "body" | "$RECORD" "!!!" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- --overwrite ----

test_refuses_to_overwrite_existing_file_without_flag() {
    echo "body 1" | "$RECORD" "Title" "" "First summary."
    local rc=0
    echo "body 2" | "$RECORD" "Title" "" "Second summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    # Original content unchanged
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "First summary." "$summary"
}

test_overwrite_replaces_existing_file() {
    echo "body 1" | "$RECORD" "Title" "" "First."
    echo "body 2" | "$RECORD" --overwrite "Title" "" "Second."
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "Second." "$summary"
}

test_overwrite_works_after_doubledash() {
    # The while-loop arg parser should handle -- correctly
    echo "body" | "$RECORD" --overwrite -- "Title" "" "Summary."
    assert_file_exists "docs/notes/title.md"
}

# ---- --append ----

test_append_extends_existing_file_body() {
    echo "original body" | "$RECORD" "Title" "" "Summary."
    echo "appended body" | "$RECORD" --append "Title"
    local content; content=$(cat docs/notes/title.md)
    assert_contains "$content" "original body"
    assert_contains "$content" "appended body"
}

test_append_preserves_original_header() {
    echo "original" | "$RECORD" "Title" "tag-a,tag-b" "Original summary."
    echo "more" | "$RECORD" --append "Title"
    local h1; h1=$(sed -n '1p' docs/notes/title.md)
    local tags; tags=$(sed -n '3p' docs/notes/title.md)
    local summary; summary=$(sed -n '4p' docs/notes/title.md)
    assert_equal "# Title" "$h1"
    assert_equal "tags: tag-a,tag-b" "$tags"
    assert_equal "Original summary." "$summary"
}

test_append_preserves_original_body() {
    echo "original body line" | "$RECORD" "Title" "" "Summary."
    echo "second body line" | "$RECORD" --append "Title"
    local content; content=$(cat docs/notes/title.md)
    assert_contains "$content" "original body line"
}

test_append_uses_single_newline_separator() {
    # Existing file ends in \n. After append, body content immediately follows
    # on the next line — no blank line between.
    printf 'first\n' | "$RECORD" "Title" "" "Summary."
    printf 'second\n' | "$RECORD" --append "Title"
    # Lines 1, 3, 4 are header; line 5 blank; line 6 is "first"; line 7 is "second".
    local line6; line6=$(sed -n '6p' docs/notes/title.md)
    local line7; line7=$(sed -n '7p' docs/notes/title.md)
    assert_equal "first" "$line6"
    assert_equal "second" "$line7"
}

test_append_to_missing_file_exits_non_zero() {
    local rc=0
    echo "body" | "$RECORD" --append "Nonexistent Title" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    assert_file_not_exists "docs/notes/nonexistent-title.md"
}

test_append_with_only_title_succeeds() {
    echo "original" | "$RECORD" "Title" "" "Summary."
    echo "more" | "$RECORD" --append "Title"
    assert_file_exists "docs/notes/title.md"
}

test_append_rejects_extra_positional_args() {
    echo "original" | "$RECORD" "Title" "" "Summary."
    local rc=0
    echo "more" | "$RECORD" --append "Title" "extra-tags" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_append_and_overwrite_mutually_exclusive() {
    local rc=0
    echo "body" | "$RECORD" --overwrite --append "Title" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_append_empty_body_still_rejected() {
    echo "original" | "$RECORD" "Title" "" "Summary."
    local rc=0
    "$RECORD" --append "Title" </dev/null 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    # Original file unchanged — assert line count is exactly what the writer produced.
    local lines; lines=$(wc -l < docs/notes/title.md)
    # Header: 4 lines + blank line 5 + body "original\n" (line 6) = 6 newlines = 6 per wc -l
    assert_equal "6" "${lines// /}"
}

# ---- argument validation ----

test_missing_title_exits_non_zero() {
    local rc=0
    echo "body" | "$RECORD" "" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_missing_summary_exits_non_zero() {
    local rc=0
    echo "body" | "$RECORD" "Title" "" "" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_unknown_flag_exits_non_zero() {
    local rc=0
    echo "body" | "$RECORD" --bogus "Title" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_empty_body_exits_non_zero() {
    local rc=0
    "$RECORD" "Title" "" "Summary." </dev/null 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    assert_file_not_exists "docs/notes/title.md"
}

test_whitespace_only_body_exits_non_zero() {
    local rc=0
    printf '   \n\t\n  \n' | "$RECORD" "Title" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    assert_file_not_exists "docs/notes/title.md"
}

# ---- silent success ----

test_success_produces_no_stdout() {
    local out; out=$(echo "body" | "$RECORD" "Title" "" "Summary." 2>/dev/null)
    assert_equal "" "$out"
}
