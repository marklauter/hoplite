#!/usr/bin/env bash
# Tests for plugins/skills/scripts/report-finding.sh

REPORT="$PLUGIN_ROOT/scripts/report-finding.sh"

# ---- happy path: code finding ----

test_code_finding_writes_file() {
    echo "body" | "$REPORT" --type code \
        "Domain throws on missing order" important \
        "src/Domain/Orders.cs:84" \
        "Results, not exceptions" \
        "Throws InvalidOperationException."
    assert_file_exists ".findings/domain-throws-on-missing-order.md"
}

test_code_finding_has_severity_field() {
    echo "body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Summary."
    local sev; sev=$(grep '^Severity:' .findings/title.md)
    assert_equal "Severity: nit" "$sev"
}

test_code_finding_has_type_field() {
    echo "body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Summary."
    local t; t=$(grep '^Type:' .findings/title.md)
    assert_equal "Type: code" "$t"
}

test_code_finding_omits_lens_field() {
    echo "body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Summary."
    local out; out=$(grep '^Lens:' .findings/title.md 2>/dev/null || true)
    assert_equal "" "$out"
}

test_location_wrapped_in_backticks() {
    echo "body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Summary."
    local loc; loc=$(grep '^Location:' .findings/title.md)
    assert_equal 'Location: `src/x.cs:1`' "$loc"
}

test_location_strips_caller_supplied_backticks() {
    echo "body" | "$REPORT" --type code "Title" nit '`src/x.cs:1`' "Principle" "Summary."
    local loc; loc=$(grep '^Location:' .findings/title.md)
    assert_equal 'Location: `src/x.cs:1`' "$loc"
}

# ---- happy path: documentation finding ----

test_documentation_finding_requires_lens() {
    local rc=0
    echo "body" | "$REPORT" --type documentation \
        "Title" nit "docs/x.md:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_documentation_finding_writes_lens_field() {
    echo "body" | "$REPORT" --type documentation --lens Line \
        "README hedges" nit "README.md:3" "Every word must earn its place" "Hedges in opening."
    local lens; lens=$(grep '^Lens:' .findings/readme-hedges.md)
    assert_equal "Lens: Line" "$lens"
}

test_documentation_finding_has_type_field() {
    echo "body" | "$REPORT" --type documentation --lens Copy \
        "Title" nit "docs/x.md:1" "Principle" "Summary."
    local t; t=$(grep '^Type:' .findings/title.md)
    assert_equal "Type: documentation" "$t"
}

# ---- enum validation ----

test_invalid_type_rejected() {
    local rc=0
    echo "body" | "$REPORT" --type architecture \
        "Title" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_invalid_severity_rejected() {
    local rc=0
    echo "body" | "$REPORT" --type code \
        "Title" critical "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_invalid_lens_rejected() {
    local rc=0
    echo "body" | "$REPORT" --type documentation --lens Pizza \
        "Title" nit "docs/x.md:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_code_with_lens_rejected() {
    local rc=0
    echo "body" | "$REPORT" --type code --lens Line \
        "Title" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- required args ----

test_missing_type_fails() {
    local rc=0
    echo "body" | "$REPORT" "Title" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_missing_title_fails() {
    local rc=0
    echo "body" | "$REPORT" --type code "" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_missing_summary_fails() {
    local rc=0
    echo "body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

# ---- --force / overwrite ----

test_refuses_overwrite_without_force() {
    echo "first body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "First summary."
    local rc=0
    echo "second body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Second summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    local sum; sum=$(grep '^First' .findings/title.md | head -1)
    assert_equal "First summary." "$sum"
}

test_force_allows_overwrite() {
    echo "first" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "First."
    echo "second" | "$REPORT" --force --type code "Title" nit "src/x.cs:1" "Principle" "Second."
    local sum; sum=$(grep '^Second' .findings/title.md | head -1)
    assert_equal "Second." "$sum"
}

# ---- slug pipeline under LC_ALL=C ----

test_slug_collapses_em_dash_to_dash() {
    # Em-dash is non-ASCII; under LC_ALL=C tr/sed treats it as non-alphanumeric
    # and the slug collapses it to a dash with surrounding word chars preserved.
    echo "body" | "$REPORT" --type code "Foo — Bar" nit "src/x.cs:1" "Principle" "Summary."
    assert_file_exists ".findings/foo-bar.md"
}

test_slug_handles_pure_non_ascii_predictably() {
    # Pure non-ASCII title: every char is non-alphanumeric → slug is empty → error.
    local rc=0
    echo "body" | "$REPORT" --type code "日本語" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_slug_caps_at_80_chars() {
    local long_title; long_title=$(printf 'a%.0s' {1..120})
    echo "body" | "$REPORT" --type code "$long_title" nit "src/x.cs:1" "Principle" "Summary."
    # The slug is the first 80 lowercase chars of the title (all 'a').
    local expected; expected=$(printf 'a%.0s' {1..80})
    assert_file_exists ".findings/${expected}.md"
}

# ---- body ----

test_body_appended_after_head() {
    printf '## Observation\nthe code does X\n' | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Summary."
    local content; content=$(cat .findings/title.md)
    assert_contains "$content" "## Observation"
    assert_contains "$content" "the code does X"
}

# ---- silent success ----

test_success_silent() {
    local out; out=$(echo "body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null)
    assert_equal "" "$out"
}
