"""Tests for check-frontmatter.py — the frontmatter well-formedness scan.

The wikilink checks live with the edge grammar (test_edge_grammar.py) and the launcher
in test_run_hook.py; this file covers ``_wellformedness_issues`` — the line-scan that a
frontmatter block, when present, is structurally valid YAML.

Stdlib ``unittest`` only, no pytest, so it runs under the same bare interpreter the hook
does. The hook module has a hyphen in its name, so it is loaded by path, not imported.

Run: ``python -m unittest plugins.hoplite-skills.hooks.test_check_frontmatter`` or,
from this directory, ``python test_check_frontmatter.py``.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent / "check-frontmatter.py"
_spec = importlib.util.spec_from_file_location("check_frontmatter", HOOK_PATH)
assert _spec is not None and _spec.loader is not None
check_frontmatter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_frontmatter)

wellformedness_issues = check_frontmatter._wellformedness_issues


def fm(block: str) -> list[str]:
    """Well-formedness issues for the frontmatter body (text between the fences)."""
    return wellformedness_issues(block.split("\n"))


class WellFormedBlocksPassClean(unittest.TestCase):
    def test_flat_mapping(self) -> None:
        self.assertEqual(fm("title: A note\nsummary: one line"), [])

    def test_nested_mapping(self) -> None:
        self.assertEqual(fm("document:\n  tags: [note]\n  created: 2026-05-25"), [])

    def test_block_list(self) -> None:
        self.assertEqual(fm("contrast:\n  - a\n  - b"), [])

    def test_block_list_zero_indent(self) -> None:
        # a block-list item at column 0 is valid YAML and belongs to the key above
        self.assertEqual(fm("contrast:\n- a\n- b"), [])

    def test_flow_list(self) -> None:
        self.assertEqual(fm("tags: [note, design]"), [])

    def test_wrapped_flow_list(self) -> None:
        # a flow collection spanning lines is a continuation, not a stray root line
        self.assertEqual(fm('cites: ["[[a]]",\n  "[[b]]"]'), [])

    def test_quoted_wikilink(self) -> None:
        self.assertEqual(fm('cites: "[[circle]]"'), [])

    def test_value_with_colon(self) -> None:
        self.assertEqual(fm("url: http://example.com\ntime: 12:30"), [])

    def test_comments_and_blanks(self) -> None:
        self.assertEqual(fm("# a comment\n\ntitle: A note"), [])

    def test_key_opening_nested_block(self) -> None:
        self.assertEqual(fm("document:\n  status: draft"), [])

    def test_empty_block(self) -> None:
        self.assertEqual(fm(""), [])


class TabsInIndentation(unittest.TestCase):
    def test_leading_tab_flagged(self) -> None:
        issues = fm("document:\n\ttags: [note]")
        self.assertTrue(any("tab in indentation" in m for m in issues), issues)

    def test_tab_after_spaces_flagged(self) -> None:
        issues = fm("document:\n  \ttags: [note]")
        self.assertTrue(any("tab in indentation" in m for m in issues), issues)

    def test_tab_inside_value_not_flagged(self) -> None:
        # a tab in the value, not the indentation, is not an indentation error
        self.assertEqual(fm("summary: a\tb"), [])


class RootLinesThatAreNotMappingEntries(unittest.TestCase):
    def test_bare_scalar_flagged(self) -> None:
        issues = fm("title: A note\nstray text with no colon")
        self.assertTrue(any("mapping entry" in m for m in issues), issues)

    def test_missing_space_after_colon_flagged(self) -> None:
        # `title:Foo` is a plain scalar in YAML, not a mapping entry
        issues = fm("title:Foo")
        self.assertTrue(any("mapping entry" in m for m in issues), issues)

    def test_line_numbers_are_file_lines(self) -> None:
        # fm_lines[0] is file line 2 (after the opening `---`)
        issues = fm("title: A note\nsummary: fine\nstray")
        self.assertTrue(any(m.startswith("line 4:") for m in issues), issues)

    def test_long_line_truncated_in_message(self) -> None:
        issues = fm("x" * 80)
        self.assertTrue(any("..." in m for m in issues), issues)

    def test_multiple_issues_all_reported(self) -> None:
        issues = fm("stray one\nalso stray")
        self.assertEqual(sum("mapping entry" in m for m in issues), 2)


if __name__ == "__main__":
    unittest.main()
