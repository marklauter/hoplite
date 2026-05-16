#!/usr/bin/env bash
# Tests for plugins/skills/skills/triaging-findings/scripts/drop.sh

DROP="$PLUGIN_ROOT/skills/triaging-findings/scripts/drop.sh"

make_finding() {
    local slug="$1"
    mkdir -p .findings
    {
        printf '# Title\n\n'
        printf 'Severity: nit\n'
        printf 'Type: code\n'
        printf 'Location: `src/x.cs:1`\n'
        printf 'Principle: Some principle\n'
        printf 'Summary.\n\n'
        printf 'Body.\n'
    } > ".findings/${slug}.md"
}

# ---- happy path ----

test_drop_deletes_finding() {
    make_finding "to-drop"
    "$DROP" "to-drop"
    assert_file_not_exists ".findings/to-drop.md"
}

test_drop_silent_on_success() {
    make_finding "to-drop"
    local out; out=$("$DROP" "to-drop" 2>&1)
    assert_equal "" "$out"
}

test_drop_preserves_sibling_findings() {
    make_finding "to-drop"
    make_finding "keeper"
    "$DROP" "to-drop"
    assert_file_exists ".findings/keeper.md"
}

# ---- argument validation ----

test_missing_slug_fails() {
    local rc=0
    "$DROP" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_slug_with_path_separator_rejected() {
    local rc=0
    "$DROP" "subdir/slug" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_slug_with_md_suffix_rejected() {
    make_finding "with-suffix"
    local rc=0
    "$DROP" "with-suffix.md" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    # The finding is preserved because the script rejected the input.
    assert_file_exists ".findings/with-suffix.md"
}

# ---- missing target ----

test_missing_finding_fails() {
    local rc=0
    "$DROP" "does-not-exist" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- repo-root anchoring ----

test_resolves_finding_at_git_root_from_subdirectory() {
    git init -q
    make_finding "anchored"
    mkdir -p src
    cd src
    "$DROP" "anchored"
    assert_file_not_exists "../.findings/anchored.md"
}
