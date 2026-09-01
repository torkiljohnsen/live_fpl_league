"""Integration tests for WeeklyReport class.

Uses a self-contained DummyAPI with minimal but internally consistent
sample data to test the full build() and save_report() flow.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any
from unittest.mock import patch

import pytest

from fpl.weekly_report import (
    WeeklyReport,
    _percentile,
    detect_current_gameweek,
    get_narrative_path,
    get_report_path,
    get_season_from_bootstrap,
)

# ---------------------------------------------------------------------------
# Minimal bootstrap data with 4 elements, 2 teams, 4 element_types
# ---------------------------------------------------------------------------

BOOTSTRAP_DATA: dict[str, Any] = {
    "total_players": 10_000_000,
    "chips": [
        {"name": "wildcard", "start_event": 1, "stop_event": 19},
        {"name": "freehit", "start_event": 1, "stop_event": 19},
        {"name": "bboost", "start_event": 1, "stop_event": 19},
        {"name": "3xc", "start_event": 1, "stop_event": 19},
    ],
    "events": [
        {
            "id": 1,
            "name": "Gameweek 1",
            "deadline_time": "2025-08-15T17:30:00Z",
            "finished": True,
            "data_checked": True,
            "is_next": False,
            "is_previous": False,
            "is_current": False,
            "average_entry_score": 50,
            "highest_score": 100,
        },
        {
            "id": 2,
            "name": "Gameweek 2",
            "deadline_time": "2025-08-22T17:30:00Z",
            "finished": True,
            "data_checked": True,
            "is_next": False,
            "is_previous": True,
            "is_current": False,
            "average_entry_score": 55,
            "highest_score": 90,
        },
        {
            "id": 3,
            "name": "Gameweek 3",
            "deadline_time": "2025-08-29T17:30:00Z",
            "finished": False,
            "is_next": True,
            "is_previous": False,
            "is_current": True,
            "average_entry_score": None,
            "highest_score": None,
        },
    ],
    "elements": [
        {
            "id": 100,
            "first_name": "Mohamed",
            "second_name": "Salah",
            "web_name": "Salah",
            "team": 1,
            "team_code": 14,
            "element_type": 3,
        },
        {
            "id": 200,
            "first_name": "Erling",
            "second_name": "Haaland",
            "web_name": "Haaland",
            "team": 2,
            "team_code": 43,
            "element_type": 4,
        },
        {
            "id": 300,
            "first_name": "Virgil",
            "second_name": "van Dijk",
            "web_name": "van Dijk",
            "team": 1,
            "team_code": 14,
            "element_type": 2,
        },
        {
            "id": 400,
            "first_name": "Alisson",
            "second_name": "Becker",
            "web_name": "Alisson",
            "team": 1,
            "team_code": 14,
            "element_type": 1,
        },
        # Extra players for transfers
        {
            "id": 500,
            "first_name": "Bruno",
            "second_name": "Fernandes",
            "web_name": "Fernandes",
            "team": 2,
            "team_code": 43,
            "element_type": 3,
        },
        {
            "id": 600,
            "first_name": "Bukayo",
            "second_name": "Saka",
            "web_name": "Saka",
            "team": 1,
            "team_code": 14,
            "element_type": 3,
        },
    ],
    "teams": [
        {"id": 1, "code": 14, "name": "Liverpool", "short_name": "LIV"},
        {"id": 2, "code": 43, "name": "Man City", "short_name": "MCI"},
    ],
    "element_types": [
        {"id": 1, "singular_name": "Goalkeeper"},
        {"id": 2, "singular_name": "Defender"},
        {"id": 3, "singular_name": "Midfielder"},
        {"id": 4, "singular_name": "Forward"},
    ],
}

# ---------------------------------------------------------------------------
# League standings with 3 participants
# ---------------------------------------------------------------------------

LEAGUE_STANDINGS: dict[str, Any] = {
    "league": {"id": 12345, "name": "Test League"},
    "standings": {
        "has_next": False,
        "page": 1,
        "results": [
            {
                "id": 1,
                "entry": 1001,
                "player_name": "Alice Manager",
                "entry_name": "Alice FC",
                "rank": 1,
                "last_rank": 2,
                "rank_sort": 1,
                "total": 200,
                "event_total": 70,
                "has_played": True,
            },
            {
                "id": 2,
                "entry": 1002,
                "player_name": "Bob Smith",
                "entry_name": "Bob United",
                "rank": 2,
                "last_rank": 1,
                "rank_sort": 2,
                "total": 180,
                "event_total": 45,
                "has_played": True,
            },
            {
                "id": 3,
                "entry": 1003,
                "player_name": "Charlie Brown",
                "entry_name": "Charlie XI",
                "rank": 3,
                "last_rank": 3,
                "rank_sort": 3,
                "total": 150,
                "event_total": 55,
                "has_played": True,
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# Event live data — points for all elements used in picks
# ---------------------------------------------------------------------------

EVENT_LIVE_DATA: dict[str, Any] = {
    "elements": [
        {"id": 100, "stats": {"total_points": 12}},  # Salah
        {"id": 200, "stats": {"total_points": 8}},  # Haaland
        {"id": 300, "stats": {"total_points": 6}},  # van Dijk
        {"id": 400, "stats": {"total_points": 3}},  # Alisson
        {"id": 500, "stats": {"total_points": 5}},  # Fernandes
        {"id": 600, "stats": {"total_points": 2}},  # Saka
    ],
}

# ---------------------------------------------------------------------------
# Team picks per participant
# ---------------------------------------------------------------------------

# Alice: captains Salah (2x), Haaland vice, van Dijk benched
ALICE_PICKS: dict[str, Any] = {
    "active_chip": None,
    "entry_history": {
        "event": 2,
        "points": 70,
        "total_points": 200,
        "rank": 500000,
        "overall_rank": 100000,
        "event_transfers": 1,
        "event_transfers_cost": 0,
        "value": 1005,
        "bank": 15,
    },
    "picks": [
        {"element": 100, "position": 1, "multiplier": 2, "is_captain": True, "is_vice_captain": False},
        {"element": 200, "position": 2, "multiplier": 1, "is_captain": False, "is_vice_captain": True},
        {"element": 400, "position": 3, "multiplier": 1, "is_captain": False, "is_vice_captain": False},
        {"element": 300, "position": 12, "multiplier": 0, "is_captain": False, "is_vice_captain": False},
    ],
}

# Bob: captains Haaland (2x), Salah vice, Saka benched, plays wildcard chip
BOB_PICKS: dict[str, Any] = {
    "active_chip": "wildcard",
    "entry_history": {
        "event": 2,
        "points": 45,
        "total_points": 180,
        "rank": 2000000,
        "overall_rank": 500000,
        "event_transfers": 3,
        "event_transfers_cost": 4,
        "value": 990,
        "bank": 30,
    },
    "picks": [
        {"element": 200, "position": 1, "multiplier": 2, "is_captain": True, "is_vice_captain": False},
        {"element": 100, "position": 2, "multiplier": 1, "is_captain": False, "is_vice_captain": True},
        {"element": 400, "position": 3, "multiplier": 1, "is_captain": False, "is_vice_captain": False},
        {"element": 600, "position": 12, "multiplier": 0, "is_captain": False, "is_vice_captain": False},
    ],
}

# Charlie: captains Salah (triple captain 3x), no vice captain with points,
# Fernandes benched with 5 points (not a bench disaster, < 20)
CHARLIE_PICKS: dict[str, Any] = {
    "active_chip": "3xc",
    "entry_history": {
        "event": 2,
        "points": 55,
        "total_points": 150,
        "rank": 3000000,
        "overall_rank": 800000,
        "event_transfers": 0,
        "event_transfers_cost": 0,
        "value": 1000,
        "bank": 0,
    },
    "picks": [
        {"element": 100, "position": 1, "multiplier": 3, "is_captain": True, "is_vice_captain": False},
        {"element": 200, "position": 2, "multiplier": 1, "is_captain": False, "is_vice_captain": True},
        {"element": 400, "position": 3, "multiplier": 1, "is_captain": False, "is_vice_captain": False},
        {"element": 500, "position": 12, "multiplier": 0, "is_captain": False, "is_vice_captain": False},
    ],
}

# ---------------------------------------------------------------------------
# Transfer data — Alice made a transfer in GW2, Bob made transfers in GW2,
# Charlie has no transfers
# ---------------------------------------------------------------------------

ALICE_TRANSFERS: list[dict[str, Any]] = [
    {
        "element_in": 200,
        "element_in_cost": 130,
        "element_out": 500,
        "element_out_cost": 100,
        "entry": 1001,
        "event": 2,
        "time": "2025-08-21T10:00:00Z",
    },
]

BOB_TRANSFERS: list[dict[str, Any]] = [
    {
        "element_in": 100,
        "element_in_cost": 125,
        "element_out": 600,
        "element_out_cost": 75,
        "entry": 1002,
        "event": 2,
        "time": "2025-08-21T11:00:00Z",
    },
    {
        "element_in": 300,
        "element_in_cost": 65,
        "element_out": 500,
        "element_out_cost": 70,
        "entry": 1002,
        "event": 2,
        "time": "2025-08-21T11:05:00Z",
    },
    # Transfer from GW1 — should be excluded when building GW2 report
    {
        "element_in": 400,
        "element_in_cost": 55,
        "element_out": 300,
        "element_out_cost": 60,
        "entry": 1002,
        "event": 1,
        "time": "2025-08-14T09:00:00Z",
    },
]

CHARLIE_TRANSFERS: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Team history per participant — GW1 and GW2 "current" entries, plus
# chips already played this season. GW2 points/points_on_bench/
# event_transfers_cost are internally consistent with the picks above.
# ---------------------------------------------------------------------------

ALICE_HISTORY: dict[str, Any] = {
    "current": [
        {
            "event": 1,
            "points": 60,
            "total_points": 60,
            "rank": 400000,
            "overall_rank": 150000,
            "bank": 10,
            "value": 1000,
            "event_transfers": 0,
            "event_transfers_cost": 0,
            "points_on_bench": 5,
        },
        {
            "event": 2,
            "points": 70,
            "total_points": 200,
            "rank": 500000,
            "overall_rank": 100000,
            "bank": 15,
            "value": 1005,
            "event_transfers": 1,
            "event_transfers_cost": 0,
            "points_on_bench": 6,
        },
    ],
    "chips": [],
}

BOB_HISTORY: dict[str, Any] = {
    "current": [
        {
            "event": 1,
            "points": 50,
            "total_points": 50,
            "rank": 1500000,
            "overall_rank": 700000,
            "bank": 20,
            "value": 1000,
            "event_transfers": 1,
            "event_transfers_cost": 0,
            "points_on_bench": 3,
        },
        {
            "event": 2,
            "points": 45,
            "total_points": 180,
            "rank": 2000000,
            "overall_rank": 500000,
            "bank": 30,
            "value": 990,
            "event_transfers": 3,
            "event_transfers_cost": 4,
            "points_on_bench": 2,
        },
    ],
    "chips": [{"name": "wildcard", "event": 2}],
}

CHARLIE_HISTORY: dict[str, Any] = {
    "current": [
        {
            "event": 1,
            "points": 40,
            "total_points": 40,
            "rank": 3500000,
            "overall_rank": 900000,
            "bank": 0,
            "value": 1000,
            "event_transfers": 0,
            "event_transfers_cost": 0,
            "points_on_bench": 4,
        },
        {
            "event": 2,
            "points": 55,
            "total_points": 150,
            "rank": 3000000,
            "overall_rank": 800000,
            "bank": 0,
            "value": 1000,
            "event_transfers": 0,
            "event_transfers_cost": 0,
            "points_on_bench": 5,
        },
    ],
    "chips": [{"name": "3xc", "event": 2}],
}


# ---------------------------------------------------------------------------
# DummyAPI for WeeklyReport integration tests
# ---------------------------------------------------------------------------


class WeeklyReportDummyAPI:
    """Minimal API returning test fixtures for WeeklyReport."""

    def __init__(self) -> None:
        self._picks: dict[str, dict[str, Any]] = {
            "1001": ALICE_PICKS,
            "1002": BOB_PICKS,
            "1003": CHARLIE_PICKS,
        }
        self._transfers: dict[str, list[dict[str, Any]]] = {
            "1001": ALICE_TRANSFERS,
            "1002": BOB_TRANSFERS,
            "1003": CHARLIE_TRANSFERS,
        }
        self._histories: dict[str, dict[str, Any]] = {
            "1001": ALICE_HISTORY,
            "1002": BOB_HISTORY,
            "1003": CHARLIE_HISTORY,
        }

    def get_bootstrap_static(self) -> dict[str, Any]:
        return BOOTSTRAP_DATA

    def get_league_standings(self, league_id: str) -> dict[str, Any]:
        return LEAGUE_STANDINGS

    def get_team(self, team_id: str) -> dict[str, Any]:
        return {}

    def get_team_history(self, team_id: str) -> dict[str, Any]:
        return self._histories.get(team_id, {"current": [], "chips": []})

    def get_team_picks(self, team_id: str, event_id: str) -> dict[str, Any]:
        return self._picks.get(team_id, {"picks": [], "entry_history": {}})

    def get_transfers(self, team_id: str) -> list[dict[str, Any]]:
        return self._transfers.get(team_id, [])

    def get_fixtures(self, event_id: int | None = None) -> list[dict[str, Any]]:
        return []

    def get_event_live(self, event_id: str) -> dict[str, Any]:
        return EVENT_LIVE_DATA


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

LEAGUE_ID = "12345"
EVENT_ID = 2


class TestWeeklyReportBuild:
    """Test the full build() flow."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_report_has_all_top_level_keys(self, report: dict[str, Any]) -> None:
        assert "meta" in report
        assert "standings" in report
        assert "awards" in report
        assert "league_summary" in report

    def test_meta_section(self, report: dict[str, Any]) -> None:
        meta = report["meta"]
        assert meta["league_id"] == LEAGUE_ID
        assert meta["league_name"] == "Test League"
        assert meta["season"] == "2025-26"
        assert meta["event_id"] == EVENT_ID
        assert "generated_at" in meta
        # GW2 should have previous report/narrative paths for GW1
        assert meta["previous_report"] == f"weekly_report/reports/{LEAGUE_ID}/2025-26/gw1.json"
        assert meta["previous_narrative"] == f"docs/narratives/2025-26/{LEAGUE_ID}/gw1.md"

    def test_meta_gw1_has_no_previous(self) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, 1)
        result = wr.build()
        assert result["meta"]["previous_report"] is None
        assert result["meta"]["previous_narrative"] is None

    def test_standings_sorted_by_league_rank(self, report: dict[str, Any]) -> None:
        standings = report["standings"]
        assert len(standings) == 3
        ranks = [p["league_rank"] for p in standings]
        assert ranks == sorted(ranks)

    def test_participant_has_all_required_fields(self, report: dict[str, Any]) -> None:
        required_fields = [
            "entry_id",
            "team_name",
            "manager_name",
            "player_first_name",
            "event_total",
            "net_points",
            "total_points",
            "league_rank",
            "league_rank_previous",
            "league_rank_change",
            "overall_rank",
            "team_value",
            "bank",
            "bench_points",
            "bench_players",
            "chip_played",
            "captain",
            "vice_captain",
            "squad",
            "transfers",
            "transfer_cost",
            "transfers_made",
        ]
        for participant in report["standings"]:
            for field in required_fields:
                assert field in participant, (
                    f"Missing field '{field}' in participant {participant.get('player_first_name')}"
                )

    def test_alice_participant_data(self, report: dict[str, Any]) -> None:
        alice = report["standings"][0]  # rank 1
        assert alice["entry_id"] == 1001
        assert alice["team_name"] == "Alice FC"
        assert alice["manager_name"] == "Alice Manager"
        assert alice["player_first_name"] == "Alice"
        assert alice["event_total"] == 70
        assert alice["transfer_cost"] == 0
        assert alice["net_points"] == 70  # 70 - 0
        assert alice["total_points"] == 200
        assert alice["league_rank"] == 1
        assert alice["league_rank_previous"] == 2
        assert alice["league_rank_change"] == 1  # 2 - 1 = +1 (rose)
        assert alice["overall_rank"] == 100000
        assert alice["team_value"] == 100.5  # 1005 / 10
        assert alice["bank"] == 1.5  # 15 / 10
        assert alice["chip_played"] is None
        assert alice["transfers_made"] == 1

    def test_captain_points_multiplied(self, report: dict[str, Any]) -> None:
        # Alice captains Salah (12 raw * 2x = 24)
        alice = report["standings"][0]
        assert alice["captain"]["name"] == "Mohamed Salah"
        assert alice["captain"]["points"] == 24

        # Bob captains Haaland (8 raw * 2x = 16)
        bob = report["standings"][1]
        assert bob["captain"]["name"] == "Erling Haaland"
        assert bob["captain"]["points"] == 16

    def test_triple_captain_points(self, report: dict[str, Any]) -> None:
        # Charlie plays 3xc chip, captains Salah (12 raw * 3x = 36)
        charlie = report["standings"][2]
        assert charlie["chip_played"] == "3xc"
        assert charlie["captain"]["name"] == "Mohamed Salah"
        assert charlie["captain"]["points"] == 36

    def test_bench_points_calculated(self, report: dict[str, Any]) -> None:
        # Alice: van Dijk (6 pts) on bench (position 12, multiplier 0)
        alice = report["standings"][0]
        assert alice["bench_points"] == 6
        assert len(alice["bench_players"]) == 1
        assert alice["bench_players"][0]["name"] == "Virgil van Dijk"
        assert alice["bench_players"][0]["points"] == 6

    def test_bob_bench_points(self, report: dict[str, Any]) -> None:
        # Bob: Saka (2 pts) on bench
        bob = report["standings"][1]
        assert bob["bench_points"] == 2
        assert len(bob["bench_players"]) == 1
        assert bob["bench_players"][0]["name"] == "Bukayo Saka"

    def test_transfers_filtered_by_event(self, report: dict[str, Any]) -> None:
        # Alice: 1 transfer in GW2
        alice = report["standings"][0]
        assert len(alice["transfers"]) == 1
        assert alice["transfers"][0]["player_in"] == "Erling Haaland"
        assert alice["transfers"][0]["player_out"] == "Bruno Fernandes"

        # Bob: 2 transfers in GW2 (GW1 transfer excluded)
        bob = report["standings"][1]
        assert len(bob["transfers"]) == 2

    def test_transfer_points_populated(self, report: dict[str, Any]) -> None:
        alice = report["standings"][0]
        t = alice["transfers"][0]
        # Haaland in (8 pts), Fernandes out (5 pts)
        assert t["player_in_points"] == 8
        assert t["player_out_points"] == 5

    def test_participant_with_no_transfers(self, report: dict[str, Any]) -> None:
        charlie = report["standings"][2]
        assert charlie["transfers"] == []
        assert charlie["transfer_cost"] == 0
        assert charlie["transfers_made"] == 0

    def test_chip_played_populated(self, report: dict[str, Any]) -> None:
        bob = report["standings"][1]
        assert bob["chip_played"] == "wildcard"

        charlie = report["standings"][2]
        assert charlie["chip_played"] == "3xc"

        alice = report["standings"][0]
        assert alice["chip_played"] is None

    def test_hit_cost_in_net_points(self, report: dict[str, Any]) -> None:
        # Bob: 45 points - 4 hit cost = 41 net
        bob = report["standings"][1]
        assert bob["event_total"] == 45
        assert bob["transfer_cost"] == 4
        assert bob["net_points"] == 41

    def test_player_names_resolved(self, report: dict[str, Any]) -> None:
        """Player names come from PlayerRegistry, not raw element IDs."""
        alice = report["standings"][0]
        squad_names = [p["name"] for p in alice["squad"]]
        assert "Mohamed Salah" in squad_names
        assert "Erling Haaland" in squad_names

    def test_squad_positions_and_multipliers(self, report: dict[str, Any]) -> None:
        alice = report["standings"][0]
        captain = [p for p in alice["squad"] if p["is_captain"]]
        assert len(captain) == 1
        assert captain[0]["element_id"] == 100
        assert captain[0]["multiplier"] == 2

        bench = [p for p in alice["squad"] if p["multiplier"] == 0]
        assert len(bench) == 1
        assert bench[0]["element_id"] == 300


class TestWeeklyReportMetaGlobalContext:
    """Test meta.next_event / meta.is_golden (issue #40 workstream K)."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_next_event(self, report: dict[str, Any]) -> None:
        next_event = report["meta"]["next_event"]
        assert next_event == {
            "id": 3,
            "deadline_time": "2025-08-29T17:30:00Z",
            "is_golden": False,
        }

    def test_is_golden_false_for_gw2(self, report: dict[str, Any]) -> None:
        assert report["meta"]["is_golden"] is False

    def test_next_event_none_when_next_gw_absent(self) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, 3)
        result = wr.build()
        assert result["meta"]["next_event"] is None

    def test_is_golden_true_on_4th_gameweek(self) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, 4)
        result = wr.build()
        assert result["meta"]["is_golden"] is True


class TestWeeklyReportGlobalBlock:
    """Test the `global` section (issue #40 workstream K)."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_global_fields(self, report: dict[str, Any]) -> None:
        g = report["global"]
        assert g["average_score"] == 55
        assert g["highest_score"] == 90
        assert g["total_players"] == 10_000_000

    def test_league_vs_world(self, report: dict[str, Any]) -> None:
        # League net-points average is 55.3 (see TestWeeklyReportLeagueSummary),
        # global average is 55 -> 0.3
        assert report["global"]["league_vs_world"] == 0.3


class TestParticipantGlobalContextFields:
    """Test per-manager fields added by issue #40 workstream K."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_alice_fields(self, report: dict[str, Any]) -> None:
        alice = report["standings"][0]
        assert alice["event_rank"] == 500000
        assert alice["event_percentile"] == 5.0
        assert alice["overall_percentile"] == 1.0
        assert alice["points_per_starter"] == 23.3  # 70 / 3 starters
        assert alice["vs_global_average"] == 15  # 70 - 55
        assert alice["form_last_5"] == 65.0  # mean(60, 70)
        assert alice["bench_points_season"] == 11  # 5 + 6
        assert alice["hit_cost_season"] == 0
        assert set(alice["chips_remaining"]) == {"wildcard", "freehit", "bboost", "3xc"}
        assert alice["chips_played_season"] == []

    def test_bob_fields(self, report: dict[str, Any]) -> None:
        bob = report["standings"][1]
        assert bob["event_percentile"] == 20.0
        assert bob["overall_percentile"] == 5.0
        assert bob["points_per_starter"] == 15.0  # 45 / 3 starters
        assert bob["vs_global_average"] == -10  # 45 - 55
        assert bob["form_last_5"] == 47.5  # mean(50, 45)
        assert bob["bench_points_season"] == 5  # 3 + 2
        assert bob["hit_cost_season"] == 4
        assert set(bob["chips_remaining"]) == {"freehit", "bboost", "3xc"}
        assert bob["chips_played_season"] == [{"name": "wildcard", "event": 2}]

    def test_charlie_fields(self, report: dict[str, Any]) -> None:
        charlie = report["standings"][2]
        assert charlie["event_percentile"] == 30.0
        assert charlie["overall_percentile"] == 8.0
        assert charlie["points_per_starter"] == 18.3  # 55 / 3 starters
        assert charlie["vs_global_average"] == 0
        assert charlie["form_last_5"] == 47.5  # mean(40, 55)
        assert set(charlie["chips_remaining"]) == {"wildcard", "freehit", "bboost"}

    def test_form_last_5_none_in_gw1(self) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, 1)
        result = wr.build()
        for p in result["standings"]:
            assert p["form_last_5"] is None


class TestLeagueSummaryGlobalContext:
    """Test league_summary.global_average / managers_above_global_average."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_global_average(self, report: dict[str, Any]) -> None:
        assert report["league_summary"]["global_average"] == 55

    def test_managers_above_global_average(self, report: dict[str, Any]) -> None:
        # Only Alice (70) is above the global average of 55
        assert report["league_summary"]["managers_above_global_average"] == 1


class TestAnglesBlock:
    """Test the `angles` section (issue #40 workstream F)."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_angles_has_all_keys(self, report: dict[str, Any]) -> None:
        angles = report["angles"]
        for key in (
            "head_to_head",
            "differentials",
            "captain_that_would_have_won",
            "streaks",
            "records",
            "chip_tracker",
        ):
            assert key in angles, f"Missing angle key: {key}"

    def test_head_to_head_this_gw(self, report: dict[str, Any]) -> None:
        h2h = {r["player_name"]: r for r in report["angles"]["head_to_head"]}
        assert h2h["Alice"]["beat"] == 2
        assert h2h["Alice"]["lost_to"] == 0
        assert h2h["Bob"]["beat"] == 0
        assert h2h["Bob"]["lost_to"] == 2
        assert h2h["Charlie"]["beat"] == 1
        assert h2h["Charlie"]["lost_to"] == 1

    def test_head_to_head_season_record(self, report: dict[str, Any]) -> None:
        h2h = {r["player_name"]: r for r in report["angles"]["head_to_head"]}
        assert h2h["Alice"]["season_record"] == {"wins": 4, "losses": 0}
        assert h2h["Bob"]["season_record"] == {"wins": 1, "losses": 3}
        assert h2h["Charlie"]["season_record"] == {"wins": 1, "losses": 3}

    def test_differentials(self, report: dict[str, Any]) -> None:
        diffs = report["angles"]["differentials"]
        top_names = {d["player_name"] for d in diffs["top"]}
        assert top_names == {"Virgil van Dijk", "Bukayo Saka", "Bruno Fernandes"}
        # Salah/Haaland/Alisson are owned by all 3 managers -> not differentials
        assert all(d["player_name"] not in {"Mohamed Salah", "Erling Haaland"} for d in diffs["top"])

    def test_captain_that_would_have_won(self, report: dict[str, Any]) -> None:
        result = report["angles"]["captain_that_would_have_won"]
        assert result is not None
        assert result["player_name"] == "Mohamed Salah"
        assert result["points"] == 12
        assert result["captained_by"] == 2  # Alice and Charlie both captained Salah

    def test_streaks_empty_with_only_two_gws(self, report: dict[str, Any]) -> None:
        # Streaks require >= 3 gameweeks of history; only 2 are available.
        assert report["angles"]["streaks"] == []

    def test_records(self, report: dict[str, Any]) -> None:
        records = report["angles"]["records"]
        assert records["best"] == {"player_name": "Alice", "event_id": 2, "points": 70}
        assert records["worst"] == {"player_name": "Charlie", "event_id": 1, "points": 40}

    def test_chip_tracker(self, report: dict[str, Any]) -> None:
        tracker = {r["player_name"]: r for r in report["angles"]["chip_tracker"]}
        assert set(tracker["Alice"]["chips_remaining"]) == {
            "wildcard", "freehit", "bboost", "3xc"
        }
        assert tracker["Bob"]["chips_played"] == [{"name": "wildcard", "event": 2}]
        assert tracker["Charlie"]["chips_played"] == [{"name": "3xc", "event": 2}]


class TestStorylines:
    """Test the top-level `storylines` key (issue #40 workstream F)."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_storylines_present_and_capped(self, report: dict[str, Any]) -> None:
        storylines = report["storylines"]
        assert isinstance(storylines, list)
        assert len(storylines) <= 6

    def test_storylines_sorted_descending(self, report: dict[str, Any]) -> None:
        scores = [s["score"] for s in report["storylines"]]
        assert scores == sorted(scores, reverse=True)

    def test_chip_played_outranks_plain_round_win(self, report: dict[str, Any]) -> None:
        """Bob's wildcard, played for the round's lowest net score, should
        score higher than the plain round win."""
        storylines = report["storylines"]
        bobs_chip = next(
            s for s in storylines
            if s["kind"] == "chip_played" and s["managers"] == ["Bob"]
        )
        round_win = next(s for s in storylines if s["kind"] == "round_win")
        assert bobs_chip["score"] > round_win["score"]

    def test_storyline_shape(self, report: dict[str, Any]) -> None:
        for s in report["storylines"]:
            assert set(s.keys()) == {"kind", "score", "managers", "facts", "summary"}
            assert isinstance(s["managers"], list)
            assert isinstance(s["summary"], str)
            assert s["summary"]


class TestReportGoldenShape:
    """One full-shape test: every top-level and per-manager key introduced
    by issue #40 (workstreams F and K) and #35 is present in a real
    build() output."""

    def test_full_report_shape(self) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        report = wr.build()

        assert set(report.keys()) == {
            "meta", "standings", "awards", "league_summary", "global",
            "angles", "storylines",
        }

        assert "next_event" in report["meta"]
        assert "is_golden" in report["meta"]

        assert set(report["global"].keys()) == {
            "average_score", "highest_score", "total_players", "league_vs_world",
        }

        assert set(report["angles"].keys()) == {
            "head_to_head", "differentials", "captain_that_would_have_won",
            "streaks", "records", "chip_tracker",
        }

        assert "global_average" in report["league_summary"]
        assert "managers_above_global_average" in report["league_summary"]

        new_participant_fields = [
            "event_rank", "event_percentile", "overall_percentile",
            "points_per_starter", "vs_global_average", "form_last_5",
            "bench_points_season", "hit_cost_season", "chips_remaining",
            "chips_played_season",
        ]
        for p in report["standings"]:
            for field in new_participant_fields:
                assert field in p, f"Missing field '{field}' in participant"

        assert isinstance(report["storylines"], list)


class TestWeeklyReportAwards:
    """Test the awards section of the report."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_awards_has_all_keys(self, report: dict[str, Any]) -> None:
        awards = report["awards"]
        expected_keys = [
            "highest_scorer",
            "lowest_scorer",
            "biggest_rise",
            "biggest_fall",
            "bench_disasters",
            "best_transfer",
            "worst_transfer",
            "captain_summary",
            "chip_usage",
            "hit_takers",
        ]
        for key in expected_keys:
            assert key in awards, f"Missing award key: {key}"

    def test_highest_scorer(self, report: dict[str, Any]) -> None:
        hs = report["awards"]["highest_scorer"]
        assert hs is not None
        # Alice has highest net_points = 70
        assert hs["player_name"] == "Alice"
        assert hs["points"] == 70

    def test_lowest_scorer(self, report: dict[str, Any]) -> None:
        ls = report["awards"]["lowest_scorer"]
        assert ls is not None
        # Bob has lowest net_points = 41 (45 - 4 hit)
        assert ls["player_name"] == "Bob"
        assert ls["points"] == 41

    def test_chip_usage(self, report: dict[str, Any]) -> None:
        chips = report["awards"]["chip_usage"]
        assert isinstance(chips, list)
        # Bob: wildcard, Charlie: 3xc
        assert len(chips) == 2
        chip_names = {c["chip"] for c in chips}
        assert "wildcard" in chip_names
        assert "3xc" in chip_names

    def test_hit_takers(self, report: dict[str, Any]) -> None:
        hits = report["awards"]["hit_takers"]
        assert isinstance(hits, list)
        # Only Bob took a hit (4 pts)
        assert len(hits) == 1
        assert hits[0]["player_name"] == "Bob"
        assert hits[0]["cost"] == 4

    def test_captain_summary(self, report: dict[str, Any]) -> None:
        cs = report["awards"]["captain_summary"]
        assert cs is not None
        # Most popular captain: Salah (Alice + Charlie = 2)
        assert cs["most_popular"]["player"] == "Mohamed Salah"
        assert cs["most_popular"]["count"] == 2
        # Best captain pick: Charlie (3xc Salah = 36)
        assert cs["best_pick"]["captain"] == "Mohamed Salah"
        assert cs["best_pick"]["points"] == 36

    def test_bench_disasters_empty_when_below_threshold(
        self, report: dict[str, Any]
    ) -> None:
        # No one has 20+ bench points
        bd = report["awards"]["bench_disasters"]
        assert bd == []


class TestWeeklyReportLeagueSummary:
    """Test the league_summary section."""

    @pytest.fixture
    def report(self) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_total_participants(self, report: dict[str, Any]) -> None:
        assert report["league_summary"]["total_participants"] == 3

    def test_leader(self, report: dict[str, Any]) -> None:
        leader = report["league_summary"]["leader"]
        assert leader["player_name"] == "Alice"
        assert leader["total_points"] == 200

    def test_average_score(self, report: dict[str, Any]) -> None:
        # Net points: Alice=70, Bob=41, Charlie=55 → avg = 166/3 = 55.3
        avg = report["league_summary"]["average_score"]
        assert avg == 55.3


class TestWeeklyReportSaveReport:
    """Test save_report() creates correct file path and valid JSON."""

    def test_save_report_creates_file(self, tmp_path: Any) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        wr.build()

        result_path = wr.save_report(str(tmp_path))

        expected_path = os.path.join(
            str(tmp_path), "weekly_report", "reports", LEAGUE_ID, "2025-26", "gw2.json"
        )
        assert os.path.normpath(result_path) == os.path.normpath(expected_path)
        assert os.path.exists(result_path)

    def test_saved_json_is_valid(self, tmp_path: Any) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        wr.build()

        result_path = wr.save_report(str(tmp_path))

        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "meta" in data
        assert "standings" in data
        assert "awards" in data
        assert "league_summary" in data
        assert data["meta"]["event_id"] == EVENT_ID

    def test_save_report_creates_directories(self, tmp_path: Any) -> None:
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        wr.build()

        result_path = wr.save_report(str(tmp_path))
        assert os.path.isfile(result_path)


class TestWeeklyReportEdgeCases:
    """Edge cases: tied scores, single participant."""

    def test_tied_scores_both_in_standings(self) -> None:
        """Two participants with the same net points both appear."""
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        report = wr.build()

        # All 3 participants should be in standings regardless of ties
        assert len(report["standings"]) == 3

    def test_report_with_different_event_id(self) -> None:
        """Building for a different event ID still works."""
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, 1)
        report = wr.build()

        assert report["meta"]["event_id"] == 1
        # GW1 — no transfers match event=1 for Alice/Charlie
        # Bob has one GW1 transfer in the fixtures
        bob = next(
            p for p in report["standings"] if p["entry_id"] == 1002
        )
        assert len(bob["transfers"]) == 1


class TestCaptainSubstitution:
    """Test captain substitution detection in _build_squad_data."""

    @pytest.fixture
    def report_with_captain_sub(self) -> dict[str, Any]:
        """Build a report where Alice's captain (Haaland) didn't play,
        so VC (Salah) gets the armband with 2x multiplier."""
        # Override Alice's picks: captain Haaland has multiplier 0,
        # VC Salah has multiplier 2 (subbed in as captain)
        alice_picks_vc_sub: dict[str, Any] = {
            "active_chip": None,
            "entry_history": ALICE_PICKS["entry_history"],
            "picks": [
                {"element": 200, "position": 1, "multiplier": 0, "is_captain": True, "is_vice_captain": False},
                {"element": 100, "position": 2, "multiplier": 2, "is_captain": False, "is_vice_captain": True},
                {"element": 400, "position": 3, "multiplier": 1, "is_captain": False, "is_vice_captain": False},
                {"element": 300, "position": 12, "multiplier": 0, "is_captain": False, "is_vice_captain": False},
            ],
        }

        class VCSubDummyAPI(WeeklyReportDummyAPI):
            def get_team_picks(self, team_id: str, event_id: str) -> dict[str, Any]:
                if team_id == "1001":
                    return alice_picks_vc_sub
                return super().get_team_picks(team_id, event_id)

        api = VCSubDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        return wr.build()

    def test_captain_did_not_play_flag(self, report_with_captain_sub: dict[str, Any]) -> None:
        alice = report_with_captain_sub["standings"][0]
        assert alice["captain"]["did_not_play"] is True

    def test_effective_captain_name(self, report_with_captain_sub: dict[str, Any]) -> None:
        alice = report_with_captain_sub["standings"][0]
        assert alice["captain"]["effective_captain"] == "Mohamed Salah"

    def test_effective_points(self, report_with_captain_sub: dict[str, Any]) -> None:
        alice = report_with_captain_sub["standings"][0]
        # Salah has 12 raw points * 2x multiplier = 24
        assert alice["captain"]["effective_points"] == 24

    def test_original_captain_points_zero(self, report_with_captain_sub: dict[str, Any]) -> None:
        alice = report_with_captain_sub["standings"][0]
        # Haaland (captain, didn't play): 8 raw * 0 multiplier = 0
        assert alice["captain"]["points"] == 0

    def test_vc_substituted_in_flag(self, report_with_captain_sub: dict[str, Any]) -> None:
        alice = report_with_captain_sub["standings"][0]
        assert alice["vice_captain"].get("substituted_in") is True

    def test_normal_captain_not_flagged(self) -> None:
        """When captain plays normally, did_not_play should be False."""
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        report = wr.build()
        alice = report["standings"][0]
        assert alice["captain"]["did_not_play"] is False
        assert "effective_points" not in alice["captain"]
        assert "effective_captain" not in alice["captain"]

    def test_captain_sub_in_awards(self, report_with_captain_sub: dict[str, Any]) -> None:
        """Captain summary awards should use effective points."""
        cs = report_with_captain_sub["awards"]["captain_summary"]
        subs = cs["vice_captain_substitutions"]
        assert len(subs) == 1
        assert subs[0]["manager"] == "Alice"
        assert subs[0]["original_captain"] == "Erling Haaland"
        assert subs[0]["effective_captain"] == "Mohamed Salah"
        assert subs[0]["effective_points"] == 24


class TestGetSeasonFromBootstrap:
    """Test the standalone get_season_from_bootstrap() helper."""

    def test_normal_season(self) -> None:
        assert get_season_from_bootstrap(BOOTSTRAP_DATA) == "2025-26"

    def test_empty_events(self) -> None:
        assert get_season_from_bootstrap({"events": []}) == "unknown"

    def test_no_events_key(self) -> None:
        assert get_season_from_bootstrap({}) == "unknown"

    def test_empty_deadline(self) -> None:
        data: dict[str, Any] = {"events": [{"deadline_time": ""}]}
        assert get_season_from_bootstrap(data) == "unknown"


class TestDetectCurrentGameweek:
    """Test the detect_current_gameweek() helper."""

    def test_returns_latest_finished_gameweek(self) -> None:
        api = WeeklyReportDummyAPI()
        assert detect_current_gameweek(api) == 2

    def test_exits_when_no_finished_gameweek(self) -> None:
        class NoFinishedAPI(WeeklyReportDummyAPI):
            def get_bootstrap_static(self) -> dict[str, Any]:
                return {"events": [{"id": 1, "finished": False}]}

        with pytest.raises(SystemExit):
            detect_current_gameweek(NoFinishedAPI())

    def test_skips_a_finished_but_unlocked_gameweek(self) -> None:
        """Points are not final until the gameweek locks at 09:00 UK the
        day after its last match. Reporting on GW3 before then would use
        pre-review BPS and Defensive Contribution numbers."""

        class UnlockedAPI(WeeklyReportDummyAPI):
            def get_bootstrap_static(self) -> dict[str, Any]:
                return {"events": [
                    {"id": 2, "finished": True, "data_checked": True},
                    {"id": 3, "finished": True, "data_checked": False},
                ]}

        assert detect_current_gameweek(UnlockedAPI()) == 2


class TestPathHelpers:
    """Test get_report_path() and get_narrative_path()."""

    def test_report_path(self) -> None:
        path = get_report_path(".", "12345", "2025-26", 5)
        assert str(path).replace("\\", "/") == "weekly_report/reports/12345/2025-26/gw5.json"

    def test_narrative_path(self) -> None:
        path = get_narrative_path(".", "12345", "2025-26", 5)
        assert str(path).replace("\\", "/") == "docs/narratives/2025-26/12345/gw5.md"

    def test_report_path_with_output_dir(self) -> None:
        path = get_report_path("/tmp/out", "999", "2024-25", 10)
        assert path.name == "gw10.json"
        assert "999" in str(path)

    def test_narrative_path_with_output_dir(self) -> None:
        path = get_narrative_path("/tmp/out", "999", "2024-25", 10)
        assert path.name == "gw10.md"
        assert "999" in str(path)


class TestSkipExisting:
    """Test the --skip-existing CLI behavior."""

    def test_skip_existing_when_report_exists(self, tmp_path: Any) -> None:
        """When report exists, skip generation."""
        report_dir = tmp_path / "weekly_report" / "reports" / LEAGUE_ID / "2025-26"
        report_dir.mkdir(parents=True)
        (report_dir / "gw2.json").write_text("{}", encoding="utf-8")

        with patch("generate_weekly_report.FPL_API") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_bootstrap_static.return_value = BOOTSTRAP_DATA

            from generate_weekly_report import main

            with patch(
                "sys.argv",
                [
                    "generate_weekly_report.py",
                    "-l", LEAGUE_ID,
                    "-e", "2",
                    "--skip-existing",
                    "--output-dir", str(tmp_path),
                ],
            ):
                main()

            # Nothing should have been built
            mock_api.get_league_standings.assert_not_called()

    def test_no_skip_when_report_missing(self, tmp_path: Any) -> None:
        """When report file doesn't exist, --skip-existing still builds."""
        with patch("generate_weekly_report.FPL_API") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_bootstrap_static.return_value = BOOTSTRAP_DATA
            mock_api.get_league_standings.return_value = LEAGUE_STANDINGS
            mock_api.get_event_live.return_value = EVENT_LIVE_DATA
            mock_api.get_team_picks.side_effect = (
                lambda tid, eid: {
                    "1001": ALICE_PICKS,
                    "1002": BOB_PICKS,
                    "1003": CHARLIE_PICKS,
                }.get(tid, {"picks": [], "entry_history": {}})
            )
            mock_api.get_transfers.side_effect = (
                lambda tid: {
                    "1001": ALICE_TRANSFERS,
                    "1002": BOB_TRANSFERS,
                    "1003": CHARLIE_TRANSFERS,
                }.get(tid, [])
            )
            mock_api.get_team_history.side_effect = (
                lambda tid: {
                    "1001": ALICE_HISTORY,
                    "1002": BOB_HISTORY,
                    "1003": CHARLIE_HISTORY,
                }.get(tid, {"current": [], "chips": []})
            )

            from generate_weekly_report import main

            with patch(
                "sys.argv",
                [
                    "generate_weekly_report.py",
                    "-l", LEAGUE_ID,
                    "-e", "2",
                    "--skip-existing",
                    "--output-dir", str(tmp_path),
                ],
            ):
                main()

            # Report should have been built
            mock_api.get_league_standings.assert_called_once()


class TestPercentileResolution:
    """A rank at the sharp end must survive being turned into a percentage."""

    def test_elite_rank_keeps_two_significant_digits(self):
        # Rank 3 605 of 10.25 m is the top 0.035 %. Rounding to one decimal
        # gave 0.0, which read as "top 0 %" and invited an invented number.
        assert _percentile(3605, 10250275) == 0.035

    def test_ordinary_rank_keeps_one_decimal(self):
        assert _percentile(286971, 10250275) == 2.8

    def test_mid_table_rank_keeps_one_decimal(self):
        assert _percentile(5000000, 10250275) == 48.8

    def test_floored_so_it_never_renders_in_scientific_notation(self):
        assert _percentile(1, 10250275) == 0.0001

    def test_missing_inputs_give_none(self):
        assert _percentile(None, 10250275) is None
        assert _percentile(3605, None) is None
        assert _percentile(0, 10250275) is None


class TestNewEntrants:
    """A manager joining mid-season is news, not a fall from nowhere."""

    @pytest.fixture
    def standings_with_newcomer(self) -> dict[str, Any]:
        """Charlie joins in GW2: FPL reports last_rank 0 for him."""
        data = copy.deepcopy(LEAGUE_STANDINGS)
        for team in data["standings"]["results"]:
            if team["entry"] == 1003:
                team["last_rank"] = 0
        return data

    def _report(self, standings: dict[str, Any], event_id: int = 2) -> dict[str, Any]:
        api = WeeklyReportDummyAPI()
        api.get_league_standings = lambda league_id: standings  # type: ignore[method-assign]
        return WeeklyReport(api, LEAGUE_ID, event_id).build()

    def test_newcomer_is_flagged(self, standings_with_newcomer):
        report = self._report(standings_with_newcomer)
        charlie = next(p for p in report["standings"] if p["entry_id"] == 1003)
        assert charlie["is_new_entrant"] is True

    def test_newcomer_has_not_fallen(self, standings_with_newcomer):
        """0 - rank would read as a drop of three places he never made."""
        report = self._report(standings_with_newcomer)
        charlie = next(p for p in report["standings"] if p["entry_id"] == 1003)
        assert charlie["league_rank_change"] == 0

    def test_established_managers_are_not_flagged(self, standings_with_newcomer):
        report = self._report(standings_with_newcomer)
        others = [p for p in report["standings"] if p["entry_id"] != 1003]
        assert all(p["is_new_entrant"] is False for p in others)

    def test_league_summary_lists_the_newcomer(self, standings_with_newcomer):
        report = self._report(standings_with_newcomer)
        entrants = report["league_summary"]["new_entrants"]
        assert [e["player_name"] for e in entrants] == ["Charlie"]
        assert entrants[0]["league_rank"] == 3

    def test_no_newcomers_is_an_empty_list(self):
        report = self._report(LEAGUE_STANDINGS)
        assert report["league_summary"]["new_entrants"] == []

    def test_gameweek_one_has_no_new_entrants(self):
        """Everyone has last_rank 0 in GW1; nobody is news for joining."""
        data = copy.deepcopy(LEAGUE_STANDINGS)
        for team in data["standings"]["results"]:
            team["last_rank"] = 0

        report = self._report(data, event_id=1)

        assert report["league_summary"]["new_entrants"] == []
        assert all(not p["is_new_entrant"] for p in report["standings"])
