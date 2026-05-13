#!/usr/bin/env bash
# Tests for plugins/skills/skills/journaling/scripts/journal-entry.sh

ENTRY="$PLUGIN_ROOT/skills/journaling/scripts/journal-entry.sh"

# Helper: find the single entry file under docs/journal/ (assumes one was just written).
find_entry() {
    ls docs/journal/*.md 2>/dev/null | head -1
}

# ---- happy path ----

test_writes_file_under_docs_journal() {
    echo "body" | "$ENTRY" "Verified cache TTL" "cache" "Summary."
    local f; f=$(find_entry)
    assert_file_exists "$f"
}

test_filename_has_date_and_time_prefix() {
    echo "body" | "$ENTRY" "Title" "" "Summary."
    local f; f=$(find_entry)
    local name; name=$(basename "$f")
    # YYYY-MM-DD-HHMM-<slug>.md
    assert_match "$name" "^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}-title\.md$"
}

test_h1_is_title() {
    echo "body" | "$ENTRY" "Some Title" "" "Summary."
    local f; f=$(find_entry)
    local first; first=$(sed -n '1p' "$f")
    assert_equal "# Some Title" "$first"
}

test_date_head_is_line_3() {
    echo "body" | "$ENTRY" "Title" "" "Summary."
    local f; f=$(find_entry)
    local date_line; date_line=$(sed -n '3p' "$f")
    # Format: "Date: YYYY-MM-DD HH:MM"
    assert_match "$date_line" "^Date: [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$"
}

test_tags_at_line_4() {
    echo "body" | "$ENTRY" "Title" "a,b" "Summary."
    local f; f=$(find_entry)
    local tags; tags=$(sed -n '4p' "$f")
    assert_equal "Tags: a,b" "$tags"
}

test_summary_at_line_5() {
    echo "body" | "$ENTRY" "Title" "" "The summary."
    local f; f=$(find_entry)
    local summary; summary=$(sed -n '5p' "$f")
    assert_equal "The summary." "$summary"
}

test_body_from_stdin_appended() {
    printf '## Context\nthe context\n' | "$ENTRY" "Title" "" "Summary."
    local f; f=$(find_entry)
    local body; body=$(cat "$f")
    assert_contains "$body" "## Context"
    assert_contains "$body" "the context"
}

# ---- slug derivation ----

test_slug_lowercases_and_dashes() {
    echo "body" | "$ENTRY" "Cache TTL: Verified!" "" "Summary."
    local f; f=$(find_entry)
    local name; name=$(basename "$f")
    # Slug portion (after the date-time prefix)
    assert_match "$name" "cache-ttl-verified\.md$"
}

test_slug_empty_after_sanitization_fails() {
    local rc=0
    echo "body" | "$ENTRY" "!!!" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- append-only / overwrite ----

test_refuses_overwrite_no_force_flag() {
    # No --force flag exists; even attempting it should fail.
    echo "body" | "$ENTRY" "Title" "" "Summary."
    # Compute the target filename using the same clock the script saw
    local target
    target="docs/journal/$(date +%Y-%m-%d)-$(date +%H%M)-title.md"
    if [ ! -e "$target" ]; then
        # Clock ticked into the next minute mid-test; skip
        return 0
    fi
    local rc=0
    echo "body 2" | "$ENTRY" "Title" "" "Different summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_force_flag_is_not_supported() {
    local rc=0
    echo "body" | "$ENTRY" --force "Title" "" "Summary." 2>/dev/null || rc=$?
    # --force is not parsed; the script sees "--force" as the title which is non-empty,
    # then "Title" as tags, then "" as summary which is empty → fails on missing summary
    # OR succeeds and treats --force as the title. Either way, the test confirms there's
    # no special force handling. The slug "force" (after sanitization) would yield a file.
    # If summary is empty (the actual summary arg position), script exits 2.
    assert_exit_code 2 "$rc"
}

# ---- argument validation ----

test_missing_title_fails() {
    local rc=0
    echo "body" | "$ENTRY" "" "" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_missing_summary_fails() {
    local rc=0
    echo "body" | "$ENTRY" "Title" "" "" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- silent success ----

test_success_produces_no_stdout() {
    local out; out=$(echo "body" | "$ENTRY" "Title" "" "Summary." 2>/dev/null)
    assert_equal "" "$out"
}
