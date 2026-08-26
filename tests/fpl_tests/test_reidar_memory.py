"""Tests for the ReidarMemory persistent knowledge system."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from fpl.reidar_memory import ReidarMemory


def _make_memory(tmp_path: Path) -> ReidarMemory:
    """Create a ReidarMemory instance pointing at tmp_path."""
    return ReidarMemory(str(tmp_path), "123456", "2025-26")


def _base_path(tmp_path: Path) -> Path:
    return tmp_path / "weekly_report" / "reidar_memory" / "123456" / "2025-26"


def _sample_report() -> dict:
    """Minimal report dict for update_memory tests."""
    return {
        "meta": {"event_id": 5, "league_id": "123456", "season": "2025-26"},
        "standings": [
            {"player_first_name": "Ola", "league_rank": 1, "event_total": 70},
            {"player_first_name": "Kari", "league_rank": 2, "event_total": 55},
        ],
        "awards": {},
        "league_summary": {"average_score": 62.5},
    }


# ---------------------------------------------------------------------------
# scaffold_directories
# ---------------------------------------------------------------------------


class TestScaffoldDirectories:
    def test_creates_directory_structure(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        assert (base / "managers").is_dir()
        assert (base / "gameweeks").is_dir()

    def test_idempotent(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        mem.scaffold_directories()  # should not error

        base = _base_path(tmp_path)
        assert (base / "managers").is_dir()


# ---------------------------------------------------------------------------
# load_manager_profiles
# ---------------------------------------------------------------------------


class TestLoadManagerProfiles:
    def test_missing_directory_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        # No directories exist yet
        assert mem.load_manager_profiles() == {}

    def test_empty_directory_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        assert mem.load_manager_profiles() == {}

    def test_reads_all_profiles(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "managers" / "Ola.md").write_text("Ola profile", encoding="utf-8")
        (base / "managers" / "Kari.md").write_text("Kari profile", encoding="utf-8")

        profiles = mem.load_manager_profiles()
        assert profiles == {"Kari": "Kari profile", "Ola": "Ola profile"}

    def test_ignores_non_md_files(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "managers" / "Ola.md").write_text("profile", encoding="utf-8")
        (base / "managers" / "notes.txt").write_text("not a profile", encoding="utf-8")

        profiles = mem.load_manager_profiles()
        assert list(profiles.keys()) == ["Ola"]


# ---------------------------------------------------------------------------
# load_season_arc
# ---------------------------------------------------------------------------


class TestLoadSeasonArc:
    def test_missing_file_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.load_season_arc() == ""

    def test_reads_existing_file(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "season_arc.md").write_text("Season arc content", encoding="utf-8")

        assert mem.load_season_arc() == "Season arc content"


# ---------------------------------------------------------------------------
# load_recent_gameweeks
# ---------------------------------------------------------------------------


class TestLoadRecentGameweeks:
    def test_missing_directory_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.load_recent_gameweeks(5) == []

    def test_no_prior_gameweeks_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        assert mem.load_recent_gameweeks(5) == []

    def test_reads_previous_gw_summaries(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "gameweeks" / "gw3.md").write_text("GW3 recap", encoding="utf-8")
        (base / "gameweeks" / "gw4.md").write_text("GW4 recap", encoding="utf-8")

        result = mem.load_recent_gameweeks(5)
        assert result == ["GW3 recap", "GW4 recap"]

    def test_window_limits_results(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        for gw in range(1, 10):
            (base / "gameweeks" / f"gw{gw}.md").write_text(
                f"GW{gw}", encoding="utf-8"
            )

        # current_event=10, window=3 -> should read gw7, gw8, gw9
        result = mem.load_recent_gameweeks(10, window=3)
        assert result == ["GW7", "GW8", "GW9"]

    def test_does_not_include_current_event(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "gameweeks" / "gw5.md").write_text("GW5", encoding="utf-8")

        # current_event=5 should NOT include gw5
        result = mem.load_recent_gameweeks(5)
        assert result == []

    def test_gw1_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        assert mem.load_recent_gameweeks(1) == []


# ---------------------------------------------------------------------------
# get_prompt_context
# ---------------------------------------------------------------------------


class TestGetPromptContext:
    def test_first_run_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.get_prompt_context(1) == ""

    def test_assembles_all_memory(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "managers" / "Ola.md").write_text("Ola profile", encoding="utf-8")
        (base / "season_arc.md").write_text("Season arc", encoding="utf-8")
        (base / "gameweeks" / "gw3.md").write_text("GW3 recap", encoding="utf-8")

        context = mem.get_prompt_context(4)

        assert "Reidars minne" in context
        assert "Managerprofiler" in context
        assert "Ola" in context
        assert "Ola profile" in context
        assert "Sesongbue" in context
        assert "Season arc" in context
        assert "Tidligere runder" in context
        assert "GW3 recap" in context

    def test_only_profiles_present(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "managers" / "Kari.md").write_text("Kari data", encoding="utf-8")

        context = mem.get_prompt_context(1)
        assert "Managerprofiler" in context
        assert "Kari data" in context
        assert "Sesongbue" not in context
        assert "Tidligere runder" not in context


# ---------------------------------------------------------------------------
# update_memory (mocked LLM)
# ---------------------------------------------------------------------------


class TestUpdateMemory:
    def _mock_client(self, response_text: str) -> MagicMock:
        """Create a mocked anthropic client returning the given text."""
        mock = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.type = "text"
        mock_content_block.text = response_text
        mock.messages.create.return_value = MagicMock(
            content=[mock_content_block], stop_reason="end_turn"
        )
        return mock

    def test_writes_manager_profiles(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nOla er en dristig manager.\n===END===\n"
            "===MANAGER: Kari===\nKari holder seg stabil.\n===END===\n"
            "===GW_SUMMARY===\nEn spennende runde.\n===END===\n"
            "===SEASON_ARC===\nTett i toppen.\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative text", client)

        base = _base_path(tmp_path)
        assert (base / "managers" / "Ola.md").read_text(encoding="utf-8") == "Ola er en dristig manager."
        assert (base / "managers" / "Kari.md").read_text(encoding="utf-8") == "Kari holder seg stabil."

    def test_writes_gw_summary(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nProfile\n===END===\n"
            "===GW_SUMMARY===\nRunde 5 var dramatisk.\n===END===\n"
            "===SEASON_ARC===\nArc\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        base = _base_path(tmp_path)
        gw_path = base / "gameweeks" / "gw5.md"
        assert gw_path.is_file()
        assert "Runde 5 var dramatisk" in gw_path.read_text(encoding="utf-8")

    def test_writes_season_arc(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nProfile\n===END===\n"
            "===GW_SUMMARY===\nSummary\n===END===\n"
            "===SEASON_ARC===\nTittelkampen er helt åpen.\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        base = _base_path(tmp_path)
        arc = (base / "season_arc.md").read_text(encoding="utf-8")
        assert "Tittelkampen er helt åpen" in arc

    def test_calls_llm_with_correct_model(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nP\n===END===\n"
            "===GW_SUMMARY===\nS\n===END===\n"
            "===SEASON_ARC===\nA\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        call_kwargs = client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-5"

    def test_first_run_bootstrap(self, tmp_path: Path):
        """On first run (no profiles), prompt should include bootstrap note."""
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nNew profile\n===END===\n"
            "===MANAGER: Kari===\nNew profile\n===END===\n"
            "===GW_SUMMARY===\nFirst GW\n===END===\n"
            "===SEASON_ARC===\nNew season\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        call_kwargs = client.messages.create.call_args
        system_prompt = call_kwargs.kwargs["system"]
        assert "FØRSTE runde" in system_prompt

    def test_existing_profiles_no_bootstrap_note(self, tmp_path: Path):
        """With existing profiles, prompt should NOT include bootstrap note."""
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        base = _base_path(tmp_path)
        (base / "managers" / "Ola.md").write_text("Old profile", encoding="utf-8")

        response = (
            "===MANAGER: Ola===\nUpdated\n===END===\n"
            "===GW_SUMMARY===\nSummary\n===END===\n"
            "===SEASON_ARC===\nArc\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        call_kwargs = client.messages.create.call_args
        system_prompt = call_kwargs.kwargs["system"]
        assert "FØRSTE runde" not in system_prompt

    def test_user_message_includes_report_and_narrative(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nP\n===END===\n"
            "===GW_SUMMARY===\nS\n===END===\n"
            "===SEASON_ARC===\nA\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "My narrative text", client)

        call_kwargs = client.messages.create.call_args
        user_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "My narrative text" in user_msg
        assert "Ola" in user_msg  # from standings

    def test_writes_ledger_and_threads(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nP\n===END===\n"
            "===GW_SUMMARY===\nS\n===END===\n"
            "===SEASON_ARC===\nA\n===END===\n"
            "===LEDGER===\n"
            "- GW5 | Ola vinner ligaen | avgjøres: GW38 | status: åpen\n"
            "===END===\n"
            "===THREADS===\n"
            "- Kari-feiden | Kari og Ola krangler om chips | sist brukt: GW5\n"
            "===END===\n"
            "===JOKES===\n"
            "- Ola som en gammel traktor\n"
            "- \"Templaten slår tilbake\"\n"
            "===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        base = _base_path(tmp_path)
        ledger = (base / "ledger.md").read_text(encoding="utf-8")
        assert "Ola vinner ligaen" in ledger
        threads = (base / "threads.md").read_text(encoding="utf-8")
        assert "Kari-feiden" in threads

    def test_missing_ledger_section_does_not_break_others(self, tmp_path: Path):
        """A malformed/missing LEDGER section must not stop THREADS/other writes."""
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nP\n===END===\n"
            "===GW_SUMMARY===\nS\n===END===\n"
            "===SEASON_ARC===\nA\n===END===\n"
            "===THREADS===\n- En tråd | tekst | sist brukt: GW5\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "Narrative", client)

        base = _base_path(tmp_path)
        assert not (base / "ledger.md").is_file()
        assert (base / "threads.md").is_file()
        assert (base / "managers" / "Ola.md").is_file()

    def test_jokes_returned_and_fed_to_record_recent(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nP\n===END===\n"
            "===GW_SUMMARY===\nS\n===END===\n"
            "===SEASON_ARC===\nA\n===END===\n"
            "===JOKES===\n- vits en\n- vits to\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(_sample_report(), "# Tittel\n\nÅpning her.", client)

        recent = mem.load_recent()
        assert len(recent) == 1
        assert recent[0]["jokes"] == ["vits en", "vits to"]

    def test_update_memory_calls_record_recent(self, tmp_path: Path):
        """update_memory must append a recent.json entry (code-side, no LLM)."""
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        response = (
            "===MANAGER: Ola===\nP\n===END===\n"
            "===GW_SUMMARY===\nS\n===END===\n"
            "===SEASON_ARC===\nA\n===END===\n"
        )
        client = self._mock_client(response)

        mem.update_memory(
            _sample_report(), "# En overskrift\n\nÅpningssetning her. Mer tekst.", client
        )

        recent = mem.load_recent()
        assert len(recent) == 1
        assert recent[0]["event_id"] == 5
        assert recent[0]["headline"] == "En overskrift"
        assert recent[0]["opener"] == "Åpningssetning her."


# ---------------------------------------------------------------------------
# load_ledger / load_threads
# ---------------------------------------------------------------------------


class TestLoadLedgerAndThreads:
    def test_missing_ledger_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.load_ledger() == ""

    def test_reads_existing_ledger(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        base = _base_path(tmp_path)
        (base / "ledger.md").write_text("- GW1 | spådom | avgjøres: GW2 | status: åpen", encoding="utf-8")
        assert "spådom" in mem.load_ledger()

    def test_missing_threads_returns_empty(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.load_threads() == ""

    def test_reads_existing_threads(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        base = _base_path(tmp_path)
        (base / "threads.md").write_text("- Tråd | tekst | sist brukt: GW1", encoding="utf-8")
        assert "Tråd" in mem.load_threads()


# ---------------------------------------------------------------------------
# record_recent / load_recent
# ---------------------------------------------------------------------------


class TestRecordAndLoadRecent:
    def test_missing_file_returns_empty_list(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.load_recent() == []

    def test_malformed_json_returns_empty_list(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        base = _base_path(tmp_path)
        (base / "recent.json").write_text("not json{{", encoding="utf-8")
        assert mem.load_recent() == []

    def test_record_recent_round_trip(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        narrative = (
            "# Store greier i denne runden\n\n"
            "![Reidars Rapport](../img.png)\n\n"
            "Dette er åpningssetningen. Og en til.\n\n"
            "Midtparagraf med detaljer.\n\n"
            "Dette er den siste setningen i kolonnen."
        )
        mem.record_recent(7, narrative, jokes=["vits a", "vits b"])

        recent = mem.load_recent()
        assert len(recent) == 1
        entry = recent[0]
        assert entry["event_id"] == 7
        assert entry["headline"] == "Store greier i denne runden"
        assert entry["opener"] == "Dette er åpningssetningen."
        assert entry["closer"] == "Dette er den siste setningen i kolonnen."
        assert entry["jokes"] == ["vits a", "vits b"]

    def test_strips_front_matter_and_image_line(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        narrative = (
            "---\n"
            "teaser: Noe skjer\n"
            "mentions: Ola\n"
            "---\n"
            "# Overskrift\n\n"
            "![bilde](x.png)\n\n"
            "Den ekte åpningen kommer her. Resten følger.\n\n"
            "Sluttlinje."
        )
        mem.record_recent(1, narrative)

        entry = mem.load_recent()[0]
        assert entry["headline"] == "Overskrift"
        assert entry["opener"] == "Den ekte åpningen kommer her."
        assert entry["closer"] == "Sluttlinje."

    def test_closer_capped_at_40_words(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        long_closer = " ".join(f"ord{i}" for i in range(60))
        narrative = f"# Tittel\n\nÅpning.\n\n{long_closer}"
        mem.record_recent(1, narrative)

        entry = mem.load_recent()[0]
        assert len(entry["closer"].rstrip("…").split()) == 40

    def test_keeps_only_last_8_entries(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()

        for gw in range(1, 11):
            mem.record_recent(gw, f"# GW{gw}\n\nÅpning {gw}.\n\nSlutt {gw}.")

        recent = mem.load_recent()
        assert len(recent) == 8
        assert [e["event_id"] for e in recent] == list(range(3, 11))

    def test_no_jokes_defaults_to_empty_list(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        mem.record_recent(1, "# T\n\nÅpning.\n\nSlutt.")
        assert mem.load_recent()[0]["jokes"] == []


# ---------------------------------------------------------------------------
# get_prompt_context — ledger/threads sections
# ---------------------------------------------------------------------------


class TestGetPromptContextLedgerThreads:
    def test_includes_ledger_and_threads_when_present(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        base = _base_path(tmp_path)
        (base / "ledger.md").write_text(
            "- GW1 | Ola vinner alt | avgjøres: GW38 | status: åpen", encoding="utf-8"
        )
        (base / "threads.md").write_text(
            "- Kari-feiden | krangler om chips | sist brukt: GW1", encoding="utf-8"
        )

        context = mem.get_prompt_context(2)

        assert "Spådomsprotokoll" in context
        assert "Ola vinner alt" in context
        assert "Åpne tråder" in context
        assert "Kari-feiden" in context

    def test_absent_when_no_ledger_or_threads(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        context = mem.get_prompt_context(2)
        assert context == ""

    def test_ledger_truncated_to_20_lines(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        base = _base_path(tmp_path)
        lines = "\n".join(f"- GW{i} | pred {i} | avgjøres: GW38 | status: åpen" for i in range(1, 31))
        (base / "ledger.md").write_text(lines, encoding="utf-8")

        context = mem.get_prompt_context(31)

        assert "pred 1 |" not in context
        assert "pred 30" in context

    def test_threads_truncated_to_10_lines(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        base = _base_path(tmp_path)
        lines = "\n".join(f"- Thread{i} | tekst | sist brukt: GW1" for i in range(1, 16))
        (base / "threads.md").write_text(lines, encoding="utf-8")

        context = mem.get_prompt_context(2)

        assert "Thread1 |" not in context
        assert "Thread15" in context


# ---------------------------------------------------------------------------
# get_do_not_repeat_block
# ---------------------------------------------------------------------------


class TestGetDoNotRepeatBlock:
    def test_empty_when_no_recent(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        assert mem.get_do_not_repeat_block(5) == ""

    def test_builds_block_from_recent(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        mem.record_recent(
            3,
            "# En overskrift\n\nEn åpningssetning. Mer tekst.\n\nEn sluttsetning.",
            jokes=["en vits"],
        )

        block = mem.get_do_not_repeat_block(5)

        assert "Ikke gjenta" in block
        assert "En overskrift" in block
        assert "En åpningssetning." in block
        assert "En sluttsetning." in block
        assert "en vits" in block
        assert "Disse er brukt opp" in block

    def test_excludes_entries_outside_window(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        mem.record_recent(1, "# Gammel sak\n\nGammel åpning.\n\nGammel slutt.")

        # current_event=10, window=5 -> gw1 is outside [5, 9]
        block = mem.get_do_not_repeat_block(10, window=5)
        assert block == ""

    def test_excludes_current_event(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        mem.record_recent(5, "# Denne uken\n\nÅpning.\n\nSlutt.")

        block = mem.get_do_not_repeat_block(5)
        assert block == ""

    def test_word_cap_respected(self, tmp_path: Path):
        mem = _make_memory(tmp_path)
        mem.scaffold_directories()
        long_jokes = [f"vits nummer {i} med noen flere ord her for lengde" for i in range(30)]
        mem.record_recent(4, "# Tittel\n\nÅpning.\n\nSlutt.", jokes=long_jokes)

        block = mem.get_do_not_repeat_block(5)
        assert len(block.split()) <= 200
