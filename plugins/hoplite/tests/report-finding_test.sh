#!/usr/bin/env bash
# Tests for plugins/hoplite/scripts/report-finding.sh

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

# ---- slug collision: auto-suffix ----

test_collision_auto_suffixes_with_counter() {
    echo "first body" | "$REPORT" --type code "Title" nit "src/x.cs:1" "Principle" "First summary."
    echo "second body" | "$REPORT" --type code "Title" nit "src/x.cs:2" "Principle" "Second summary."
    echo "third body" | "$REPORT" --type code "Title" nit "src/x.cs:3" "Principle" "Third summary."
    assert_file_exists ".findings/title.md"
    assert_file_exists ".findings/title-2.md"
    assert_file_exists ".findings/title-3.md"
    local first; first=$(grep '^First' .findings/title.md | head -1)
    assert_equal "First summary." "$first"
    local second; second=$(grep '^Second' .findings/title-2.md | head -1)
    assert_equal "Second summary." "$second"
    local third; third=$(grep '^Third' .findings/title-3.md | head -1)
    assert_equal "Third summary." "$third"
}

test_force_flag_rejected_as_unknown() {
    local rc=0
    echo "body" | "$REPORT" --force --type code "Title" nit "src/x.cs:1" "Principle" "Summary." 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
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

# ---- repo-root anchoring ----
# When invoked from a subdirectory of a git repo, the finding must land at the
# repo root, not in a `.findings/` under the caller's CWD. The bug being
# prevented: build-gate.sh anchors at the solution directory (often `src/`), so
# follow-up `report-finding.sh` calls inherit that CWD.

test_writes_to_repo_root_from_subdirectory() {
    git init -q
    mkdir -p src
    cd src
    echo "body" | "$REPORT" --type code "Anchored" nit "src/x.cs:1" "Principle" "Summary."
    assert_file_exists "../.findings/anchored.md"
    assert_file_not_exists ".findings/anchored.md"
}
