"""Tests for the stdio JSON-RPC host."""

from __future__ import annotations

import io
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Never, final

import pytest
from fakes import real

from hoplite_catalog.corpus import Corpus
from hoplite_catalog.server import (
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    respond,
    serve,
)


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "edge.md").write_text("---\ntitle: Edge\n---\n\n# Edge\n", encoding="utf-8")
    (docs / "loose.md").write_text("# Loose\n", encoding="utf-8")
    return tmp_path


def _request(method: str, params: dict[str, Any] | None = None, request_id: int = 1) -> str:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return json.dumps(message)


def _result(message: dict[str, Any] | None) -> dict[str, Any]:
    assert message is not None
    assert "error" not in message, message
    result: dict[str, Any] = message["result"]
    return result


def _error_of(message: dict[str, Any] | None) -> dict[str, Any]:
    assert message is not None
    error: Any = message["error"]
    return error


def _tool_text(message: dict[str, Any] | None) -> str:
    result = _result(message)
    text: str = result["content"][0]["text"]
    return text


class TestHandshake:
    def test_initialize_names_the_server_and_protocol(self, corpus: Path) -> None:
        result = _result(respond(real(corpus), _request("initialize")))
        assert result["protocolVersion"] == PROTOCOL_VERSION
        assert result["serverInfo"]["name"] == SERVER_NAME
        assert "tools" in result["capabilities"]

    def test_the_reported_version_matches_every_manifest(self) -> None:
        # Four files declare it and initialize reports one of them, so a bump that misses
        # any of them ships a server that lies about which version it is. pyproject was the
        # one left behind at 0.1.0. The marketplace entry is what a user installs from, and
        # it sits outside the plugin, which is how it escaped this test the first time.
        plugin = Path(__file__).parent.parent
        declared: str = json.loads(
            (plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
        packaged = tomllib.loads((plugin / "pyproject.toml").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (plugin.parent.parent / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        listed = next(
            entry["version"] for entry in marketplace["plugins"] if entry["name"] == "hoplite-mcp"
        )
        assert declared == SERVER_VERSION
        assert packaged["project"]["version"] == SERVER_VERSION
        assert listed == SERVER_VERSION

    def test_initialized_notification_gets_no_reply(self, corpus: Path) -> None:
        line = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert respond(real(corpus), line) is None

    def test_ping_is_answered(self, corpus: Path) -> None:
        assert _result(respond(real(corpus), _request("ping"))) == {}


class TestLaunchConfiguration:
    def test_the_working_directory_is_kept_off_the_import_path(self) -> None:
        # `-m` prepends the working directory to sys.path, ahead of the PYTHONPATH that
        # points at the plugin. Claude Code launches the server in the user's own project,
        # so a `hoplite_catalog/` or `hoplite_catalog.py` sitting in a cloned repo would
        # shadow the plugin and run at server start. `-P` is what stops that, and it is a
        # line in a JSON file with nothing else to keep it there.
        config = json.loads((Path(__file__).parents[1] / ".mcp.json").read_text(encoding="utf-8"))
        args: list[str] = config["mcpServers"]["catalog"]["args"]
        assert "-P" in args
        assert args.index("-P") < args.index("-m")


class TestToolsList:
    def test_advertises_both_tools(self, corpus: Path) -> None:
        tools = _result(respond(real(corpus), _request("tools/list")))["tools"]
        assert [tool["name"] for tool in tools] == ["contents", "vocabulary"]

    def test_both_tools_are_marked_read_only(self, corpus: Path) -> None:
        for tool in _result(respond(real(corpus), _request("tools/list")))["tools"]:
            assert tool["annotations"]["readOnlyHint"] is True
            assert tool["annotations"]["openWorldHint"] is False

    def test_every_input_is_optional(self, corpus: Path) -> None:
        tools = _result(respond(real(corpus), _request("tools/list")))["tools"]
        assert list(tools[0]["inputSchema"]["properties"]) == ["under", "keys"]
        assert list(tools[1]["inputSchema"]["properties"]) == ["under"]
        for tool in tools:
            assert tool["inputSchema"]["additionalProperties"] is False
            assert "required" not in tool["inputSchema"]


_HEADINGS = ("# directories", "# other files", "# documents")


def _section(text: str, heading: str) -> str:
    """The body of one group of the contents report.

    Anchored on the heading lines, not on blank lines: a blank line separates the groups
    and also separates two documents inside the last one, so the headings are what make
    the report unambiguous to read.
    """
    lines = text.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if any(line.startswith(candidate) for candidate in _HEADINGS)
    ]
    for start, end in zip(starts, [*starts[1:], len(lines)], strict=True):
        if lines[start].startswith(heading):
            return "\n".join(lines[start + 1 : end]).strip("\n")
    raise AssertionError(f"no {heading!r} group in:\n{text}")


_DOCS = {"under": "docs"}


class TestContents:
    def test_reports_the_subtree_the_other_files_and_the_documents(self, corpus: Path) -> None:
        (corpus / "docs" / "graph.pdf").write_text("", encoding="utf-8")
        params = {"name": "contents", "arguments": _DOCS}
        message = respond(real(corpus), _request("tools/call", params))
        assert _tool_text(message) == (
            "# directories (documents directly in each)\n"
            "docs/ 2\n"
            "\n"
            "# other files\n"
            "docs/graph.pdf\n"
            "\n"
            "# documents\n"
            "docs/edge.md\n"
            "title: Edge\n"
            "\n"
            "docs/loose.md"
        )
        assert _result(message)["isError"] is False

    def test_the_subtree_carries_every_folder_with_its_count(self, corpus: Path) -> None:
        (corpus / "docs" / "sub" / "deeper").mkdir(parents=True)
        (corpus / "docs" / "sub" / "deep.md").write_text("---\ntitle: D\n---\n", encoding="utf-8")
        text = _tool_text(
            respond(real(corpus), _request("tools/call", {"name": "contents", "arguments": _DOCS}))
        )
        assert _section(text, "# directories") == "docs/ 2\n  sub/ 1\n    deeper/ 0"

    def test_documents_do_not_recurse(self, corpus: Path) -> None:
        # The whole point: the caller pays for the folder it asked for, not the corpus.
        (corpus / "docs" / "sub").mkdir()
        (corpus / "docs" / "sub" / "deep.md").write_text("---\ntitle: D\n---\n", encoding="utf-8")
        text = _tool_text(
            respond(real(corpus), _request("tools/call", {"name": "contents", "arguments": _DOCS}))
        )
        assert "docs/sub/deep.md" not in text

    def test_the_default_is_the_corpus_root(self, corpus: Path) -> None:
        # Not a guessed folder name: one corpus keeps its documents in `docs`, another in
        # `vault`, another at the top level. The root is the only answer that fits all three.
        text = _tool_text(respond(real(corpus), _request("tools/call", {"name": "contents"})))
        assert _section(text, "# directories") == "./ 0\n  docs/ 2"

    def test_the_default_never_walks_a_hidden_folder(self, corpus: Path) -> None:
        # The corpus root is a working directory, so it is where .git and .venv live.
        (corpus / ".git" / "objects").mkdir(parents=True)
        text = _tool_text(respond(real(corpus), _request("tools/call", {"name": "contents"})))
        assert ".git" not in text

    def test_naming_a_hidden_folder_outright_still_works(self, corpus: Path) -> None:
        (corpus / ".github").mkdir()
        (corpus / ".github" / "ci.md").write_text("---\ntitle: CI\n---\n", encoding="utf-8")
        params = {"name": "contents", "arguments": {"under": ".github"}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is False
        assert _section(_tool_text(message), "# documents") == ".github/ci.md\ntitle: CI"

    def test_a_folder_named_like_a_document_does_not_break_the_call(self, corpus: Path) -> None:
        # Obsidian produces these. It used to be counted as a document, listed as a folder,
        # and then read — which failed and took the whole listing with it.
        (corpus / "docs" / "sub.md").mkdir()
        params = {"name": "contents", "arguments": _DOCS}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is False
        text = _tool_text(message)
        assert _section(text, "# directories") == "docs/ 2\n  sub.md/ 0"
        assert _section(text, "# documents") == "docs/edge.md\ntitle: Edge\n\ndocs/loose.md"

    def test_under_walks_into_one_folder(self, corpus: Path) -> None:
        (corpus / "docs" / "sub").mkdir()
        (corpus / "docs" / "sub" / "deep.md").write_text("---\ntitle: D\n---\n", encoding="utf-8")
        params = {"name": "contents", "arguments": {"under": "docs/sub"}}
        text = _tool_text(respond(real(corpus), _request("tools/call", params)))
        assert _section(text, "# documents") == "docs/sub/deep.md\ntitle: D"

    def test_a_folder_holding_no_documents_is_a_real_answer(self, corpus: Path) -> None:
        (corpus / "docs" / "empty").mkdir()
        params = {"name": "contents", "arguments": {"under": "docs/empty"}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is False
        assert _section(_tool_text(message), "# documents") == "none"

    def test_naming_one_document_returns_the_listing_alone(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": "docs/edge.md"}}
        assert _tool_text(respond(real(corpus), _request("tools/call", params))) == (
            "docs/edge.md\ntitle: Edge"
        )

    def test_a_bad_under_is_an_error_result_not_a_protocol_error(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": "docs/nope"}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "does not exist" in _tool_text(message)

    def test_escaping_the_root_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": ".."}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "outside the corpus root" in _tool_text(message)

    def test_a_non_string_under_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": 7}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True

    def test_keys_projects_the_frontmatter(self, corpus: Path) -> None:
        (corpus / "docs" / "edge.md").write_text(
            "---\ntitle: Edge\nsummary: long prose\ntags: [glossary]\n---\n", encoding="utf-8"
        )
        params = {"name": "contents", "arguments": {"under": "docs", "keys": ["title", "tags"]}}
        text = _tool_text(respond(real(corpus), _request("tools/call", params)))
        assert "title: Edge" in text
        assert "tags: [glossary]" in text
        assert "summary" not in text

    def test_omitting_keys_keeps_the_summary(self, corpus: Path) -> None:
        (corpus / "docs" / "edge.md").write_text(
            "---\ntitle: Edge\nsummary: long prose\n---\n", encoding="utf-8"
        )
        text = _tool_text(
            respond(real(corpus), _request("tools/call", {"name": "contents", "arguments": _DOCS}))
        )
        assert "summary: long prose" in text

    def test_an_empty_keys_list_returns_paths_alone(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": "docs", "keys": []}}
        text = _tool_text(respond(real(corpus), _request("tools/call", params)))
        assert _section(text, "# documents") == "docs/edge.md\n\ndocs/loose.md"

    def test_a_non_list_keys_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"keys": "title"}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "list of strings" in _tool_text(message)

    def test_a_non_string_key_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"keys": ["title", 7]}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True

    def test_a_misspelled_key_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": "docs", "keys": ["titel"]}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "none of the requested keys" in _tool_text(message)

    def test_a_frontmatterless_folder_is_not_blamed_on_the_keys(self, corpus: Path) -> None:
        # Nothing here has frontmatter, so an empty projection is the corpus's doing, not
        # a typo. Refusing with a message naming the keys would be confidently wrong.
        bare = corpus / "docs" / "bare"
        bare.mkdir()
        (bare / "a.md").write_text("# A\n", encoding="utf-8")
        params = {"name": "contents", "arguments": {"under": "docs/bare", "keys": ["title"]}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is False
        assert _section(_tool_text(message), "# documents") == "docs/bare/a.md"

    def test_a_link_out_of_the_corpus_is_reported_not_refused(self, corpus: Path) -> None:
        # The reason stands where the frontmatter would be, and the rest of the folder
        # still lists. It used to fail the whole call, with no argument left to route
        # around it once `exclude` was removed.
        try:
            (corpus / "docs" / "dangling.md").symlink_to(corpus.parent / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        message = respond(
            real(corpus), _request("tools/call", {"name": "contents", "arguments": _DOCS})
        )
        assert _result(message)["isError"] is False
        assert _section(_tool_text(message), "# documents") == (
            "docs/dangling.md\nlinks to a target outside the corpus\n\n"
            "docs/edge.md\ntitle: Edge\n\ndocs/loose.md"
        )
        assert str(corpus.parent) not in _tool_text(message)

    def test_an_unreadable_document_is_reported_without_a_host_path(self, corpus: Path) -> None:
        # A link dangling inside the corpus passes containment and fails at the read. The
        # raw OSError would leak a host path and name the document by where its bytes live.
        try:
            (corpus / "docs" / "inner.md").symlink_to(corpus / "docs" / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        message = respond(
            real(corpus), _request("tools/call", {"name": "contents", "arguments": _DOCS})
        )
        assert _result(message)["isError"] is False
        text = _tool_text(message)
        assert "docs/inner.md\ncannot be read (" in text
        assert "docs/edge.md\ntitle: Edge" in text
        assert str(corpus) not in text

    def test_an_unreadable_document_does_not_stop_the_key_count(self, corpus: Path) -> None:
        # vocabulary recurses, so raising here cost the whole subtree for one bad link.
        try:
            (corpus / "docs" / "inner.md").symlink_to(corpus / "docs" / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        message = respond(real(corpus), _request("tools/call", {"name": "vocabulary"}))
        assert _result(message)["isError"] is False
        assert _tool_text(message) == "title: 1"

    def test_a_mis_encoded_document_does_not_stop_the_key_count(self, corpus: Path) -> None:
        # UnicodeDecodeError is a ValueError, so _call_tool caught it as a whole-call
        # failure: one latin-1 file cost vocabulary the entire subtree. No symlink needed.
        (corpus / "docs" / "latin.md").write_bytes(b"---\ntitle: caf\xe9\n---\n")

        message = respond(real(corpus), _request("tools/call", {"name": "vocabulary"}))
        assert _result(message)["isError"] is False
        assert _tool_text(message) == "title: 1"

    def test_a_key_absent_from_some_documents_is_fine(self, corpus: Path) -> None:
        # docs/loose.md has no frontmatter at all; docs/edge.md has a title.
        params = {"name": "contents", "arguments": {"under": "docs", "keys": ["title"]}}
        text = _tool_text(respond(real(corpus), _request("tools/call", params)))
        assert _section(text, "# documents") == "docs/edge.md\ntitle: Edge\n\ndocs/loose.md"


class TestVocabulary:
    def test_counts_the_keys_across_the_whole_subtree(self, corpus: Path) -> None:
        (corpus / "docs" / "sub").mkdir()
        (corpus / "docs" / "sub" / "deep.md").write_text(
            "---\ntitle: D\nstatus: locked\n---\n", encoding="utf-8"
        )
        message = respond(real(corpus), _request("tools/call", {"name": "vocabulary"}))
        assert _tool_text(message) == "status: 1\ntitle: 2"
        assert _result(message)["isError"] is False

    def test_under_scopes_the_count(self, corpus: Path) -> None:
        (corpus / "docs" / "sub").mkdir()
        (corpus / "docs" / "sub" / "deep.md").write_text(
            "---\nstatus: locked\n---\n", encoding="utf-8"
        )
        params = {"name": "vocabulary", "arguments": {"under": "docs/sub"}}
        assert _tool_text(respond(real(corpus), _request("tools/call", params))) == "status: 1"

    def test_a_folder_with_no_frontmatter_says_so(self, corpus: Path) -> None:
        bare = corpus / "docs" / "bare"
        bare.mkdir()
        (bare / "a.md").write_text("# A\n", encoding="utf-8")
        params = {"name": "vocabulary", "arguments": {"under": "docs/bare"}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is False
        assert _tool_text(message) == "no frontmatter keys under 'docs/bare'"

    def test_it_answers_which_keys_contents_can_be_asked_for(self, corpus: Path) -> None:
        # The reason the tool exists: `contents(keys=[...])` refuses a key that does not
        # exist, and nothing else could tell the caller which ones do.
        (corpus / "docs" / "edge.md").write_text(
            "---\ntitle: Edge\nstatus: locked\n---\n", encoding="utf-8"
        )
        keys = [
            line.split(":")[0]
            for line in _tool_text(
                respond(real(corpus), _request("tools/call", {"name": "vocabulary"}))
            ).splitlines()
        ]
        params = {"name": "contents", "arguments": {"keys": keys}}
        assert _result(respond(real(corpus), _request("tools/call", params)))["isError"] is False

    def test_the_default_counts_from_the_corpus_root(self, corpus: Path) -> None:
        assert _tool_text(
            respond(real(corpus), _request("tools/call", {"name": "vocabulary"}))
        ) == ("title: 1")

    def test_hidden_folders_are_never_counted(self, corpus: Path) -> None:
        # A .venv is full of markdown, and counting it would report keys from packages
        # while `contents` says the folder does not exist.
        venv = corpus / ".venv" / "pkg"
        venv.mkdir(parents=True)
        (venv / "README.md").write_text("---\nlicense: MIT\n---\n", encoding="utf-8")
        text = _tool_text(respond(real(corpus), _request("tools/call", {"name": "vocabulary"})))
        assert text == "title: 1"

    def test_a_bad_under_is_an_error_result(self, corpus: Path) -> None:
        params = {"name": "vocabulary", "arguments": {"under": "docs/nope"}}
        message = respond(real(corpus), _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "does not exist" in _tool_text(message)

    def test_a_non_string_under_is_refused(self, corpus: Path) -> None:
        params = {"name": "vocabulary", "arguments": {"under": 7}}
        assert _result(respond(real(corpus), _request("tools/call", params)))["isError"] is True

    def test_an_unknown_tool_is_an_error_result(self, corpus: Path) -> None:
        message = respond(real(corpus), _request("tools/call", {"name": "nope"}))
        assert _result(message)["isError"] is True
        assert "unknown tool" in _tool_text(message)


class TestProtocolErrors:
    def test_malformed_json_returns_a_parse_error(self, corpus: Path) -> None:
        assert _error_of(respond(real(corpus), "{not json"))["code"] == -32700

    def test_an_unknown_method_returns_method_not_found(self, corpus: Path) -> None:
        assert _error_of(respond(real(corpus), _request("resources/list")))["code"] == -32601

    def test_a_json_array_is_an_invalid_request(self, corpus: Path) -> None:
        assert _error_of(respond(real(corpus), "[1, 2]"))["code"] == -32600


@final
@dataclass(frozen=True, slots=True)
class _RefusingFiles:
    """A ``Files`` that fails the test if the host reads the corpus at all.

    A notification owes no reply, so ``respond`` returns ``None`` whether or not it ran the
    method first. Refusing every read is what makes the difference observable.
    """

    def _refuse(self, path: Path) -> Never:
        raise AssertionError(f"the corpus was read for a notification: {path}")

    def entries(self, directory: Path) -> tuple[Path, ...]:
        self._refuse(directory)

    def is_directory(self, path: Path) -> bool:
        self._refuse(path)

    def is_file(self, path: Path) -> bool:
        self._refuse(path)

    def is_symlink(self, path: Path) -> bool:
        self._refuse(path)

    def exists(self, path: Path) -> bool:
        self._refuse(path)

    def resolve(self, path: Path) -> Path:
        # The one method that answers. `Corpus` resolves its root once at construction,
        # which in the host happens before any traffic; refusing here would fail the test
        # on the setup rather than on the behavior it watches. Nothing can be served off a
        # resolve alone — every dispatch path reaches `exists`, `entries`, or `is_file`.
        return path

    def read_text(self, path: Path) -> str:
        self._refuse(path)


class TestNotifications:
    def test_a_tools_call_without_an_id_is_not_dispatched(self, corpus: Path) -> None:
        # Dispatching first and discarding the result let a `vocabulary` notification read
        # every document in the corpus to answer a message that owes no reply.
        line = json.dumps(
            {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "vocabulary"}}
        )
        assert respond(Corpus(_RefusingFiles(), corpus), line) is None

    def test_an_unknown_method_without_an_id_is_still_silent(self, corpus: Path) -> None:
        line = json.dumps({"jsonrpc": "2.0", "method": "resources/list"})
        assert respond(Corpus(_RefusingFiles(), corpus), line) is None


class TestServeLoop:
    def test_replies_to_requests_and_skips_notifications(self, corpus: Path) -> None:
        lines = "\n".join(
            [
                _request("initialize"),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                "",
                _request("tools/list", request_id=2),
            ]
        )
        stdout = io.StringIO()
        assert serve(real(corpus), io.StringIO(lines), stdout) == 0

        replies = [json.loads(line) for line in stdout.getvalue().splitlines()]
        assert [reply["id"] for reply in replies] == [1, 2]

    def test_a_leading_byte_order_mark_is_tolerated(self, corpus: Path) -> None:
        stdout = io.StringIO()
        assert serve(real(corpus), io.StringIO("﻿" + _request("initialize")), stdout) == 0
        assert json.loads(stdout.getvalue())["id"] == 1
