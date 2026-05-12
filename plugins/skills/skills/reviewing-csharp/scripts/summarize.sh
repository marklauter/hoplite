#!/usr/bin/env bash
# Summarize the .findings/ directory.
#
# Output:
#   line 1: counts — e.g., `0 important, 2 nit, 7 pre-existing`
#   line 2: verdict — based on the important count
#   line 3: non-canonical principle line, only if any finding's Principle is
#           not a writing-csharp Philosophy heading
#
# Verdict logic:
#   - any important > 0          → "diff is blocked on important findings"
#   - important == 0, nit > 0    → "diff is shippable; nits optional"
#   - important == 0, nit == 0   → "diff is shippable"
#   - any pre-existing           → appended "; pre-existing triage pending"
#
# Empty or missing .findings/ prints `no findings` and exits 0.
#
# Usage:
#   summarize.sh

set -e

if [ ! -d .findings ]; then
    echo "no findings"
    exit 0
fi

shopt -s nullglob
files=(.findings/*.md)

if [ ${#files[@]} -eq 0 ]; then
    echo "no findings"
    exit 0
fi

important=0
nit=0
preexisting=0
declare -a noncanonical

writing_skill="${CLAUDE_PLUGIN_ROOT:-}/skills/writing-csharp/SKILL.md"
canonical=""
if [ -f "$writing_skill" ]; then
    canonical=$(awk '/^## Philosophy/{flag=1; next} /^## /{flag=0} flag && /^### /{sub(/^### /, ""); print}' "$writing_skill")
fi

is_canonical() {
    local p="$1"
    [ -z "$canonical" ] && return 0
    while IFS= read -r line; do
        [ "$line" = "$p" ] && return 0
    done <<< "$canonical"
    return 1
}

for f in "${files[@]}"; do
    severity=$(sed -n '3s/^Severity: //p' "$f")
    principle=$(sed -n '5s/^Principle: //p' "$f")
    case "$severity" in
        important) important=$((important + 1)) ;;
        nit) nit=$((nit + 1)) ;;
        pre-existing) preexisting=$((preexisting + 1)) ;;
    esac
    if [ -n "$principle" ] && ! is_canonical "$principle"; then
        noncanonical+=("$(basename "$f"): $principle")
    fi
done

echo "$important important, $nit nit, $preexisting pre-existing"

if [ "$important" -gt 0 ]; then
    verdict="diff is blocked on important findings"
elif [ "$nit" -gt 0 ]; then
    verdict="diff is shippable; nits optional"
else
    verdict="diff is shippable"
fi

if [ "$preexisting" -gt 0 ]; then
    verdict="${verdict}; pre-existing triage pending"
fi

echo "$verdict"

if [ ${#noncanonical[@]} -gt 0 ]; then
    echo "${#noncanonical[@]} finding(s) cite a non-canonical principle — candidate(s) for writing-csharp:"
    for entry in "${noncanonical[@]}"; do
        echo "  $entry"
    done
fi
