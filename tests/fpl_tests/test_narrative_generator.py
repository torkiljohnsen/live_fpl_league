"""Tests for the NarrativeGenerator class."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fpl.narrative_generator import NarrativeGenerator, run_narrative_pipeline


def _mock_client(response_text: str = "Generated narrative") -> MagicMock:
    """Create a mocked anthropic client."""
    mock = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.type = "text"
    mock_content_block.text = response_text
    mock.messages.create.return_value = MagicMock(
        content=[mock_content_block], stop_reason="end_turn"
    )
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

    def test_extra_instructions_appended_to_user_message(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            extra_instructions="Rett disse feilene:\n- for lang",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Rett disse feilene" in user_msg
        assert "for lang" in user_msg

    def test_no_extra_instructions_omits_section(self):
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
        assert "Rett disse feilene" not in user_msg

    def test_reference_docs_included_in_user_message(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            reference_docs="### Some doc\n\nContent here",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "## Oppslagsverk (bare for denne runden)" in user_msg
        assert "### Some doc" in user_msg
        assert "Content here" in user_msg

    def test_no_reference_docs_omits_section(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            reference_docs=None,
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Oppslagsverk" not in user_msg

    def test_empty_reference_docs_omits_section(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            reference_docs="",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Oppslagsverk" not in user_msg

    def test_reference_docs_appear_before_previous_narrative(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            previous_narrative="Previous week text here",
            reference_docs="### Some doc\n\nContent here",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert user_msg.index("Oppslagsverk") < user_msg.index(
            "Previous week text here"
        )

    def test_assignment_included_in_user_message(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            assignment="## Ukens oppdrag\nUkens form: Spalten — testbeskrivelse.",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "## Ukens oppdrag" in user_msg
        assert "Spalten" in user_msg

    def test_no_assignment_omits_section(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            assignment=None,
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Ukens oppdrag" not in user_msg

    def test_assignment_appears_before_reference_docs(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            assignment="## Ukens oppdrag\nUkens form: Spalten.",
            reference_docs="### Some doc\n\nContent here",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert user_msg.index("Ukens oppdrag") < user_msg.index("Oppslagsverk")

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
        assert call_kwargs.kwargs["model"] == "claude-sonnet-5"

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


class TestRunNarrativePipelineReferenceDocs:
    def test_reference_docs_loaded_and_passed_to_generate(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ):
        # GW1 -> select_reference_docs triggers real reference files.
        report = {
            "meta": {
                "event_id": 1,
                "league_id": "123456",
                "season": "2025-26",
                "previous_narrative": None,
            },
            "standings": [],
            "awards": {},
            "league_summary": {},
        }

        mock_generator = MagicMock()
        mock_generator.generate.return_value = "Narrative text"
        mock_generator.save_narrative.return_value = tmp_path / "gw1.md"
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch(
                "fpl.narrative_generator.ReidarMemory", return_value=mock_memory
            ),
        ):
            run_narrative_pipeline(report, "123456", 1, str(tmp_path))

        call_kwargs = mock_generator.generate.call_args.kwargs
        assert call_kwargs["reference_docs"]
        assert "FPL rules 2026/27" in call_kwargs["reference_docs"]

        captured = capsys.readouterr()
        assert "Reference docs:" in captured.out
        assert "fpl_rules_2026-27.md" in captured.out

    def test_quiet_gameweek_passes_empty_reference_docs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ):
        report = {
            "meta": {
                "event_id": 7,
                "league_id": "123456",
                "season": "2025-26",
                "previous_narrative": None,
                "next_event": {
                    "id": 8,
                    "deadline_time": "2026-10-30T17:30:00Z",  # a Friday
                    "is_golden": False,
                },
            },
            "standings": [
                {
                    "player_first_name": "Ola",
                    "league_rank": 1,
                    "total_points": 50,
                    "chip_played": None,
                    "captain": {"name": "Haaland", "did_not_play": False},
                },
                {
                    "player_first_name": "Kari",
                    "league_rank": 2,
                    "total_points": 45,
                    "chip_played": None,
                    "captain": {"name": "Salah", "did_not_play": False},
                },
            ],
            "awards": {},
            "league_summary": {},
        }

        mock_generator = MagicMock()
        mock_generator.generate.return_value = "Narrative text"
        mock_generator.save_narrative.return_value = tmp_path / "gw7.md"
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch(
                "fpl.narrative_generator.ReidarMemory", return_value=mock_memory
            ),
        ):
            run_narrative_pipeline(report, "123456", 7, str(tmp_path))

        call_kwargs = mock_generator.generate.call_args.kwargs
        assert call_kwargs["reference_docs"] == ""

        captured = capsys.readouterr()
        assert "Reference docs: none (0 words)" in captured.out


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


# ---------------------------------------------------------------------------
# run_narrative_pipeline() — style lint gate (issue #40, workstream E)
# ---------------------------------------------------------------------------


def _pipeline_report(event_id: int = 6) -> dict:
    return {
        "meta": {"event_id": event_id, "league_id": "123", "season": "2025-26"},
        "standings": [{"player_first_name": "Ola", "event_total": 70}],
        "awards": {},
        "league_summary": {},
    }


# A narrative that trips several hard failures: three-fragment staccato
# headline, and the "Vi sees" sign-off.
_BAD_NARRATIVE = (
    "# Chip-karneval. Ny leder. Anders krasjlander.\n\n"
    "![Reidars Rapport](../../reidars_rapport_1.png)\n\n"
    "En helt vanlig runde uten noe spesielt å melde her i det hele tatt.\n\n"
    "Vi sees."
)

_GOOD_NARRATIVE = (
    "# En helt vanlig overskrift for runden\n\n"
    "![Reidars Rapport](../../reidars_rapport_1.png)\n\n"
    "En helt vanlig runde uten noe spesielt å melde her i det hele tatt.\n\n"
    "Ha det bra til neste gang."
)


def _make_save_narrative(tmp_path: Path):
    def _save(content, output_dir, league_id, season, event_id):  # type: ignore[no-untyped-def]
        p = (
            Path(output_dir)
            / "docs"
            / "narratives"
            / season
            / league_id
            / f"gw{event_id}.md"
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    return _save


class TestRunNarrativePipelineStyleLintGate:
    def test_regenerates_exactly_once_on_failing_first_draft(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.side_effect = [_BAD_NARRATIVE, _GOOD_NARRATIVE]
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch("fpl.narrative_generator.read_reidar_doc", return_value="doc"),
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            path = run_narrative_pipeline(
                _pipeline_report(), "123", 6, str(tmp_path)
            )

        assert mock_generator.generate.call_count == 2
        second_call_kwargs = mock_generator.generate.call_args_list[1].kwargs
        assert second_call_kwargs.get("extra_instructions")
        assert Path(path).read_text(encoding="utf-8") == _GOOD_NARRATIVE

    def test_does_not_regenerate_on_clean_first_draft(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.side_effect = [_GOOD_NARRATIVE]
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch("fpl.narrative_generator.read_reidar_doc", return_value="doc"),
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            path = run_narrative_pipeline(
                _pipeline_report(), "123", 6, str(tmp_path)
            )

        assert mock_generator.generate.call_count == 1
        assert Path(path).read_text(encoding="utf-8") == _GOOD_NARRATIVE

    def test_memory_update_uses_final_narrative(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.side_effect = [_BAD_NARRATIVE, _GOOD_NARRATIVE]
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch("fpl.narrative_generator.read_reidar_doc", return_value="doc"),
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            run_narrative_pipeline(_pipeline_report(), "123", 6, str(tmp_path))

        mock_memory.update_memory.assert_called_once()
        call_kwargs = mock_memory.update_memory.call_args.kwargs
        assert call_kwargs["narrative"] == _GOOD_NARRATIVE


# ---------------------------------------------------------------------------
# run_narrative_pipeline() — format scheduler wiring (issue #40, workstream A/B)
# ---------------------------------------------------------------------------


class TestRunNarrativePipelineFormatScheduler:
    def test_assignment_text_passed_to_generate(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _GOOD_NARRATIVE
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch("fpl.narrative_generator.read_reidar_doc", return_value="doc"),
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            run_narrative_pipeline(_pipeline_report(), "123", 6, str(tmp_path))

        call_kwargs = mock_generator.generate.call_args.kwargs
        assert "## Ukens oppdrag" in call_kwargs["assignment"]
        assert "Kalender:" in call_kwargs["assignment"]

    def test_shapes_json_written_after_successful_run(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _GOOD_NARRATIVE
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch("fpl.narrative_generator.read_reidar_doc", return_value="doc"),
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            run_narrative_pipeline(_pipeline_report(), "123", 6, str(tmp_path))

        shapes_path = (
            tmp_path / "weekly_report" / "reidar_memory" / "123" / "2025-26" / "shapes.json"
        )
        assert shapes_path.is_file()
        data = json.loads(shapes_path.read_text(encoding="utf-8"))
        assert data == [{"event_id": 6, "shape": data[0]["shape"], "constraint": data[0]["constraint"]}]

    def test_set_piece_gw1_forces_season_preview_shape(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _GOOD_NARRATIVE
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch("fpl.narrative_generator.read_reidar_doc", return_value="doc"),
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            run_narrative_pipeline(_pipeline_report(event_id=1), "123", 1, str(tmp_path))

        call_kwargs = mock_generator.generate.call_args.kwargs
        assert "Sesongforhåndsomtalen" in call_kwargs["assignment"]
