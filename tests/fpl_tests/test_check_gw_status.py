"""Tests for check_gw_status module."""

import json
from typing import Any
from pathlib import Path

from check_gw_status import (
    check_status,
    count_finished_events,
    count_finished_fixtures,
    load_state,
    save_state,
)


class StubAPI:
    """Stub API returning configurable bootstrap and fixtures data."""

    def __init__(
        self,
        finished_fixture_count: int = 0,
        total_fixture_count: int = 0,
        finished_event_count: int = 0,
        total_event_count: int = 1,
    ):
        # Build fixtures
        self._fixtures = []
        for i in range(finished_fixture_count):
            self._fixtures.append({"id": i + 1, "finished": True})
        for i in range(total_fixture_count - finished_fixture_count):
            self._fixtures.append({"id": finished_fixture_count + i + 1, "finished": False})

        # Build events
        events = []
        for i in range(total_event_count):
            events.append({
                "id": i + 1,
                "finished": i < finished_event_count,
                "is_current": i == finished_event_count,
                "deadline_time": "2025-08-16T10:00:00Z",
            })
        self._bootstrap = {"events": events}

    def get_bootstrap_static(self) -> dict[str, Any]:
        return self._bootstrap

    def get_fixtures(self, event_id: int | None = None) -> list[dict[str, Any]]:
        return self._fixtures

    # Protocol stubs (unused by check_gw_status)
    def get_league_standings(self, league_id: str) -> dict[str, Any]:
        return {}

    def get_team(self, team_id: str) -> dict[str, Any]:
        return {}

    def get_team_history(self, team_id: str) -> dict[str, Any]:
        return {}

    def get_team_picks(self, team_id: str, event_id: str) -> dict[str, Any]:
        return {}

    def get_transfers(self, team_id: str) -> list[dict[str, Any]]:
        return []

    def get_event_live(self, event_id: str) -> dict[str, Any]:
        return {}


class TestStateIO:
    def test_load_missing_file(self, tmp_path: Path) -> None:
        assert load_state(tmp_path / "nope.json") == {}

    def test_roundtrip(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state = {"finished_fixtures": 100, "finished_events": 10}
        save_state(state_path, state)
        assert load_state(state_path) == state


class TestCounters:
    def test_count_finished_fixtures(self) -> None:
        api = StubAPI(finished_fixture_count=50, total_fixture_count=380)
        assert count_finished_fixtures(api) == 50

    def test_count_finished_fixtures_none(self) -> None:
        api = StubAPI(finished_fixture_count=0, total_fixture_count=10)
        assert count_finished_fixtures(api) == 0

    def test_count_finished_events(self) -> None:
        api = StubAPI(finished_event_count=28, total_event_count=38)
        assert count_finished_events(api) == 28

    def test_count_finished_events_none(self) -> None:
        api = StubAPI(finished_event_count=0, total_event_count=38)
        assert count_finished_events(api) == 0


class TestCheckStatus:
    def test_first_run_nothing_finished(self, tmp_path: Path) -> None:
        """First run with no state file and no finished fixtures."""
        api = StubAPI(finished_fixture_count=0, total_fixture_count=10)
        has_new, gw_fin, new_state = check_status(api, tmp_path / "state.json")
        assert has_new is False
        assert gw_fin is False
        assert new_state == {"finished_fixtures": 0, "finished_events": 0}

    def test_first_run_with_finished_fixtures(self, tmp_path: Path) -> None:
        """First run, some fixtures already finished."""
        api = StubAPI(finished_fixture_count=50, total_fixture_count=380,
                      finished_event_count=5, total_event_count=38)
        has_new, gw_fin, _ = check_status(api, tmp_path / "state.json")
        assert has_new is True
        assert gw_fin is True

    def test_no_change(self, tmp_path: Path) -> None:
        """Counts unchanged since last run."""
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 100, "finished_events": 10})
        api = StubAPI(finished_fixture_count=100, total_fixture_count=380,
                      finished_event_count=10, total_event_count=38)
        has_new, gw_fin, _ = check_status(api, state_path)
        assert has_new is False
        assert gw_fin is False

    def test_new_fixture_finished(self, tmp_path: Path) -> None:
        """One more fixture finished since last run."""
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 100, "finished_events": 10})
        api = StubAPI(finished_fixture_count=101, total_fixture_count=380,
                      finished_event_count=10, total_event_count=38)
        has_new, gw_fin, _ = check_status(api, state_path)
        assert has_new is True
        assert gw_fin is False

    def test_gameweek_finished(self, tmp_path: Path) -> None:
        """A new event was marked finished (no new fixtures)."""
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 290, "finished_events": 28})
        api = StubAPI(finished_fixture_count=290, total_fixture_count=380,
                      finished_event_count=29, total_event_count=38)
        has_new, gw_fin, _ = check_status(api, state_path)
        assert has_new is False
        assert gw_fin is True

    def test_both_change(self, tmp_path: Path) -> None:
        """New fixtures AND a new finished event in the same check."""
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 280, "finished_events": 27})
        api = StubAPI(finished_fixture_count=290, total_fixture_count=380,
                      finished_event_count=28, total_event_count=38)
        has_new, gw_fin, new_state = check_status(api, state_path)
        assert has_new is True
        assert gw_fin is True
        assert new_state == {"finished_fixtures": 290, "finished_events": 28}

    def test_no_repeat_after_save(self, tmp_path: Path) -> None:
        """After saving state, same counts should not trigger again."""
        state_path = tmp_path / "state.json"
        api = StubAPI(finished_fixture_count=290, total_fixture_count=380,
                      finished_event_count=29, total_event_count=38)
        # First check — detects changes
        _, _, new_state = check_status(api, state_path)
        # Save the state (simulating what the workflow does)
        save_state(state_path, new_state)
        # Second check — nothing new
        has_new, gw_fin, _ = check_status(api, state_path)
        assert has_new is False
        assert gw_fin is False
