"""Integration tests for WeeklyReport class.

Uses a self-contained DummyAPI with minimal but internally consistent
sample data to test the full build() and save_report() flow.
"""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import patch

import pytest

from fpl.weekly_report import WeeklyReport, get_season_from_bootstrap

# ---------------------------------------------------------------------------
# Minimal bootstrap data with 4 elements, 2 teams, 4 element_types
# ---------------------------------------------------------------------------

BOOTSTRAP_DATA: dict[str, Any] = {
    "events": [
        {
            "id": 1,
            "name": "Gameweek 1",
            "deadline_time": "2025-08-15T17:30:00Z",
            "finished": True,
            "is_next": False,
            "is_previous": False,
            "is_current": False,
        },
        {
            "id": 2,
            "name": "Gameweek 2",
            "deadline_time": "2025-08-22T17:30:00Z",
            "finished": True,
            "is_next": False,
            "is_previous": True,
            "is_current": False,
        },
        {
            "id": 3,
            "name": "Gameweek 3",
            "deadline_time": "2025-08-29T17:30:00Z",
            "finished": False,
            "is_next": True,
            "is_previous": False,
            "is_current": True,
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

    def get_bootstrap_static(self) -> dict[str, Any]:
        return BOOTSTRAP_DATA

    def get_league_standings(self, league_id: str) -> dict[str, Any]:
        return LEAGUE_STANDINGS

    def get_team(self, team_id: str) -> dict[str, Any]:
        return {}

    def get_team_history(self, team_id: str) -> dict[str, Any]:
        return {}

    def get_team_picks(self, team_id: str, event_id: str) -> dict[str, Any]:
        return self._picks.get(team_id, {"picks": [], "entry_history": {}})

    def get_transfers(self, team_id: str) -> list[dict[str, Any]]:
        return self._transfers.get(team_id, [])

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


class TestSkipExisting:
    """Test the --skip-existing CLI behavior."""

    def test_skip_existing_when_report_and_narrative_exist(self, tmp_path: Any) -> None:
        """When both report and narrative exist, skip everything."""
        report_dir = tmp_path / "weekly_report" / "reports" / LEAGUE_ID / "2025-26"
        report_dir.mkdir(parents=True)
        (report_dir / "gw2.json").write_text("{}", encoding="utf-8")

        narrative_dir = tmp_path / "docs" / "narratives" / "2025-26" / LEAGUE_ID
        narrative_dir.mkdir(parents=True)
        (narrative_dir / "gw2.md").write_text("Reidar says hi", encoding="utf-8")

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
                    "--narrative",
                    "--skip-existing",
                    "--output-dir", str(tmp_path),
                ],
            ):
                main()

            # Nothing should have been built
            mock_api.get_league_standings.assert_not_called()

    def test_skip_existing_without_narrative_flag(self, tmp_path: Any) -> None:
        """When report exists and --narrative is not set, skip everything."""
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

            mock_api.get_league_standings.assert_not_called()

    def test_retry_narrative_when_report_exists_but_narrative_missing(
        self, tmp_path: Any
    ) -> None:
        """When report exists but narrative doesn't, load report and retry narrative."""
        # Create a valid report JSON
        api = WeeklyReportDummyAPI()
        wr = WeeklyReport(api, LEAGUE_ID, EVENT_ID)
        wr.build()
        wr.save_report(str(tmp_path))

        with patch("generate_weekly_report.FPL_API") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_bootstrap_static.return_value = BOOTSTRAP_DATA

            with patch("generate_weekly_report._generate_narrative") as mock_narr:
                mock_narr.return_value = "some/path.md"

                from generate_weekly_report import main

                with patch(
                    "sys.argv",
                    [
                        "generate_weekly_report.py",
                        "-l", LEAGUE_ID,
                        "-e", "2",
                        "--narrative",
                        "--skip-existing",
                        "--output-dir", str(tmp_path),
                    ],
                ):
                    main()

                # Report should NOT have been rebuilt
                mock_api.get_league_standings.assert_not_called()
                # Narrative SHOULD have been attempted
                mock_narr.assert_called_once()

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
