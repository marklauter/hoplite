#!/usr/bin/env bash
# Tests for plugins/skills/skills/taking-notes/scripts/list-notes.sh

LIST="$PLUGIN_ROOT/skills/taking-notes/scripts/list-notes.sh"

make_note() {
    local slug="$1" title="$2" tags="$3" summary="$4"
    mkdir -p docs/notes
    {
        printf '# %s\n\n' "$title"
        printf 'Tags: %s\n' "$tags"
        printf '%s\n\n' "$summary"
        printf 'Body content.\n'
    } > "docs/notes/${slug}.md"
}

setup() {
    make_note "cache-ttl"     "Cache TTL is 300s"       "auth,cache"  "Confirmed via appsettings.json."
    make_note "redirect-loop" "Redirect loop on logout" "auth,bug"    "Stale session cookie."
    make_note "untagged"      "Untagged note"           ""            "No tags."
}

# ---- empty / missing directory ----

test_missing_directory_prints_no_notes() {
    rm -rf docs/notes
    local out; out=$("$LIST")
    assert_equal "no notes" "$out"
}

test_empty_directory_prints_no_notes() {
    rm -rf docs/notes
    mkdir -p docs/notes
    local out; out=$("$LIST")
    assert_equal "no notes" "$out"
}

# ---- no filter: all notes ----

test_lists_all_notes_when_no_filter() {
    local out; out=$("$LIST")
    assert_contains "$out" "Cache TTL is 300s"
    assert_contains "$out" "Redirect loop on logout"
    assert_contains "$out" "Untagged note"
}

test_output_includes_title() {
    local out; out=$("$LIST")
    assert_contains "$out" "Cache TTL is 300s"
}

test_output_includes_tags_line() {
    local out; out=$("$LIST")
    assert_contains "$out" "  tags: auth,cache"
}

test_output_includes_summary() {
    local out; out=$("$LIST")
    assert_contains "$out" "  Confirmed via appsettings.json."
}

test_output_includes_filename_arrow() {
    local out; out=$("$LIST")
    assert_contains "$out" "  -> cache-ttl.md"
}

# ---- tag filter ----

test_tag_filter_includes_matches() {
    local out; out=$("$LIST" auth)
    assert_contains "$out" "Cache TTL is 300s"
    assert_contains "$out" "Redirect loop on logout"
}

test_tag_filter_excludes_non_matches() {
    local out; out=$("$LIST" cache)
    assert_contains "$out" "Cache TTL is 300s"
    assert_not_contains "$out" "Redirect loop on logout"
}

test_tag_filter_excludes_untagged() {
    local out; out=$("$LIST" auth)
    assert_not_contains "$out" "Untagged note"
}

test_tag_filter_no_match_prints_message() {
    local out; out=$("$LIST" nonexistent)
    assert_equal "no notes tagged 'nonexistent'" "$out"
}

test_tag_filter_requires_exact_match_not_substring() {
    # 'cach' is a prefix of 'cache' but not the same tag
    local out; out=$("$LIST" cach)
    assert_equal "no notes tagged 'cach'" "$out"
}

# ---- exit code ----

test_exit_code_zero_on_no_notes() {
    rm -rf docs/notes
    local rc=0
    "$LIST" >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}

test_exit_code_zero_on_no_filter_match() {
    local rc=0
    "$LIST" nonexistent >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}
