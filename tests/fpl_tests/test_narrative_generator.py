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

    def test_do_not_repeat_included_in_user_message(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            do_not_repeat="## Ikke gjenta (brukt de siste fem rundene)\nNoe unikt her",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Ikke gjenta" in user_msg
        assert "Noe unikt her" in user_msg

    def test_do_not_repeat_absent_when_empty(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            do_not_repeat="",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "Ikke gjenta" not in user_msg

    def test_do_not_repeat_defaults_to_none(self):
        """Omitting do_not_repeat entirely must not raise or add the section."""
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
        assert "Ikke gjenta" not in user_msg

    def test_do_not_repeat_appears_after_previous_narrative(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)

        gen.generate(
            report_json=_sample_report(),
            persona="P",
            narrative_guide="G",
            examples="E",
            memory_context="",
            previous_narrative="FORRIGE_MARKØR",
            do_not_repeat="IKKE_GJENTA_MARKØR",
        )

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert user_msg.index("FORRIGE_MARKØR") < user_msg.index("IKKE_GJENTA_MARKØR")

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
        # GW1 selects more than the word budget allows; what's-new survives.
        assert "2026/27" in call_kwargs["reference_docs"]

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


class TestRunNarrativePipelineDevicePalette:
    """DEVICE_PALETTE.md rides along with the guide in the system prompt."""

    def test_palette_appended_to_narrative_guide(self, tmp_path: Path):
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _GOOD_NARRATIVE
        mock_generator.save_narrative.side_effect = _make_save_narrative(tmp_path)
        mock_generator._client = MagicMock()

        mock_memory = MagicMock()
        mock_memory.get_prompt_context.return_value = ""

        with (
            patch(
                "fpl.narrative_generator.NarrativeGenerator",
                return_value=mock_generator,
            ),
            patch("fpl.narrative_generator.ReidarMemory", return_value=mock_memory),
        ):
            run_narrative_pipeline(_pipeline_report(), "123", 6, str(tmp_path))

        guide = mock_generator.generate.call_args.kwargs["narrative_guide"]
        assert "# Narrative Guide" in guide
        assert "# Device Palette" in guide
        assert 'class="fact-box"' in guide


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


# ---------------------------------------------------------------------------
# run_narrative_pipeline() — do_not_repeat wiring
# ---------------------------------------------------------------------------


class TestRunNarrativePipelineDoNotRepeat:
    def _run(self, tmp_path: Path, mock_generator: MagicMock) -> None:
        from fpl import narrative_generator as ng

        with patch.object(ng, "read_reidar_doc", return_value="DOC"), patch.object(
            ng, "NarrativeGenerator", return_value=mock_generator
        ), patch.object(ng.ReidarMemory, "update_memory"):
            result = {"meta": {"season": "2025-26", "event_id": 5}}
            ng.run_narrative_pipeline(
                result=result,
                league_id="123456",
                event_id=5,
                output_dir=str(tmp_path),
            )

    def _mock_generator(self, tmp_path: Path) -> MagicMock:
        mock_generator = MagicMock()
        mock_generator.generate.return_value = "# Tittel\n\nÅpning."
        mock_generator.save_narrative.return_value = tmp_path / "gw5.md"
        mock_generator._client = MagicMock()
        return mock_generator

    def test_passes_do_not_repeat_kwarg(self, tmp_path: Path):
        mock_generator = self._mock_generator(tmp_path)
        self._run(tmp_path, mock_generator)

        _, kwargs = mock_generator.generate.call_args
        assert "do_not_repeat" in kwargs

    def test_empty_do_not_repeat_when_no_memory(self, tmp_path: Path):
        """With no recent.json yet, the block passed through should be empty."""
        mock_generator = self._mock_generator(tmp_path)
        self._run(tmp_path, mock_generator)

        _, kwargs = mock_generator.generate.call_args
        assert kwargs["do_not_repeat"] == ""

    def test_uses_recorded_recent_entries(self, tmp_path: Path):
        """A prior recent.json entry inside the window shows up in do_not_repeat."""
        from fpl.reidar_memory import ReidarMemory

        memory = ReidarMemory(str(tmp_path), "123456", "2025-26")
        memory.scaffold_directories()
        memory.record_recent(4, "# Forrige overskrift\n\nForrige åpning.\n\nForrige slutt.")

        mock_generator = self._mock_generator(tmp_path)
        self._run(tmp_path, mock_generator)

        _, kwargs = mock_generator.generate.call_args
        assert "Forrige overskrift" in kwargs["do_not_repeat"]


class TestCompactReportForPrompt:
    def test_squad_becomes_strings_and_ids_are_dropped(self):
        from fpl.narrative_generator import compact_report_for_prompt

        report = {
            "standings": [
                {
                    "entry_id": 1,
                    "player_first_name": "Ola",
                    "captain": {"name": "Haaland", "element_id": 5, "points": 4},
                    "vice_captain": {"name": "Saka", "element_id": 6, "points": 9},
                    "bench_players": [{"name": "X"}],
                    "squad": [
                        {"element_id": 5, "name": "Haaland", "club": "Man City",
                         "position": 1, "points": 2, "is_captain": True, "multiplier": 2},
                        {"element_id": 7, "name": "Raya", "club": "Arsenal",
                         "position": 12, "points": 6, "is_captain": False, "multiplier": 0},
                    ],
                }
            ]
        }
        compact = compact_report_for_prompt(report)
        p = compact["standings"][0]
        assert p["squad"] == ["Haaland (Man City) 2 (C)", "Raya (Arsenal) 6 (benk)"]
        assert "bench_players" not in p
        assert "entry_id" not in p
        assert "element_id" not in p["captain"]
        # the original is untouched
        assert report["standings"][0]["squad"][0]["element_id"] == 5

    def test_user_message_uses_compact_view(self):
        client = _mock_client()
        gen = NarrativeGenerator(client=client)
        report = _sample_report()
        report["standings"] = [{
            "player_first_name": "Ola",
            "squad": [{"element_id": 99, "name": "Raya", "club": "Arsenal",
                       "points": 6, "is_captain": False, "multiplier": 1}],
        }]
        gen.generate(report_json=report, persona="P", narrative_guide="G",
                     examples="E", memory_context="")
        user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "Raya (Arsenal) 6" in user_msg
        assert "99" not in user_msg
