#!/usr/bin/env bash
# Produce the canonical scope for a review pass.
#
# Three modes:
#   1. Diff mode (default) — git diff against HEAD or a ref.
#   2. Audit mode (--all)  — walk a directory tree (filesystem).
#   3. Paths mode (--paths) — explicit files and/or directories.
#
# When invoked with no args against a clean tree (or outside a git repo),
# the script emits a structured hint and exits non-zero. The caller decides
# whether to ask the user or fall back to a skill-declared default.
#
# Output sections:
#   ==> files       changed/audited file paths (status markers M/A/D/R in
#                   diff mode only; bare paths in audit and paths modes).
#   ==> diff        full unified diff (diff mode only).
#   ==> untracked   new files not yet under git (diff mode, no-arg case only).
#
# Output discipline:
#   - Success: the sections above (varies by mode).
#   - Failure: error to stderr, exit non-zero.
#   - Clean-tree no-args: hint to stderr, exit 1.
#
# Usage:
#   changes.sh                     diff mode: uncommitted vs HEAD
#                                  (staged + unstaged + untracked file list)
#   changes.sh <ref>               diff against <ref> (e.g. main, HEAD~3)
#   changes.sh <ref1> <ref2>       three-dot diff: what is on <ref2> since
#                                  it diverged from <ref1>
#   changes.sh --all [<dir>]       audit mode: walk <dir> (default: .).
#                                  Filesystem scan. Skips hidden dirs and
#                                  symlinks. Respects .gitignore when in a
#                                  git repo. No git repo required.
#   changes.sh --paths <p>...      paths mode: enumerate the given paths.
#                                  Directories expand recursively (same
#                                  walker as --all). Files included as-is.
#                                  Errors on a missing path. No git repo
#                                  required. Consumes all following args
#                                  until next flag.

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

emit_hint() {
    cat >&2 <<'EOF'
no diff detected. specify scope explicitly:
  changes.sh <ref>              # diff against ref
  changes.sh --paths <p>...     # review specific files or dirs
  changes.sh --all [<dir>]      # audit directory (default: .)
EOF
}

# Filter helper: read paths on stdin, drop hidden entries and symlinks,
# emit only regular files. Paths are expected relative to cwd.
filter_paths() {
    while IFS= read -r path; do
        path="${path#./}"
        # Skip any path with a hidden segment (segment starting with .).
        # Wrap with leading and trailing slash so the pattern matches
        # leading hidden segments and full-path hidden segments uniformly.
        case "/$path/" in
            */.*/*) continue ;;
        esac
        [ -L "$path" ] && continue
        [ -f "$path" ] && echo "$path"
    done
}

# Walk a directory. Respects .gitignore when in a git repo; otherwise
# falls back to a plain filesystem walk. Output: sorted relative paths.
walk_dir() {
    local dir="$1"
    if git rev-parse --git-dir >/dev/null 2>&1; then
        # ls-files emits paths relative to cwd when run with a pathspec.
        # --cached: tracked files. --others: untracked. --exclude-standard:
        # honors .gitignore, .git/info/exclude, and global excludes.
        git ls-files --cached --others --exclude-standard -- "$dir" 2>/dev/null \
            | filter_paths \
            | LC_ALL=C sort -u
    else
        find "$dir" -type f 2>/dev/null \
            | filter_paths \
            | LC_ALL=C sort -u
    fi
}

# Expand one path arg from --paths into zero or more file paths.
# A file passes through; a directory is walked; a missing path errors.
expand_path() {
    local arg="$1"
    if [ -f "$arg" ]; then
        # Don't filter explicit files — the user named them deliberately.
        # But still drop symlinks (they cause loops and ambiguity).
        if [ -L "$arg" ]; then
            echo "changes.sh: symlink skipped: $arg" >&2
            return 0
        fi
        echo "${arg#./}"
    elif [ -d "$arg" ]; then
        walk_dir "$arg"
    else
        echo "changes.sh: path does not exist: $arg" >&2
        return 1
    fi
}

run_git() {
    local output
    output=$(git "$@" 2>&1) || { local code=$?; echo "$output"; exit $code; }
    echo "$output"
}

# Diff mode against a ref (or HEAD when no ref). Preserves prior behavior.
do_diff() {
    local range="$1"
    local show_untracked="$2"

    echo "==> files"
    local files
    files=$(run_git diff --name-status "$range")
    if [ -z "$files" ]; then
        echo "(no changes)"
    else
        echo "$files"
    fi

    echo
    echo "==> diff"
    local diff
    diff=$(run_git diff --no-color "$range")
    if [ -z "$diff" ]; then
        echo "(no diff)"
    else
        echo "$diff"
    fi

    if [ "$show_untracked" = "1" ]; then
        echo
        echo "==> untracked"
        local untracked
        untracked=$(run_git ls-files --others --exclude-standard)
        if [ -z "$untracked" ]; then
            echo "(none)"
        else
            echo "$untracked"
        fi
    fi
}

# Audit/paths mode: emit a single ==> files section with bare paths.
do_files() {
    local paths="$1"
    echo "==> files"
    if [ -z "$paths" ]; then
        echo "(no files)"
    else
        echo "$paths"
    fi
}

# Argument parsing. --all and --paths are mutually exclusive with each
# other and with ref args. They consume the rest of the argv until the
# next flag (none currently exist after them).

if [ $# -ge 1 ] && [ "$1" = "--all" ]; then
    shift
    if [ $# -gt 1 ]; then
        echo "changes.sh: --all takes at most one directory arg" >&2
        exit 2
    fi
    target="${1:-.}"
    if [ ! -d "$target" ]; then
        echo "changes.sh: --all target is not a directory: $target" >&2
        exit 2
    fi
    paths=$(walk_dir "$target")
    do_files "$paths"
    exit 0
fi

if [ $# -ge 1 ] && [ "$1" = "--paths" ]; then
    shift
    if [ $# -lt 1 ]; then
        echo "changes.sh: --paths requires at least one path" >&2
        exit 2
    fi
    all_paths=""
    for arg in "$@"; do
        if expanded=$(expand_path "$arg"); then
            if [ -n "$expanded" ]; then
                if [ -z "$all_paths" ]; then
                    all_paths="$expanded"
                else
                    all_paths="${all_paths}"$'\n'"${expanded}"
                fi
            fi
        else
            exit 2
        fi
    done
    # Sort and dedupe across all expanded args.
    if [ -n "$all_paths" ]; then
        all_paths=$(echo "$all_paths" | LC_ALL=C sort -u)
    fi
    do_files "$all_paths"
    exit 0
fi

# Diff mode (existing behavior, plus the clean-tree hint).
ARG1="${1:-}"
ARG2="${2:-}"

if [ -z "$ARG1" ]; then
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        emit_hint
        exit 1
    fi
    has_diff=$(git diff --name-only HEAD 2>/dev/null | head -n 1 || true)
    has_untracked=$(git ls-files --others --exclude-standard 2>/dev/null | head -n 1 || true)
    if [ -z "$has_diff" ] && [ -z "$has_untracked" ]; then
        emit_hint
        exit 1
    fi
    do_diff "HEAD" "1"
elif [ -z "$ARG2" ]; then
    do_diff "$ARG1" "0"
else
    do_diff "${ARG1}...${ARG2}" "0"
fi
