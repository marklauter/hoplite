#!/usr/bin/env bash
# Tests for plugins/hoplite/skills/triaging-findings/scripts/file.sh

FILE="$PLUGIN_ROOT/skills/triaging-findings/scripts/file.sh"

make_finding() {
    local slug="$1" title="$2"
    mkdir -p .findings
    {
        printf '# %s\n\n' "$title"
        printf 'Severity: nit\n'
        printf 'Type: code\n'
        printf 'Location: `src/x.cs:1`\n'
        printf 'Principle: Some principle\n'
        printf 'Summary.\n\n'
        printf '## Observation\nFinding body.\n'
    } > ".findings/${slug}.md"
}

make_template() {
    mkdir -p .github/ISSUE_TEMPLATE
    cat > .github/ISSUE_TEMPLATE/tech-debt.yml <<'EOF'
name: Tech Debt
description: Test template
labels: ["tech-debt"]
EOF
}

# Stub gh so create.sh runs without reaching GitHub. Modes:
#   success  → prints a URL on stdout, exits 0
#   failure  → prints an error on stderr, exits 1
make_gh_stub() {
    local mode="${1:-success}"
    mkdir -p bin
    if [ "$mode" = "success" ]; then
        cat > bin/gh <<'EOF'
#!/usr/bin/env bash
# Drain stdin (create.sh pipes the body via --body-file -).
cat > /dev/null
echo "https://github.com/test/repo/issues/42"
EOF
    else
        cat > bin/gh <<'EOF'
#!/usr/bin/env bash
cat > /dev/null
echo "gh: simulated API error" >&2
exit 1
EOF
    fi
    chmod +x bin/gh
    export PATH="$PWD/bin:$PATH"
}

# ---- happy path ----

test_file_creates_issue_and_deletes_finding() {
    make_finding "to-file" "Refactor serialization layer"
    make_template
    make_gh_stub success
    echo "composed body" | "$FILE" "to-file" tech-debt.yml > /dev/null
    assert_file_not_exists ".findings/to-file.md"
}

test_file_prints_gh_url_on_success() {
    make_finding "to-file" "Title"
    make_template
    make_gh_stub success
    local out; out=$(echo "body" | "$FILE" "to-file" tech-debt.yml 2>&1)
    assert_contains "$out" "https://github.com/test/repo/issues/42"
}

# ---- failure preserves the finding ----

test_file_preserves_finding_when_gh_fails() {
    make_finding "to-file" "Title"
    make_template
    make_gh_stub failure
    local rc=0
    echo "body" | "$FILE" "to-file" tech-debt.yml > /dev/null 2>&1 || rc=$?
    assert_exit_code 1 "$rc"
    assert_file_exists ".findings/to-file.md"
}

# ---- argument validation ----

test_missing_slug_fails() {
    local rc=0
    echo "body" | "$FILE" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_missing_template_fails() {
    local rc=0
    echo "body" | "$FILE" "some-slug" 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_slug_with_path_separator_rejected() {
    local rc=0
    echo "body" | "$FILE" "subdir/slug" tech-debt.yml 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_slug_with_md_suffix_rejected() {
    local rc=0
    echo "body" | "$FILE" "slug.md" tech-debt.yml 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_empty_stdin_rejected() {
    make_finding "to-file" "Title"
    local rc=0
    "$FILE" "to-file" tech-debt.yml < /dev/null 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    assert_file_exists ".findings/to-file.md"
}

# ---- missing target ----

test_missing_finding_fails() {
    make_template
    local rc=0
    echo "body" | "$FILE" "does-not-exist" tech-debt.yml 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
}

test_finding_without_h1_title_rejected() {
    make_template
    mkdir -p .findings
    printf 'No H1 here\n\nSeverity: nit\n' > .findings/no-title.md
    local rc=0
    echo "body" | "$FILE" "no-title" tech-debt.yml 2>/dev/null || rc=$?
    assert_exit_code 2 "$rc"
    assert_file_exists ".findings/no-title.md"
}

# ---- title is read from the finding's H1 ----
# The body on stdin is the reshaped body; the title comes from the finding.

test_h1_is_used_as_issue_title() {
    make_finding "to-file" "The exact title from H1"
    make_template
    # Stub captures argv and writes to a sentinel so we can assert.
    mkdir -p bin
    cat > bin/gh <<'EOF'
#!/usr/bin/env bash
cat > /dev/null
for arg in "$@"; do
    if [ "$prev" = "--title" ]; then
        printf '%s' "$arg" > "$TITLE_SINK"
    fi
    prev="$arg"
done
echo "https://example.invalid/issues/1"
EOF
    chmod +x bin/gh
    export PATH="$PWD/bin:$PATH"
    export TITLE_SINK="$PWD/captured-title"
    echo "body" | "$FILE" "to-file" tech-debt.yml > /dev/null
    local captured; captured=$(cat "$TITLE_SINK")
    assert_equal "The exact title from H1" "$captured"
}
