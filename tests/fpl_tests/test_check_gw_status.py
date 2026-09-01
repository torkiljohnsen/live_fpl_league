"""Tests for check_gw_status module."""

from pathlib import Path
from typing import Any

from check_gw_status import (
    check_status,
    count_finished_events,
    count_finished_fixtures,
    latest_finished_event,
    load_state,
    mark_notified,
    pending_notification,
    save_counts,
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
                "data_checked": i < finished_event_count,
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

    def test_count_finished_fixtures_counts_provisional(self) -> None:
        """From 2026/27 a played fixture stays `finished: false` until the
        gameweek locks at 09:00 UK the day after its final match. Dashboards
        must refresh on match day, so provisional fixtures count too."""

        class ProvisionalAPI(StubAPI):
            def get_fixtures(self, event_id: int | None = None) -> list[dict[str, Any]]:
                return [
                    {"id": 1, "finished": False, "finished_provisional": True},
                    {"id": 2, "finished": False, "finished_provisional": False},
                    {"id": 3, "finished": True, "finished_provisional": True},
                ]

        assert count_finished_fixtures(ProvisionalAPI()) == 2

    def test_count_finished_events_requires_the_lock(self) -> None:
        """A gameweek only counts once FPL has locked it.

        Scores lock at 09:00 UK the day after the gameweek's final match,
        tracked by data_checked. An event marked finished but not yet
        checked can still have its BPS and Defensive Contribution points
        amended, so the report must not be built from it.
        """

        class UnlockedAPI(StubAPI):
            def get_bootstrap_static(self) -> dict[str, Any]:
                return {"events": [
                    {"id": 1, "finished": True, "data_checked": True},
                    {"id": 2, "finished": True, "data_checked": False},
                    {"id": 3, "finished": False, "data_checked": False},
                ]}

        assert count_finished_events(UnlockedAPI()) == 1

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


class TestHasFinishedGameweek:
    """The absolute signal manual dispatch uses to skip pre-season reports."""

    def test_false_before_the_first_gameweek_is_scored(self, tmp_path: Path) -> None:
        api = StubAPI(finished_fixture_count=3, total_fixture_count=380,
                      finished_event_count=0, total_event_count=38)
        _, _, new_state = check_status(api, tmp_path / "state.json")
        assert new_state["finished_events"] == 0

    def test_true_once_a_gameweek_has_finished(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 10, "finished_events": 1})
        api = StubAPI(finished_fixture_count=10, total_fixture_count=380,
                      finished_event_count=1, total_event_count=38)
        has_new, gw_fin, new_state = check_status(api, state_path)
        # Nothing new since last run, but a gameweek exists to report on
        assert has_new is False
        assert gw_fin is False
        assert new_state["finished_events"] == 1


class TestLatestFinishedEvent:
    """latest_finished_event() reports which gameweek is locked, not how many."""

    def test_returns_highest_locked_event(self):
        api = StubAPI(finished_event_count=3, total_event_count=38)
        assert latest_finished_event(api) == 3

    def test_returns_none_before_any_gameweek_locks(self):
        api = StubAPI(finished_event_count=0, total_event_count=38)
        assert latest_finished_event(api) is None


def _write_narrative(root: Path, season: str, league_id: str, gw: int) -> None:
    path = root / "docs" / "narratives" / season / league_id / f"gw{gw}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Reidar\n", encoding="utf-8")


class TestPendingNotification:
    """The Teams card is gated on a narrative existing but not yet announced."""

    SEASON = "2025-26"
    LEAGUE = "848662"

    def test_pending_when_narrative_exists_and_is_unannounced(self, tmp_path):
        api = StubAPI(finished_event_count=2, total_event_count=38)
        _write_narrative(tmp_path, self.SEASON, self.LEAGUE, 2)

        event_id, season = pending_notification(
            api, tmp_path / "state.json", self.LEAGUE, str(tmp_path)
        )

        assert event_id == 2
        assert season == self.SEASON

    def test_not_pending_once_marked_notified(self, tmp_path):
        api = StubAPI(finished_event_count=2, total_event_count=38)
        _write_narrative(tmp_path, self.SEASON, self.LEAGUE, 2)
        state_path = tmp_path / "state.json"
        save_state(state_path, {"notified_events": [1, 2]})

        assert pending_notification(
            api, state_path, self.LEAGUE, str(tmp_path)
        ) == (None, "")

    def test_not_pending_while_the_narrative_is_still_being_written(self, tmp_path):
        """The gameweek is locked but generate_narrative.py has not run yet."""
        api = StubAPI(finished_event_count=2, total_event_count=38)

        assert pending_notification(
            api, tmp_path / "state.json", self.LEAGUE, str(tmp_path)
        ) == (None, "")

    def test_not_pending_before_any_gameweek_locks(self, tmp_path):
        api = StubAPI(finished_event_count=0, total_event_count=38)

        assert pending_notification(
            api, tmp_path / "state.json", self.LEAGUE, str(tmp_path)
        ) == (None, "")

    def test_a_new_gameweek_is_pending_even_though_earlier_ones_were_sent(self, tmp_path):
        api = StubAPI(finished_event_count=3, total_event_count=38)
        _write_narrative(tmp_path, self.SEASON, self.LEAGUE, 3)
        state_path = tmp_path / "state.json"
        save_state(state_path, {"notified_events": [1, 2]})

        event_id, _ = pending_notification(
            api, state_path, self.LEAGUE, str(tmp_path)
        )

        assert event_id == 3


class TestMarkNotified:
    """Marking is what stops the next hourly run from sending a duplicate."""

    def test_records_the_gameweek(self, tmp_path):
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 20, "finished_events": 2})

        mark_notified(state_path, 2)

        assert load_state(state_path)["notified_events"] == [2]

    def test_keeps_the_counts_it_shares_the_file_with(self, tmp_path):
        state_path = tmp_path / "state.json"
        save_state(state_path, {"finished_fixtures": 20, "finished_events": 2})

        mark_notified(state_path, 2)

        state = load_state(state_path)
        assert state["finished_fixtures"] == 20
        assert state["finished_events"] == 2

    def test_is_idempotent(self, tmp_path):
        state_path = tmp_path / "state.json"
        mark_notified(state_path, 2)
        mark_notified(state_path, 2)

        assert load_state(state_path)["notified_events"] == [2]

    def test_accumulates_across_gameweeks_in_order(self, tmp_path):
        state_path = tmp_path / "state.json"
        for gw in (2, 1, 3):
            mark_notified(state_path, gw)

        assert load_state(state_path)["notified_events"] == [1, 2, 3]


class TestSaveCounts:
    """--save runs before the card is sent, so it must not clear the marker."""

    def test_preserves_notified_events(self, tmp_path):
        state_path = tmp_path / "state.json"
        save_state(state_path, {"notified_events": [1, 2]})
        api = StubAPI(
            finished_fixture_count=30, total_fixture_count=380,
            finished_event_count=3, total_event_count=38,
        )

        save_counts(api, state_path)

        state = load_state(state_path)
        assert state["notified_events"] == [1, 2]
        assert state["finished_fixtures"] == 30
        assert state["finished_events"] == 3
