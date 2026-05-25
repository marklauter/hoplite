#!/usr/bin/env bash
# Tests for plugins/armory/scripts/list-findings.sh

LIST="$PLUGIN_ROOT/scripts/list-findings.sh"

make_finding() {
    local slug="$1" title="$2" severity="$3" type="$4" lens="$5" location="$6" principle="$7" summary="$8"
    mkdir -p .findings
    {
        printf '# %s\n\n' "$title"
        printf 'Severity: %s\n' "$severity"
        printf 'Type: %s\n' "$type"
        [ -n "$lens" ] && printf 'Lens: %s\n' "$lens"
        printf 'Location: `%s`\n' "$location"
        printf 'Principle: %s\n' "$principle"
        printf '%s\n\n' "$summary"
        printf 'Body.\n'
    } > ".findings/${slug}.md"
}

setup() {
    make_finding "code-throws"   "Domain throws"         "important" "code"          ""        "src/x.cs:1"   "Results, not exceptions"      "Throws."
    make_finding "doc-hedges"    "README hedges"         "nit"       "documentation" "Line"    "README.md:3"  "Every word must earn its place" "Hedges in opening."
    make_finding "legacy-issue"  "Old finding"           "nit"       ""              ""        "src/y.cs:5"   "Some principle"               "Legacy."
}

# ---- empty / missing ----

test_missing_findings_dir_prints_no_findings() {
    rm -rf .findings
    local out; out=$("$LIST")
    assert_equal "no findings" "$out"
}

test_empty_findings_dir_prints_no_findings() {
    rm -rf .findings
    mkdir -p .findings
    local out; out=$("$LIST")
    assert_equal "no findings" "$out"
}

# ---- output format ----

test_lists_all_findings() {
    local out; out=$("$LIST")
    assert_contains "$out" "Domain throws"
    assert_contains "$out" "README hedges"
    assert_contains "$out" "Old finding"
}

test_severity_field_in_output() {
    local out; out=$("$LIST")
    assert_contains "$out" "  severity: important"
    assert_contains "$out" "  severity: nit"
}

test_type_field_present_when_set() {
    local out; out=$("$LIST")
    assert_contains "$out" "  type: code"
    assert_contains "$out" "  type: documentation"
}

test_lens_field_present_only_when_set() {
    local out; out=$("$LIST")
    # Lens shown for documentation finding
    assert_contains "$out" "  lens: Line"
    # No lens line for code findings (need to be careful — substring may match)
    # Check that the count of `lens:` lines matches the count of doc findings (1)
    local count; count=$(echo "$out" | grep -c "  lens:")
    assert_equal "1" "$count"
}

test_location_field_in_output() {
    local out; out=$("$LIST")
    assert_contains "$out" "  location: \`src/x.cs:1\`"
}

test_principle_field_in_output() {
    local out; out=$("$LIST")
    assert_contains "$out" "  principle: Results, not exceptions"
}

test_summary_in_output() {
    local out; out=$("$LIST")
    assert_contains "$out" "  Throws."
}

test_filename_arrow_in_output() {
    local out; out=$("$LIST")
    assert_contains "$out" "  → code-throws.md"
}

# ---- legacy findings (no Type field) ----

test_legacy_finding_omits_type_line() {
    local out; out=$("$LIST")
    # The legacy finding has no Type: in its head, so no type line in output.
    assert_contains "$out" "Old finding"
    # Confirm the type-line count: setup creates 2 with type + 1 without → 2 type lines
    local count; count=$(echo "$out" | grep -c "  type:")
    assert_equal "2" "$count"
}

# ---- exit code ----

test_exit_zero_on_no_findings() {
    rm -rf .findings
    local rc=0
    "$LIST" >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}
