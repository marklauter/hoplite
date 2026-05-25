#!/usr/bin/env bash
# Tests for plugins/hoplite/scripts/query.sh (shared findings query)

QUERY="$PLUGIN_ROOT/scripts/query.sh"

make_finding() {
    local slug="$1" title="$2" severity="$3" type="$4" lens="$5" location="$6" principle="$7" summary="$8"
    mkdir -p .findings
    {
        printf '# %s\n\n' "$title"
        printf 'Severity: %s\n' "$severity"
        [ -n "$type" ] && printf 'Type: %s\n' "$type"
        [ -n "$lens" ] && printf 'Lens: %s\n' "$lens"
        printf 'Location: `%s`\n' "$location"
        printf 'Principle: %s\n' "$principle"
        printf '%s\n\n' "$summary"
        printf 'Body.\n'
    } > ".findings/${slug}.md"
}

setup() {
    make_finding "domain-throws"   "Domain throws on missing order" "important"    "code"          ""       "src/Domain/Orders.cs:84" "Results, not exceptions"       "Throws InvalidOperationException."
    make_finding "nit-explicit-var" "Explicit type where var works" "nit"          "code"          ""       "src/Domain/Range.cs:12"  "Inference, not annotation"     "Could use var."
    make_finding "old-debt"        "Old TODO comment"               "pre-existing" "code"          ""       "src/Utils/Helper.cs:30"  "One source of truth"           "Pre-existing debt."
    make_finding "doc-hedges"      "README hedges"                  "nit"          "documentation" "Line"   "README.md:3"             "Every word must earn its place" "Hedges in opening."
    make_finding "doc-stale-ref"   "Broken cross-reference"         "important"    "documentation" "References" "docs/api.md:14"     "Source is the authority"        "Linked page missing."
    make_finding "legacy"          "Pre-Type-field finding"         "nit"          ""              ""       "src/legacy.cs:1"         "Some principle"                "Legacy."
}

# ---- no flags ----

test_no_flags_returns_every_finding() {
    local out; out=$("$QUERY")
    assert_contains "$out" "Domain throws"
    assert_contains "$out" "README hedges"
    assert_contains "$out" "Pre-Type-field finding"
}

# ---- --severity ----

test_severity_exact_match() {
    local out; out=$("$QUERY" --severity important)
    assert_contains "$out" "Domain throws"
    assert_contains "$out" "Broken cross-reference"
    assert_not_contains "$out" "Explicit type"
}

test_severity_invalid_value_rejected() {
    local rc=0
    "$QUERY" --severity critical 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- --xseverity ----

test_xseverity_excludes_matches() {
    local out; out=$("$QUERY" --xseverity pre-existing)
    assert_contains "$out" "Domain throws"
    assert_contains "$out" "Explicit type"
    assert_not_contains "$out" "Old TODO"
}

# ---- --type ----

test_type_exact_match() {
    local out; out=$("$QUERY" --type documentation)
    assert_contains "$out" "README hedges"
    assert_contains "$out" "Broken cross-reference"
    assert_not_contains "$out" "Domain throws"
}

test_type_code_includes_legacy_findings_with_no_type_field() {
    # Backward-compat: absent Type: is treated as code
    local out; out=$("$QUERY" --type code)
    assert_contains "$out" "Pre-Type-field finding"
}

test_type_invalid_value_rejected() {
    local rc=0
    "$QUERY" --type architecture 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- --xtype ----

test_xtype_excludes_matches() {
    local out; out=$("$QUERY" --xtype documentation)
    assert_contains "$out" "Domain throws"
    assert_not_contains "$out" "README hedges"
}

test_xtype_code_excludes_legacy_findings_with_no_type_field() {
    # Backward-compat: legacy findings count as code, so --xtype code excludes them
    local out; out=$("$QUERY" --xtype code)
    assert_not_contains "$out" "Pre-Type-field finding"
    assert_contains "$out" "README hedges"
}

# ---- --lens ----

test_lens_exact_match() {
    local out; out=$("$QUERY" --lens Line)
    assert_contains "$out" "README hedges"
    assert_not_contains "$out" "Broken cross-reference"
}

test_lens_invalid_value_rejected() {
    local rc=0
    "$QUERY" --lens Pizza 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- --xlens ----

test_xlens_excludes_matches() {
    local out; out=$("$QUERY" --type documentation --xlens References)
    assert_contains "$out" "README hedges"
    assert_not_contains "$out" "Broken cross-reference"
}

# ---- substring fields ----

test_title_substring_case_insensitive() {
    local out; out=$("$QUERY" --title throws)
    assert_contains "$out" "Domain throws"
    assert_not_contains "$out" "Explicit type"
}

test_location_substring_case_insensitive() {
    local out; out=$("$QUERY" --location domain)
    assert_contains "$out" "Domain throws"
    assert_contains "$out" "Explicit type"
    assert_not_contains "$out" "Old TODO"
}

test_principle_substring_case_insensitive() {
    local out; out=$("$QUERY" --principle "results, not exceptions")
    assert_contains "$out" "Domain throws"
    assert_not_contains "$out" "Explicit type"
}

test_summary_substring_case_insensitive() {
    local out; out=$("$QUERY" --summary INVALIDOPERATIONEXCEPTION)
    assert_contains "$out" "Domain throws"
    assert_not_contains "$out" "Explicit type"
}

# ---- AND combination ----

test_multiple_flags_and_together() {
    local out; out=$("$QUERY" --type documentation --severity important)
    assert_contains "$out" "Broken cross-reference"
    assert_not_contains "$out" "README hedges"
}

# ---- empty / missing ----

test_missing_findings_dir_prints_no_findings() {
    rm -rf .findings
    local out; out=$("$QUERY")
    assert_equal "no findings" "$out"
}

test_no_match_prints_no_matches() {
    local out; out=$("$QUERY" --type documentation --lens Coherence)
    assert_equal "no matches" "$out"
}

# ---- exit code ----

test_exit_zero_on_no_match() {
    local rc=0
    "$QUERY" --severity important --type documentation --lens Structure >/dev/null || rc=$?
    assert_exit_code 0 "$rc"
}

# ---- argument validation ----

test_unknown_flag_rejected() {
    local rc=0
    "$QUERY" --bogus 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}
