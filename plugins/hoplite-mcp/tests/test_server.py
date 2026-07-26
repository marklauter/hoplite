"""Tests for the stdio JSON-RPC host."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

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
        result = _result(respond(corpus, _request("initialize")))
        assert result["protocolVersion"] == PROTOCOL_VERSION
        assert result["serverInfo"]["name"] == SERVER_NAME
        assert "tools" in result["capabilities"]

    def test_the_reported_version_matches_the_plugin_manifest(self) -> None:
        # initialize reports SERVER_VERSION, so a bumped manifest must not leave it behind.
        manifest = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"
        declared: str = json.loads(manifest.read_text(encoding="utf-8"))["version"]
        assert declared == SERVER_VERSION

    def test_initialized_notification_gets_no_reply(self, corpus: Path) -> None:
        line = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert respond(corpus, line) is None

    def test_ping_is_answered(self, corpus: Path) -> None:
        assert _result(respond(corpus, _request("ping"))) == {}


class TestToolsList:
    def test_advertises_contents(self, corpus: Path) -> None:
        tools = _result(respond(corpus, _request("tools/list")))["tools"]
        assert [tool["name"] for tool in tools] == ["contents"]

    def test_contents_is_marked_read_only(self, corpus: Path) -> None:
        tool = _result(respond(corpus, _request("tools/list")))["tools"][0]
        assert tool["annotations"]["readOnlyHint"] is True
        assert tool["annotations"]["openWorldHint"] is False

    def test_every_input_is_optional(self, corpus: Path) -> None:
        schema = _result(respond(corpus, _request("tools/list")))["tools"][0]["inputSchema"]
        assert list(schema["properties"]) == ["under", "keys", "exclude"]
        assert schema["additionalProperties"] is False
        assert "required" not in schema


class TestToolsCall:
    def test_lists_the_corpus(self, corpus: Path) -> None:
        message = respond(corpus, _request("tools/call", {"name": "contents"}))
        assert _tool_text(message) == "docs/edge.md\ntitle: Edge\n\ndocs/loose.md"
        assert _result(message)["isError"] is False

    def test_under_scopes_the_listing(self, corpus: Path) -> None:
        (corpus / "docs" / "sub").mkdir()
        (corpus / "docs" / "sub" / "deep.md").write_text("---\ntitle: D\n---\n", encoding="utf-8")
        params = {"name": "contents", "arguments": {"under": "docs/sub"}}
        assert _tool_text(respond(corpus, _request("tools/call", params))) == (
            "docs/sub/deep.md\ntitle: D"
        )

    def test_an_empty_folder_says_so(self, corpus: Path) -> None:
        (corpus / "docs" / "empty").mkdir()
        params = {"name": "contents", "arguments": {"under": "docs/empty"}}
        assert "no markdown documents" in _tool_text(
            respond(corpus, _request("tools/call", params))
        )

    def test_a_bad_under_is_an_error_result_not_a_protocol_error(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": "docs/nope"}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "does not exist" in _tool_text(message)

    def test_escaping_the_root_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": ".."}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "outside the corpus root" in _tool_text(message)

    def test_a_non_string_under_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": 7}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True

    def test_keys_projects_the_frontmatter(self, corpus: Path) -> None:
        (corpus / "docs" / "edge.md").write_text(
            "---\ntitle: Edge\nsummary: long prose\ntags: [glossary]\n---\n", encoding="utf-8"
        )
        params = {"name": "contents", "arguments": {"under": "docs", "keys": ["title", "tags"]}}
        text = _tool_text(respond(corpus, _request("tools/call", params)))
        assert "title: Edge" in text
        assert "tags: [glossary]" in text
        assert "summary" not in text

    def test_omitting_keys_keeps_the_summary(self, corpus: Path) -> None:
        (corpus / "docs" / "edge.md").write_text(
            "---\ntitle: Edge\nsummary: long prose\n---\n", encoding="utf-8"
        )
        text = _tool_text(respond(corpus, _request("tools/call", {"name": "contents"})))
        assert "summary: long prose" in text

    def test_an_empty_keys_list_returns_paths_alone(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"under": "docs", "keys": []}}
        text = _tool_text(respond(corpus, _request("tools/call", params)))
        assert text == "docs/edge.md\n\ndocs/loose.md"

    def test_a_non_list_keys_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"keys": "title"}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "list of strings" in _tool_text(message)

    def test_a_non_string_key_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"keys": ["title", 7]}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True

    def test_exclude_drops_a_folder(self, corpus: Path) -> None:
        (corpus / "docs" / "journal").mkdir()
        (corpus / "docs" / "journal" / "day.md").write_text(
            "---\ntitle: D\n---\n", encoding="utf-8"
        )
        params = {"name": "contents", "arguments": {"exclude": ["docs/journal"]}}
        text = _tool_text(respond(corpus, _request("tools/call", params)))
        assert "docs/journal/day.md" not in text
        assert "docs/edge.md" in text

    def test_excluding_everything_says_so(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"exclude": ["docs"]}}
        text = _tool_text(respond(corpus, _request("tools/call", params)))
        assert text == "no markdown documents under 'docs' after exclusions"

    def test_a_trailing_slash_on_exclude_still_excludes(self, corpus: Path) -> None:
        (corpus / "docs" / "journal").mkdir()
        (corpus / "docs" / "journal" / "day.md").write_text(
            "---\ntitle: D\n---\n", encoding="utf-8"
        )
        params = {"name": "contents", "arguments": {"exclude": ["docs/journal/"]}}
        assert "docs/journal/day.md" not in _tool_text(
            respond(corpus, _request("tools/call", params))
        )

    def test_a_misspelled_key_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"keys": ["titel"]}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "none of the requested keys" in _tool_text(message)

    def test_a_frontmatterless_subtree_is_not_blamed_on_the_keys(self, corpus: Path) -> None:
        # Nothing here has frontmatter, so an empty projection is the corpus's doing, not
        # a typo. Refusing with a message naming the keys would be confidently wrong.
        bare = corpus / "docs" / "bare"
        bare.mkdir()
        (bare / "a.md").write_text("# A\n", encoding="utf-8")
        params = {"name": "contents", "arguments": {"under": "docs/bare", "keys": ["title"]}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is False
        assert _tool_text(message) == "docs/bare/a.md"

    def test_an_exclude_relative_to_under_is_refused(self, corpus: Path) -> None:
        (corpus / "docs" / "journal").mkdir()
        params = {"name": "contents", "arguments": {"exclude": ["journal"]}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "not a folder in the corpus" in _tool_text(message)

    def test_a_key_absent_from_some_documents_is_fine(self, corpus: Path) -> None:
        # docs/loose.md has no frontmatter at all; docs/edge.md has a title.
        params = {"name": "contents", "arguments": {"keys": ["title"]}}
        text = _tool_text(respond(corpus, _request("tools/call", params)))
        assert text == "docs/edge.md\ntitle: Edge\n\ndocs/loose.md"

    def test_a_non_list_exclude_is_refused(self, corpus: Path) -> None:
        params = {"name": "contents", "arguments": {"exclude": "docs/journal"}}
        message = respond(corpus, _request("tools/call", params))
        assert _result(message)["isError"] is True
        assert "'exclude' must be a list of strings" in _tool_text(message)

    def test_keys_and_exclude_compose(self, corpus: Path) -> None:
        (corpus / "docs" / "journal").mkdir()
        (corpus / "docs" / "journal" / "day.md").write_text(
            "---\ntitle: D\n---\n", encoding="utf-8"
        )
        params = {
            "name": "contents",
            "arguments": {"keys": ["title"], "exclude": ["docs/journal"]},
        }
        text = _tool_text(respond(corpus, _request("tools/call", params)))
        assert text == "docs/edge.md\ntitle: Edge\n\ndocs/loose.md"

    def test_an_unknown_tool_is_an_error_result(self, corpus: Path) -> None:
        message = respond(corpus, _request("tools/call", {"name": "nope"}))
        assert _result(message)["isError"] is True
        assert "unknown tool" in _tool_text(message)


class TestProtocolErrors:
    def test_malformed_json_returns_a_parse_error(self, corpus: Path) -> None:
        assert _error_of(respond(corpus, "{not json"))["code"] == -32700

    def test_an_unknown_method_returns_method_not_found(self, corpus: Path) -> None:
        assert _error_of(respond(corpus, _request("resources/list")))["code"] == -32601

    def test_a_json_array_is_an_invalid_request(self, corpus: Path) -> None:
        assert _error_of(respond(corpus, "[1, 2]"))["code"] == -32600


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
        assert serve(corpus, io.StringIO(lines), stdout) == 0

        replies = [json.loads(line) for line in stdout.getvalue().splitlines()]
        assert [reply["id"] for reply in replies] == [1, 2]

    def test_a_leading_byte_order_mark_is_tolerated(self, corpus: Path) -> None:
        stdout = io.StringIO()
        assert serve(corpus, io.StringIO("﻿" + _request("initialize")), stdout) == 0
        assert json.loads(stdout.getvalue())["id"] == 1
