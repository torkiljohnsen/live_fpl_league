"""Tests for fpl/claude_api.py."""

from unittest.mock import MagicMock

import pytest

from fpl import claude_api


def _block(block_type: str, text: str = "") -> MagicMock:
    block = MagicMock()
    block.type = block_type
    block.text = text
    return block


def _mock_client(
    content: list, stop_reason: str = "end_turn", category: str | None = None
) -> MagicMock:
    client = MagicMock()
    response = MagicMock(content=content, stop_reason=stop_reason)
    response.stop_details = MagicMock(category=category) if category else None
    client.messages.create.return_value = response
    return client


class TestComplete:
    def test_returns_text_block(self):
        client = _mock_client([_block("text", "Reidar skriver.")])

        result = claude_api.complete(client, system="S", user="U")

        assert result == "Reidar skriver."

    def test_skips_thinking_blocks(self):
        """Thinking is on by default, so text is not always the first block."""
        client = _mock_client([_block("thinking"), _block("text", "Rapporten.")])

        result = claude_api.complete(client, system="S", user="U")

        assert result == "Rapporten."

    def test_sends_model_and_token_ceiling(self):
        client = _mock_client([_block("text", "x")])

        claude_api.complete(client, system="S", user="U")

        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["model"] == claude_api.MODEL
        assert kwargs["max_tokens"] == claude_api.MAX_TOKENS

    def test_refusal_raises(self):
        client = _mock_client(
            [_block("text", "")], stop_reason="refusal", category="cyber"
        )

        with pytest.raises(RuntimeError, match="refused"):
            claude_api.complete(client, system="S", user="U")

    def test_truncated_response_raises(self):
        """A truncated response would write half a memory file — fail loudly."""
        client = _mock_client([_block("text", "halv")], stop_reason="max_tokens")

        with pytest.raises(RuntimeError, match="truncated"):
            claude_api.complete(client, system="S", user="U")

