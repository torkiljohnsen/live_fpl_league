"""Tests for the NarrativeGenerator class."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fpl.narrative_generator import NarrativeGenerator


def _mock_client(response_text: str = "Generated narrative") -> MagicMock:
    """Create a mocked anthropic client."""
    mock = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = response_text
    mock.messages.create.return_value = MagicMock(content=[mock_content_block])
    return mock


def _sample_report() -> dict:
    return {
        "meta": {"event_id": 5, "league_id": "123456", "season": "2025-26"},
        "standings": [
            {"player_first_name": "Ola", "event_total": 70},
        ],
        "awards": {"highest_scorer": {"player_first_name": "Ola"}},
        "league_summary": {"average_score": 55},
    }


# ---------------------------------------------------------------------------
# Constructor / API key handling
# ---------------------------------------------------------------------------


class TestNarrativeGeneratorInit:
    def test_accepts_provided_client(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)
        assert gen._client is client

    def test_missing_api_key_raises_runtime_error(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ANTHROPIC_API_KEY is not set
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                NarrativeGenerator()

    def test_error_message_is_helpful(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(RuntimeError, match="environment variable"):
                NarrativeGenerator()


# ---------------------------------------------------------------------------
# generate() — prompt assembly
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_system_prompt_includes_all_sections(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="PERSONA TEXT",
            narrative_guide="GUIDE TEXT",
            examples="EXAMPLE TEXT",
            memory_context="MEMORY TEXT",
        )

        call_kwargs = client.messages.create.call_args
        system = call_kwargs.kwargs["system"]
        assert "PERSONA TEXT" in system
        assert "GUIDE TEXT" in system
        assert "EXAMPLE TEXT" in system
        assert "MEMORY TEXT" in system

    def test_system_prompt_sections_separated_by_divider(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="M",
        )

        call_kwargs = client.messages.create.call_args
        system = call_kwargs.kwargs["system"]
        assert "---" in system

    def test_empty_memory_excluded_from_system_prompt(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="PERSONA",
            narrative_guide="GUIDE",
            examples="EXAMPLES",
            memory_context="",
        )

        call_kwargs = client.messages.create.call_args
        system = call_kwargs.kwargs["system"]
        # With empty memory_context, only 3 sections joined by ---
        assert system.count("---") == 2

    def test_user_message_includes_report_json(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Ola" in user_msg
        assert "json" in user_msg

    def test_previous_narrative_included_in_user_message(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            previous_narrative="Previous week text here",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Previous week text here" in user_msg

    def test_no_previous_narrative_omits_section(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            previous_narrative=None,
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "forrige ukes" not in user_msg

    def test_uses_correct_model(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
        )

        call_kwargs = client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"

    def test_returns_generated_text(self):
        client = _mock_client("Reidars Rapport for runde 5")
        gen = NarrativeGenerator(client=client)

        result = gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
        )

        assert result == "Reidars Rapport for runde 5"


# ---------------------------------------------------------------------------
# save_narrative()
# ---------------------------------------------------------------------------


class TestSaveNarrative:
    def test_creates_correct_path(self, tmp_path: Path):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        path = gen.save_narrative(
            content="# Reidars Rapport",
            output_dir=str(tmp_path),
            league_id="123456",
            season="2025-26",
            event_id=5,
        )

        expected = tmp_path / "docs" / "narratives" / "2025-26" / "123456" / "gw5.md"
        assert path == expected
        assert path.is_file()

    def test_file_content_matches(self, tmp_path: Path):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        narrative = "# Reidars Rapport\n\nEn spennende runde."
        path = gen.save_narrative(
            content=narrative,
            output_dir=str(tmp_path),
            league_id="123456",
            season="2025-26",
            event_id=10,
        )

        assert path.read_text(encoding="utf-8") == narrative

    def test_creates_directories(self, tmp_path: Path):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.save_narrative(
            content="text",
            output_dir=str(tmp_path),
            league_id="999",
            season="2024-25",
            event_id=1,
        )

        assert (tmp_path / "docs" / "narratives" / "2024-25" / "999").is_dir()

    def test_overwrites_existing_file(self, tmp_path: Path):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.save_narrative("first", str(tmp_path), "123", "2025-26", 1)
        path = gen.save_narrative("second", str(tmp_path), "123", "2025-26", 1)

        assert path.read_text(encoding="utf-8") == "second"
