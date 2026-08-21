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
    client.beta.messages.create.return_value = response
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

    def test_sends_model_and_fallbacks(self):
        client = _mock_client([_block("text", "x")])

        claude_api.complete(client, system="S", user="U")

        kwargs = client.beta.messages.create.call_args.kwargs
        assert kwargs["model"] == claude_api.MODEL
        assert kwargs["max_tokens"] == claude_api.MAX_TOKENS
        assert kwargs["fallbacks"] == "default"
        assert claude_api.FALLBACK_BETA in kwargs["betas"]

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


class TestFallbackDegradation:
    """The weekly run must survive an account without the fallbacks beta."""

    def _bad_request(self, message: str) -> Exception:
        exc = Exception(message)
        exc.status_code = 400  # type: ignore[attr-defined]
        return exc

    def test_retries_without_fallbacks_on_beta_rejection(self, capsys):
        client = MagicMock()
        client.beta.messages.create.side_effect = self._bad_request(
            "fallbacks: unsupported beta"
        )
        client.messages.create.return_value = MagicMock(
            content=[_block("text", "Rapporten.")], stop_reason="end_turn"
        )

        result = claude_api.complete(client, system="S", user="U")

        assert result == "Rapporten."
        assert "WARNING" in capsys.readouterr().err

    def test_other_errors_propagate(self):
        client = MagicMock()
        client.beta.messages.create.side_effect = RuntimeError("connection reset")

        with pytest.raises(RuntimeError, match="connection reset"):
            claude_api.complete(client, system="S", user="U")

        client.messages.create.assert_not_called()
