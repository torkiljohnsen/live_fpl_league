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
        mock_content_block.text = response_text
        mock.messages.create.return_value = MagicMock(
            content=[mock_content_block]
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
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"

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
