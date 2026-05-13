#!/usr/bin/env bash
# Tests for plugins/skills/scripts/summarize.sh

SUMMARIZE="$PLUGIN_ROOT/scripts/summarize.sh"

make_finding() {
    local slug="$1" title="$2" severity="$3" type="$4" lens="$5" principle="$6"
    mkdir -p .findings
    {
        printf '# %s\n\n' "$title"
        printf 'Severity: %s\n' "$severity"
        [ -n "$type" ] && printf 'Type: %s\n' "$type"
        [ -n "$lens" ] && printf 'Lens: %s\n' "$lens"
        printf 'Location: `src/x:1`\n'
        printf 'Principle: %s\n' "$principle"
        printf '%s\n\n' "Summary."
        printf 'Body.\n'
    } > ".findings/${slug}.md"
}

# ---- empty / missing ----

test_missing_dir_prints_no_findings() {
    rm -rf .findings
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_equal "no findings" "$out"
}

test_empty_dir_prints_no_findings() {
    rm -rf .findings
    mkdir -p .findings
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_equal "no findings" "$out"
}

# ---- code count line ----

test_code_count_line_when_code_findings_exist() {
    make_finding "a" "A" important code "" "Make invalid states unrepresentable"
    make_finding "b" "B" nit code "" "Immutable by default"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "code: 1 important, 1 nit, 0 pre-existing"
}

test_no_code_line_when_no_code_findings() {
    make_finding "a" "A" nit documentation Line "Every word must earn its place"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_not_contains "$out" "code:"
}

# ---- documentation count line ----

test_documentation_count_line_when_doc_findings_exist() {
    make_finding "a" "A" important documentation Accuracy "Source is the authority"
    make_finding "b" "B" nit documentation Line "Every word must earn its place"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "documentation: 1 important, 1 nit, 0 pre-existing"
}

test_lens_breakdown_when_documentation_present() {
    make_finding "a" "A" nit documentation Line "Every word must earn its place"
    make_finding "b" "B" nit documentation Line "Every word must earn its place"
    make_finding "c" "C" nit documentation Copy "Markdown is the wire format"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "by lens: 2 Line, 1 Copy"
}

test_no_lens_breakdown_when_only_code() {
    make_finding "a" "A" nit code "" "Immutable by default"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_not_contains "$out" "by lens:"
}

# ---- verdict ----

test_verdict_blocked_when_any_important() {
    make_finding "a" "A" important code "" "Immutable by default"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "diff is blocked on important findings"
}

test_verdict_shippable_nits_optional_when_only_nits() {
    make_finding "a" "A" nit code "" "Immutable by default"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "diff is shippable; nits optional"
}

test_verdict_appends_preexisting_pending() {
    make_finding "a" "A" nit code "" "Immutable by default"
    make_finding "b" "B" pre-existing code "" "Some principle"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "pre-existing triage pending"
}

test_verdict_blocked_combines_with_preexisting() {
    make_finding "a" "A" important code "" "Some principle"
    make_finding "b" "B" pre-existing code "" "Some principle"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "diff is blocked on important findings; pre-existing triage pending"
}

# ---- backward-compat: legacy findings without Type: ----

test_legacy_finding_counts_as_code() {
    make_finding "legacy" "Legacy" nit "" "" "Some principle"
    local out; out=$("$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "code: 0 important, 1 nit, 0 pre-existing"
}

# ---- non-canonical principle warnings ----

test_non_canonical_principle_flagged_when_rubric_readable() {
    # CLAUDE_PLUGIN_ROOT must be set for the rubric to be readable.
    make_finding "wonky" "Wonky" nit code "" "Made up principle nobody named"
    local out; out=$(CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" "$SUMMARIZE" 2>/dev/null)
    assert_contains "$out" "1 code finding(s) cite a non-canonical principle"
    assert_contains "$out" "wonky.md: Made up principle nobody named"
}

test_canonical_principle_not_flagged() {
    # Use a real writing-csharp Philosophy heading with its citation suffix.
    make_finding "ok" "OK" nit code "" "Immutable by default (Hickey)"
    local out; out=$(CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" "$SUMMARIZE" 2>/dev/null)
    assert_not_contains "$out" "cite a non-canonical principle"
}

test_canonical_principle_matches_without_citation_suffix() {
    # Citation suffix is stripped on both sides — un-cited form matches too.
    make_finding "ok" "OK" nit code "" "Immutable by default"
    local out; out=$(CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" "$SUMMARIZE" 2>/dev/null)
    assert_not_contains "$out" "cite a non-canonical principle"
}

# ---- stderr warning when CLAUDE_PLUGIN_ROOT is unset ----

test_unset_plugin_root_emits_stderr_warning() {
    make_finding "a" "A" nit code "" "Some principle"
    local stderr; stderr=$(CLAUDE_PLUGIN_ROOT="" "$SUMMARIZE" 2>&1 >/dev/null)
    assert_contains "$stderr" "CLAUDE_PLUGIN_ROOT is unset"
}

test_unset_plugin_root_still_produces_counts() {
    make_finding "a" "A" nit code "" "Some principle"
    local stdout; stdout=$(CLAUDE_PLUGIN_ROOT="" "$SUMMARIZE" 2>/dev/null)
    assert_contains "$stdout" "code: 0 important, 1 nit, 0 pre-existing"
}
