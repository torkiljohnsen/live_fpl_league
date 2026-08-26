"""Tests for weekly report award calculation functions."""

from collections import Counter

from fpl.weekly_report_stats import (
    _SCORE_FAMILY_KINDS,
    get_bench_disasters,
    get_biggest_rank_fall,
    get_biggest_rank_rise,
    get_captain_summary,
    get_captain_that_would_have_won,
    get_chip_tracker,
    get_chip_usage,
    get_chips_played_to_date,
    get_chips_remaining,
    get_differentials,
    get_head_to_head,
    get_highest_gameweek_scorer,
    get_hit_takers,
    get_lowest_gameweek_scorer,
    get_records,
    get_streaks,
    get_transfer_impact,
    rank_storylines,
)


def _make_participant(
    name: str = "Test",
    net_points: int = 50,
    event_total: int = 55,
    team_name: str = "Test FC",
    league_rank: int = 1,
    league_rank_previous: int = 1,
    league_rank_change: int = 0,
    bench_points: int = 0,
    chip_played: str | None = None,
    captain: dict | None = None,
    transfers: list | None = None,
    transfer_cost: int = 0,
) -> dict:
    """Build a minimal participant dict for testing stat functions."""
    return {
        "player_first_name": name,
        "team_name": team_name,
        "net_points": net_points,
        "event_total": event_total,
        "league_rank": league_rank,
        "league_rank_previous": league_rank_previous,
        "league_rank_change": league_rank_change,
        "bench_points": bench_points,
        "chip_played": chip_played,
        "captain": captain or {"name": "Salah", "points": 10},
        "transfers": transfers or [],
        "transfer_cost": transfer_cost,
    }


# --- get_highest_gameweek_scorer ---


class TestHighestGameweekScorer:
    def test_returns_highest_scorer(self):
        participants = [
            _make_participant(name="Alice", net_points=80),
            _make_participant(name="Bob", net_points=45),
            _make_participant(name="Charlie", net_points=62),
        ]
        result = get_highest_gameweek_scorer(participants)
        assert result is not None
        assert result["player_name"] == "Alice"
        assert result["points"] == 80

    def test_returns_none_for_empty_list(self):
        assert get_highest_gameweek_scorer([]) is None

    def test_single_participant(self):
        result = get_highest_gameweek_scorer([_make_participant(name="Solo", net_points=33)])
        assert result is not None
        assert result["player_name"] == "Solo"
        assert result["points"] == 33

    def test_tie_returns_one(self):
        participants = [
            _make_participant(name="Alice", net_points=60),
            _make_participant(name="Bob", net_points=60),
        ]
        result = get_highest_gameweek_scorer(participants)
        assert result is not None
        assert result["points"] == 60


# --- get_lowest_gameweek_scorer ---


class TestLowestGameweekScorer:
    def test_returns_lowest_scorer(self):
        participants = [
            _make_participant(name="Alice", net_points=80),
            _make_participant(name="Bob", net_points=25),
            _make_participant(name="Charlie", net_points=62),
        ]
        result = get_lowest_gameweek_scorer(participants)
        assert result is not None
        assert result["player_name"] == "Bob"
        assert result["points"] == 25

    def test_returns_none_for_empty_list(self):
        assert get_lowest_gameweek_scorer([]) is None

    def test_negative_net_points(self):
        participants = [
            _make_participant(name="Alice", net_points=40),
            _make_participant(name="Bob", net_points=-4),
        ]
        result = get_lowest_gameweek_scorer(participants)
        assert result is not None
        assert result["player_name"] == "Bob"
        assert result["points"] == -4


# --- get_biggest_rank_rise ---


class TestBiggestRankRise:
    def test_returns_biggest_rise(self):
        participants = [
            _make_participant(name="Alice", league_rank=2, league_rank_previous=5, league_rank_change=3),
            _make_participant(name="Bob", league_rank=4, league_rank_previous=6, league_rank_change=2),
        ]
        result = get_biggest_rank_rise(participants)
        assert result is not None
        assert result["player_name"] == "Alice"
        assert result["change"] == 3
        assert result["old_rank"] == 5
        assert result["new_rank"] == 2

    def test_returns_none_for_empty_list(self):
        assert get_biggest_rank_rise([]) is None

    def test_returns_none_when_no_change_above_threshold(self):
        participants = [
            _make_participant(name="Alice", league_rank_change=1),
            _make_participant(name="Bob", league_rank_change=0),
        ]
        assert get_biggest_rank_rise(participants) is None

    def test_threshold_boundary_at_exactly_2(self):
        participants = [
            _make_participant(name="Alice", league_rank=3, league_rank_previous=5, league_rank_change=2),
        ]
        result = get_biggest_rank_rise(participants)
        assert result is not None
        assert result["player_name"] == "Alice"
        assert result["change"] == 2

    def test_ignores_negative_changes(self):
        participants = [
            _make_participant(name="Alice", league_rank_change=-3),
        ]
        assert get_biggest_rank_rise(participants) is None


# --- get_biggest_rank_fall ---


class TestBiggestRankFall:
    def test_returns_biggest_fall(self):
        participants = [
            _make_participant(name="Alice", league_rank=6, league_rank_previous=3, league_rank_change=-3),
            _make_participant(name="Bob", league_rank=5, league_rank_previous=3, league_rank_change=-2),
        ]
        result = get_biggest_rank_fall(participants)
        assert result is not None
        assert result["player_name"] == "Alice"
        assert result["change"] == -3
        assert result["old_rank"] == 3
        assert result["new_rank"] == 6

    def test_returns_none_for_empty_list(self):
        assert get_biggest_rank_fall([]) is None

    def test_returns_none_when_no_fall_above_threshold(self):
        participants = [
            _make_participant(name="Alice", league_rank_change=-1),
            _make_participant(name="Bob", league_rank_change=0),
        ]
        assert get_biggest_rank_fall(participants) is None

    def test_threshold_boundary_at_exactly_minus_2(self):
        participants = [
            _make_participant(name="Alice", league_rank=5, league_rank_previous=3, league_rank_change=-2),
        ]
        result = get_biggest_rank_fall(participants)
        assert result is not None
        assert result["player_name"] == "Alice"
        assert result["change"] == -2

    def test_ignores_positive_changes(self):
        participants = [
            _make_participant(name="Alice", league_rank_change=3),
        ]
        assert get_biggest_rank_fall(participants) is None


# --- #35: rank rise/fall are suppressed in early gameweeks ---


class TestRankAwardsEarlyGameweekDamping:
    def test_gw1_suppresses_rise_even_with_large_change(self):
        participants = [
            _make_participant(
                name="Alice", league_rank=1, league_rank_previous=10, league_rank_change=9
            ),
        ]
        assert get_biggest_rank_rise(participants, event_id=1) is None

    def test_gw1_suppresses_fall_even_with_large_change(self):
        participants = [
            _make_participant(
                name="Alice", league_rank=10, league_rank_previous=1, league_rank_change=-9
            ),
        ]
        assert get_biggest_rank_fall(participants, event_id=1) is None

    def test_no_previous_rank_skips_candidate_regardless_of_event_id(self):
        """A previous rank of 0 (the GW1 artifact) is never a real fall,
        even outside GW1 — e.g. a manager who joined the league mid-season."""
        participants = [
            _make_participant(
                name="Alice", league_rank=10, league_rank_previous=0, league_rank_change=-10
            ),
        ]
        assert get_biggest_rank_fall(participants, event_id=7) is None
        assert get_biggest_rank_rise(participants, event_id=7) is None

    def test_gw2_to_5_requires_change_of_at_least_3(self):
        participants = [
            _make_participant(
                name="Alice", league_rank=3, league_rank_previous=5, league_rank_change=2
            ),
        ]
        assert get_biggest_rank_rise(participants, event_id=3) is None
        assert get_biggest_rank_fall(participants, event_id=3) is None

    def test_gw2_to_5_change_of_3_is_reported(self):
        participants = [
            _make_participant(
                name="Alice", league_rank=2, league_rank_previous=5, league_rank_change=3
            ),
        ]
        result = get_biggest_rank_rise(participants, event_id=4)
        assert result is not None
        assert result["player_name"] == "Alice"

    def test_gw6_reverts_to_change_of_2(self):
        participants = [
            _make_participant(
                name="Alice", league_rank=3, league_rank_previous=5, league_rank_change=2
            ),
        ]
        result = get_biggest_rank_rise(participants, event_id=6)
        assert result is not None
        assert result["player_name"] == "Alice"

    def test_no_event_id_preserves_default_threshold_of_2(self):
        """Existing callers that don't pass event_id keep today's behaviour."""
        participants = [
            _make_participant(
                name="Alice", league_rank=3, league_rank_previous=5, league_rank_change=2
            ),
        ]
        result = get_biggest_rank_rise(participants)
        assert result is not None


# --- get_bench_disasters ---


class TestBenchDisasters:
    def test_returns_bench_disaster(self):
        participants = [
            _make_participant(name="Alice", bench_points=25, event_total=60),
            _make_participant(name="Bob", bench_points=5),
        ]
        result = get_bench_disasters(participants)
        assert len(result) == 1
        assert result[0]["player_name"] == "Alice"
        assert result[0]["bench_points"] == 25
        assert result[0]["event_total"] == 60

    def test_returns_empty_for_empty_list(self):
        assert get_bench_disasters([]) == []

    def test_excludes_bench_boost_chip(self):
        participants = [
            _make_participant(name="Alice", bench_points=30, chip_played="bboost"),
        ]
        assert get_bench_disasters(participants) == []

    def test_threshold_boundary_at_19_excluded(self):
        participants = [
            _make_participant(name="Alice", bench_points=19),
        ]
        assert get_bench_disasters(participants) == []

    def test_threshold_boundary_at_20_included(self):
        participants = [
            _make_participant(name="Alice", bench_points=20),
        ]
        result = get_bench_disasters(participants)
        assert len(result) == 1
        assert result[0]["player_name"] == "Alice"

    def test_custom_threshold(self):
        participants = [
            _make_participant(name="Alice", bench_points=15),
        ]
        result = get_bench_disasters(participants, threshold=15)
        assert len(result) == 1

    def test_multiple_disasters(self):
        participants = [
            _make_participant(name="Alice", bench_points=25),
            _make_participant(name="Bob", bench_points=22),
            _make_participant(name="Charlie", bench_points=10),
        ]
        result = get_bench_disasters(participants)
        assert len(result) == 2


# --- get_transfer_impact ---


class TestTransferImpact:
    def test_returns_best_and_worst(self):
        participants = [
            _make_participant(
                name="Alice",
                transfers=[{"player_in_points": 12, "player_out_points": 2}],
                transfer_cost=0,
            ),
            _make_participant(
                name="Bob",
                transfers=[{"player_in_points": 1, "player_out_points": 8}],
                transfer_cost=0,
            ),
        ]
        result = get_transfer_impact(participants)
        assert result is not None
        assert result["best"]["player_name"] == "Alice"
        assert result["best"]["net_gain"] == 10
        assert result["worst"]["player_name"] == "Bob"
        assert result["worst"]["net_loss"] == -7

    def test_returns_none_for_empty_list(self):
        assert get_transfer_impact([]) is None

    def test_returns_none_when_no_transfers(self):
        participants = [
            _make_participant(name="Alice", transfers=[]),
            _make_participant(name="Bob", transfers=[]),
        ]
        assert get_transfer_impact(participants) is None

    def test_includes_hit_cost(self):
        participants = [
            _make_participant(
                name="Alice",
                transfers=[{"player_in_points": 10, "player_out_points": 5}],
                transfer_cost=4,
            ),
        ]
        result = get_transfer_impact(participants)
        assert result is not None
        # Net = (10 - 5) - 4 = 1
        assert result["best"]["net_gain"] == 1

    def test_multiple_transfers(self):
        participants = [
            _make_participant(
                name="Alice",
                transfers=[
                    {"player_in_points": 8, "player_out_points": 2},
                    {"player_in_points": 3, "player_out_points": 6},
                ],
                transfer_cost=4,
            ),
        ]
        result = get_transfer_impact(participants)
        assert result is not None
        # Net = (8-2) + (3-6) - 4 = 6 + (-3) - 4 = -1
        assert result["best"]["net_gain"] == -1

    def test_single_participant_is_both_best_and_worst(self):
        participants = [
            _make_participant(
                name="Alice",
                transfers=[{"player_in_points": 5, "player_out_points": 3}],
                transfer_cost=0,
            ),
        ]
        result = get_transfer_impact(participants)
        assert result is not None
        assert result["best"]["player_name"] == "Alice"
        assert result["worst"]["player_name"] == "Alice"


# --- get_captain_summary ---


class TestCaptainSummary:
    def test_returns_summary(self):
        participants = [
            _make_participant(name="Alice", captain={"name": "Salah", "points": 20}),
            _make_participant(name="Bob", captain={"name": "Salah", "points": 20}),
            _make_participant(name="Charlie", captain={"name": "Haaland", "points": 4}),
        ]
        result = get_captain_summary(participants)
        assert result["most_popular"]["player"] == "Salah"
        assert result["most_popular"]["count"] == 2
        assert result["best_pick"]["manager"] == "Alice"  # or Bob, both 20
        assert result["best_pick"]["points"] == 20
        assert result["worst_pick"]["manager"] == "Charlie"
        assert result["worst_pick"]["points"] == 4

    def test_returns_empty_for_empty_list(self):
        assert get_captain_summary([]) == {}

    def test_single_participant(self):
        participants = [
            _make_participant(name="Alice", captain={"name": "Salah", "points": 15}),
        ]
        result = get_captain_summary(participants)
        assert result["most_popular"]["player"] == "Salah"
        assert result["most_popular"]["count"] == 1
        assert result["best_pick"]["manager"] == "Alice"
        assert result["worst_pick"]["manager"] == "Alice"

    def test_all_different_captains(self):
        participants = [
            _make_participant(name="Alice", captain={"name": "Salah", "points": 12}),
            _make_participant(name="Bob", captain={"name": "Haaland", "points": 8}),
            _make_participant(name="Charlie", captain={"name": "Palmer", "points": 16}),
        ]
        result = get_captain_summary(participants)
        assert result["most_popular"]["count"] == 1
        assert result["best_pick"]["manager"] == "Charlie"
        assert result["best_pick"]["points"] == 16
        assert result["worst_pick"]["manager"] == "Bob"
        assert result["worst_pick"]["points"] == 8

    def test_captain_substitution_uses_effective_points(self):
        """When a captain didn't play, effective_points should be used for best/worst."""
        participants = [
            _make_participant(
                name="Alice",
                captain={
                    "name": "Haaland",
                    "points": 0,
                    "did_not_play": True,
                    "effective_captain": "Salah",
                    "effective_points": 24,
                },
            ),
            _make_participant(
                name="Bob",
                captain={"name": "Palmer", "points": 16},
            ),
            _make_participant(
                name="Charlie",
                captain={"name": "Saka", "points": 4},
            ),
        ]
        result = get_captain_summary(participants)
        # Alice's effective_points (24) should make her the best pick
        assert result["best_pick"]["manager"] == "Alice"
        assert result["best_pick"]["points"] == 24
        # Charlie's 4 is worst
        assert result["worst_pick"]["manager"] == "Charlie"
        assert result["worst_pick"]["points"] == 4

    def test_vice_captain_substitutions_listed(self):
        """Managers whose captain was subbed should appear in vice_captain_substitutions."""
        participants = [
            _make_participant(
                name="Alice",
                captain={
                    "name": "Haaland",
                    "points": 0,
                    "did_not_play": True,
                    "effective_captain": "Salah",
                    "effective_points": 24,
                },
            ),
            _make_participant(
                name="Bob",
                captain={"name": "Palmer", "points": 16},
            ),
        ]
        result = get_captain_summary(participants)
        subs = result["vice_captain_substitutions"]
        assert len(subs) == 1
        assert subs[0]["manager"] == "Alice"
        assert subs[0]["original_captain"] == "Haaland"
        assert subs[0]["effective_captain"] == "Salah"
        assert subs[0]["effective_points"] == 24

    def test_no_substitutions_when_captains_played(self):
        """No vice_captain_substitutions when all captains played."""
        participants = [
            _make_participant(name="Alice", captain={"name": "Salah", "points": 20}),
            _make_participant(name="Bob", captain={"name": "Haaland", "points": 16}),
        ]
        result = get_captain_summary(participants)
        assert result["vice_captain_substitutions"] == []


# --- get_chip_usage ---


class TestChipUsage:
    def test_returns_chip_users(self):
        participants = [
            _make_participant(name="Alice", chip_played="wildcard", net_points=70),
            _make_participant(name="Bob", chip_played=None),
        ]
        result = get_chip_usage(participants)
        assert len(result) == 1
        assert result[0]["player_name"] == "Alice"
        assert result[0]["chip"] == "wildcard"
        assert result[0]["points"] == 70

    def test_returns_empty_when_no_chips(self):
        participants = [
            _make_participant(name="Alice"),
            _make_participant(name="Bob"),
        ]
        assert get_chip_usage(participants) == []

    def test_returns_empty_for_empty_list(self):
        assert get_chip_usage([]) == []

    def test_multiple_chip_users(self):
        participants = [
            _make_participant(name="Alice", chip_played="wildcard", net_points=70),
            _make_participant(name="Bob", chip_played="3xc", net_points=90),
            _make_participant(name="Charlie"),
        ]
        result = get_chip_usage(participants)
        assert len(result) == 2
        chips = {r["player_name"]: r["chip"] for r in result}
        assert chips["Alice"] == "wildcard"
        assert chips["Bob"] == "3xc"


# --- get_hit_takers ---


class TestHitTakers:
    def test_returns_hit_takers(self):
        participants = [
            _make_participant(name="Alice", transfer_cost=8, net_points=50),
            _make_participant(name="Bob", transfer_cost=0),
        ]
        result = get_hit_takers(participants)
        assert len(result) == 1
        assert result[0]["player_name"] == "Alice"
        assert result[0]["cost"] == 8
        assert result[0]["net_points"] == 50

    def test_returns_empty_when_no_hits(self):
        participants = [
            _make_participant(name="Alice", transfer_cost=0),
            _make_participant(name="Bob", transfer_cost=0),
        ]
        assert get_hit_takers(participants) == []

    def test_returns_empty_for_empty_list(self):
        assert get_hit_takers([]) == []

    def test_multiple_hit_takers(self):
        participants = [
            _make_participant(name="Alice", transfer_cost=4, net_points=60),
            _make_participant(name="Bob", transfer_cost=8, net_points=45),
            _make_participant(name="Charlie", transfer_cost=0),
        ]
        result = get_hit_takers(participants)
        assert len(result) == 2
        costs = {r["player_name"]: r["cost"] for r in result}
        assert costs["Alice"] == 4
        assert costs["Bob"] == 8


# ---------------------------------------------------------------------------
# New data angles (issue #40 workstream F)
# ---------------------------------------------------------------------------


def _make_full_participant(
    name: str,
    entry_id: int,
    event_total: int = 50,
    squad: list[dict] | None = None,
    captain_element_id: int = 1,
    captain_did_not_play: bool = False,
    effective_captain: str | None = None,
    bench_points: int = 0,
    transfer_cost: int = 0,
    chip_played: str | None = None,
    chips_remaining: list[str] | None = None,
    chips_played_season: list[dict] | None = None,
    event_percentile: float | None = None,
    overall_percentile: float | None = None,
    points_per_starter: float | None = None,
) -> dict:
    captain: dict = {"name": "Salah", "element_id": captain_element_id}
    if captain_did_not_play:
        captain["did_not_play"] = True
        captain["effective_captain"] = effective_captain
    return {
        "entry_id": entry_id,
        "player_first_name": name,
        "event_total": event_total,
        "squad": squad or [],
        "captain": captain,
        "bench_points": bench_points,
        "transfer_cost": transfer_cost,
        "chip_played": chip_played,
        "chips_remaining": chips_remaining or [],
        "chips_played_season": chips_played_season or [],
        "event_percentile": event_percentile,
        "overall_percentile": overall_percentile,
        "points_per_starter": points_per_starter,
    }


class TestChipsRemaining:
    BOOTSTRAP_CHIPS = [
        {"name": "wildcard", "start_event": 1, "stop_event": 19},
        {"name": "freehit", "start_event": 1, "stop_event": 19},
        {"name": "bboost", "start_event": 1, "stop_event": 19},
        {"name": "3xc", "start_event": 1, "stop_event": 19},
        {"name": "wildcard", "start_event": 20, "stop_event": 38},
        {"name": "freehit", "start_event": 20, "stop_event": 38},
        {"name": "bboost", "start_event": 20, "stop_event": 38},
        {"name": "3xc", "start_event": 20, "stop_event": 38},
    ]

    def test_all_available_when_none_played(self):
        result = get_chips_remaining(self.BOOTSTRAP_CHIPS, [], 5)
        assert set(result) == {"wildcard", "freehit", "bboost", "3xc"}

    def test_excludes_chip_played_this_window(self):
        played = [{"name": "wildcard", "event": 3}]
        result = get_chips_remaining(self.BOOTSTRAP_CHIPS, played, 5)
        assert "wildcard" not in result
        assert set(result) == {"freehit", "bboost", "3xc"}

    def test_second_half_window_is_independent(self):
        """A chip played in the first half doesn't count against the
        second half's allowance."""
        played = [{"name": "wildcard", "event": 3}]
        result = get_chips_remaining(self.BOOTSTRAP_CHIPS, played, 25)
        assert "wildcard" in result

    def test_chip_played_in_other_window_still_available(self):
        played = [{"name": "wildcard", "event": 25}]
        result = get_chips_remaining(self.BOOTSTRAP_CHIPS, played, 5)
        assert "wildcard" in result

    def test_empty_bootstrap_chips(self):
        assert get_chips_remaining([], [], 5) == []


class TestChipsPlayedToDate:
    def test_filters_by_event(self):
        played = [
            {"name": "wildcard", "event": 2},
            {"name": "bboost", "event": 10},
        ]
        result = get_chips_played_to_date(played, 5)
        assert result == [{"name": "wildcard", "event": 2}]

    def test_includes_current_event(self):
        played = [{"name": "wildcard", "event": 5}]
        result = get_chips_played_to_date(played, 5)
        assert result == [{"name": "wildcard", "event": 5}]

    def test_empty_when_none_played(self):
        assert get_chips_played_to_date([], 5) == []


class TestHeadToHead:
    def test_beat_and_lost_to_this_gw(self):
        participants = [
            _make_full_participant("Alice", 1, event_total=80),
            _make_full_participant("Bob", 2, event_total=50),
            _make_full_participant("Charlie", 3, event_total=65),
        ]
        result = get_head_to_head(participants)
        by_name = {r["player_name"]: r for r in result}
        assert by_name["Alice"]["beat"] == 2
        assert by_name["Alice"]["lost_to"] == 0
        assert by_name["Bob"]["beat"] == 0
        assert by_name["Bob"]["lost_to"] == 2
        assert by_name["Charlie"]["beat"] == 1
        assert by_name["Charlie"]["lost_to"] == 1

    def test_no_histories_gives_zero_season_record(self):
        participants = [_make_full_participant("Alice", 1, event_total=50)]
        result = get_head_to_head(participants)
        assert result[0]["season_record"] == {"wins": 0, "losses": 0}

    def test_season_record_from_histories(self):
        participants = [
            _make_full_participant("Alice", 1, event_total=50),
            _make_full_participant("Bob", 2, event_total=40),
        ]
        histories = {
            1: [{"event": 1, "points": 60}, {"event": 2, "points": 50}],
            2: [{"event": 1, "points": 40}, {"event": 2, "points": 40}],
        }
        result = get_head_to_head(participants, histories)
        by_name = {r["player_name"]: r for r in result}
        # Alice beat Bob both GWs (60>40, 50>40)
        assert by_name["Alice"]["season_record"] == {"wins": 2, "losses": 0}
        assert by_name["Bob"]["season_record"] == {"wins": 0, "losses": 2}

    def test_empty_participants(self):
        assert get_head_to_head([]) == []


class TestDifferentials:
    def test_owned_by_exactly_one_manager(self):
        participants = [
            _make_full_participant(
                "Alice", 1,
                squad=[
                    {"element_id": 1, "name": "Salah", "points": 12},
                    {"element_id": 2, "name": "Haaland", "points": 8},
                ],
            ),
            _make_full_participant(
                "Bob", 2,
                squad=[
                    {"element_id": 1, "name": "Salah", "points": 12},
                    {"element_id": 3, "name": "Palmer", "points": 20},
                ],
            ),
        ]
        result = get_differentials(participants)
        # Salah owned by both -> not a differential; Haaland/Palmer are
        names = {d["player_name"] for d in result["top"]}
        assert "Salah" not in names
        assert "Haaland" in names
        assert "Palmer" in names

    def test_sorted_by_points_desc(self):
        participants = [
            _make_full_participant(
                "Alice", 1,
                squad=[
                    {"element_id": 1, "name": "Low", "points": 2},
                    {"element_id": 2, "name": "High", "points": 20},
                ],
            ),
        ]
        result = get_differentials(participants)
        assert [d["player_name"] for d in result["top"]] == ["High", "Low"]

    def test_top_capped_at_5_bottom_at_3(self):
        squad = [
            {"element_id": i, "name": f"P{i}", "points": i} for i in range(10)
        ]
        participants = [_make_full_participant("Alice", 1, squad=squad)]
        result = get_differentials(participants)
        assert len(result["top"]) == 5
        assert len(result["bottom"]) == 3

    def test_no_differentials(self):
        participants = [
            _make_full_participant(
                "Alice", 1, squad=[{"element_id": 1, "name": "Salah", "points": 12}]
            ),
            _make_full_participant(
                "Bob", 2, squad=[{"element_id": 1, "name": "Salah", "points": 12}]
            ),
        ]
        result = get_differentials(participants)
        assert result == {"top": [], "bottom": []}


class TestCaptainThatWouldHaveWon:
    def test_finds_highest_scoring_player(self):
        participants = [
            _make_full_participant(
                "Alice", 1, captain_element_id=1,
                squad=[
                    {"element_id": 1, "name": "Salah", "points": 12},
                    {"element_id": 2, "name": "Palmer", "points": 20},
                ],
            ),
        ]
        result = get_captain_that_would_have_won(participants)
        assert result is not None
        assert result["player_name"] == "Palmer"
        assert result["points"] == 20
        assert result["captained_by"] == 0

    def test_counts_managers_who_captained_him(self):
        participants = [
            _make_full_participant(
                "Alice", 1, captain_element_id=2,
                squad=[{"element_id": 2, "name": "Palmer", "points": 20}],
            ),
            _make_full_participant(
                "Bob", 2, captain_element_id=2,
                squad=[{"element_id": 2, "name": "Palmer", "points": 20}],
            ),
            _make_full_participant(
                "Charlie", 3, captain_element_id=1,
                squad=[{"element_id": 2, "name": "Palmer", "points": 20}],
            ),
        ]
        result = get_captain_that_would_have_won(participants)
        assert result is not None
        assert result["captained_by"] == 2

    def test_empty_participants(self):
        assert get_captain_that_would_have_won([]) is None


class TestStreaks:
    def test_above_average_streak_reported_at_3(self):
        histories = {
            1: [
                {"event": 1, "points": 80, "overall_rank": 100},
                {"event": 2, "points": 80, "overall_rank": 90},
                {"event": 3, "points": 80, "overall_rank": 80},
            ],
            2: [
                {"event": 1, "points": 20, "overall_rank": 900},
                {"event": 2, "points": 20, "overall_rank": 900},
                {"event": 3, "points": 20, "overall_rank": 900},
            ],
        }
        participants = [
            _make_full_participant("Alice", 1),
            _make_full_participant("Bob", 2),
        ]
        result = get_streaks(participants, histories)
        above_avg = [s for s in result if s["kind"] == "above_average"]
        assert len(above_avg) == 1
        assert above_avg[0]["player_name"] == "Alice"
        assert above_avg[0]["length"] == 3

    def test_streak_below_3_not_reported(self):
        histories = {
            1: [
                {"event": 1, "points": 80, "overall_rank": 100},
                {"event": 2, "points": 20, "overall_rank": 900},
            ],
            2: [
                {"event": 1, "points": 20, "overall_rank": 900},
                {"event": 2, "points": 80, "overall_rank": 100},
            ],
        }
        participants = [
            _make_full_participant("Alice", 1),
            _make_full_participant("Bob", 2),
        ]
        result = get_streaks(participants, histories)
        assert result == []

    def test_round_wins_streak(self):
        histories = {
            1: [
                {"event": 1, "points": 90, "overall_rank": 100},
                {"event": 2, "points": 90, "overall_rank": 100},
                {"event": 3, "points": 90, "overall_rank": 100},
            ],
            2: [
                {"event": 1, "points": 10, "overall_rank": 900},
                {"event": 2, "points": 10, "overall_rank": 900},
                {"event": 3, "points": 10, "overall_rank": 900},
            ],
        }
        participants = [
            _make_full_participant("Alice", 1),
            _make_full_participant("Bob", 2),
        ]
        result = get_streaks(participants, histories)
        wins = [s for s in result if s["kind"] == "round_wins"]
        assert len(wins) == 1
        assert wins[0]["player_name"] == "Alice"
        assert wins[0]["length"] == 3

    def test_green_arrows_streak(self):
        histories = {
            1: [
                {"event": 1, "points": 50, "overall_rank": 1000},
                {"event": 2, "points": 50, "overall_rank": 500},
                {"event": 3, "points": 50, "overall_rank": 100},
                {"event": 4, "points": 50, "overall_rank": 50},
            ],
        }
        participants = [_make_full_participant("Alice", 1)]
        result = get_streaks(participants, histories)
        arrows = [s for s in result if s["kind"] == "green_arrows"]
        assert len(arrows) == 1
        assert arrows[0]["length"] == 3

    def test_no_histories_returns_empty(self):
        participants = [_make_full_participant("Alice", 1)]
        assert get_streaks(participants, {}) == []


class TestRecords:
    def test_best_and_worst(self):
        histories = {
            1: [{"event": 1, "points": 90}, {"event": 2, "points": 40}],
            2: [{"event": 1, "points": 30}, {"event": 2, "points": 60}],
        }
        participants = [
            _make_full_participant("Alice", 1),
            _make_full_participant("Bob", 2),
        ]
        result = get_records(participants, histories)
        assert result["best"] == {"player_name": "Alice", "event_id": 1, "points": 90}
        assert result["worst"] == {"player_name": "Bob", "event_id": 1, "points": 30}

    def test_empty_histories(self):
        participants = [_make_full_participant("Alice", 1)]
        result = get_records(participants, {})
        assert result == {"best": None, "worst": None}


class TestChipTracker:
    def test_reads_participant_chip_fields(self):
        participants = [
            _make_full_participant(
                "Alice", 1,
                chips_remaining=["wildcard", "freehit"],
                chips_played_season=[{"name": "bboost", "event": 1}],
            ),
        ]
        result = get_chip_tracker(participants)
        assert result == [{
            "player_name": "Alice",
            "chips_remaining": ["wildcard", "freehit"],
            "chips_played": [{"name": "bboost", "event": 1}],
        }]

    def test_empty_participants(self):
        assert get_chip_tracker([]) == []


class TestRankStorylines:
    def _base_report(self, **overrides) -> dict:
        report = {
            "meta": {"event_id": 5, "is_golden": False},
            "global": {"average_score": 50},
            "standings": [
                _make_full_participant(
                    "Alice", 1, event_total=90, event_percentile=0.5,
                    overall_percentile=0.3, points_per_starter=8.0,
                ),
                _make_full_participant(
                    "Bob", 2, event_total=20, event_percentile=99.5,
                ),
            ],
            "awards": {},
            "angles": {"streaks": [], "records": {}},
        }
        report.update(overrides)
        return report

    def test_returns_at_most_6(self):
        report = self._base_report()
        result = rank_storylines(report)
        assert len(result) <= 6

    def test_sorted_descending_by_score(self):
        report = self._base_report()
        result = rank_storylines(report)
        scores = [s["score"] for s in result]
        assert scores == sorted(scores, reverse=True)

    def test_gw_rank_extreme_triggers(self):
        report = self._base_report()
        result = rank_storylines(report)
        kinds = {s["kind"] for s in result}
        assert "gw_rank_extreme" in kinds

    def test_below_half_average_triggers(self):
        report = self._base_report()
        result = rank_storylines(report)
        below = [s for s in result if s["kind"] == "score_far_below_average"]
        assert len(below) == 1
        assert below[0]["managers"] == ["Bob"]

    def test_summary_contains_numbers(self):
        report = self._base_report()
        result = rank_storylines(report)
        for s in result:
            assert any(ch.isdigit() for ch in s["summary"])

    def test_golden_winner_when_golden(self):
        report = self._base_report(meta={"event_id": 4, "is_golden": True})
        result = rank_storylines(report)
        kinds = {s["kind"] for s in result}
        assert "golden_winner" in kinds

    def test_empty_report(self):
        report = {
            "meta": {"event_id": 1, "is_golden": False},
            "global": {},
            "standings": [],
            "awards": {},
            "angles": {},
        }
        assert rank_storylines(report) == []


class TestChipsRemainingWindowNotYetOpen:
    def test_wildcard_opening_at_gw2_counts_as_available_at_gw1(self):
        chips = [
            {"name": "wildcard", "start_event": 2, "stop_event": 19},
            {"name": "wildcard", "start_event": 20, "stop_event": 38},
            {"name": "bboost", "start_event": 1, "stop_event": 19},
        ]
        assert get_chips_remaining(chips, [], 1) == ["wildcard", "bboost"]

    def test_second_half_window_not_counted_in_first_half(self):
        chips = [
            {"name": "3xc", "start_event": 1, "stop_event": 19},
            {"name": "3xc", "start_event": 20, "stop_event": 38},
        ]
        assert get_chips_remaining(chips, [{"name": "3xc", "event": 5}], 7) == []


class TestStorylinesPerManagerCap:
    def test_at_most_two_score_family_storylines_per_manager(self):
        report = {
            "meta": {"event_id": 1},
            "global": {"average_score": 50, "total_players": 1000},
            "standings": [
                {
                    "player_first_name": "A", "event_total": 120, "net_points": 120,
                    "event_percentile": 0.1, "overall_percentile": 0.1,
                    "chip_played": "bboost", "bench_points": 0, "transfer_cost": 0,
                    "captain": {}, "points_per_starter": 10.0,
                },
                {
                    "player_first_name": "B", "event_total": 51, "net_points": 51,
                    "event_percentile": 50.0, "overall_percentile": 50.0,
                    "chip_played": None, "bench_points": 25, "transfer_cost": 0,
                    "captain": {}, "points_per_starter": 4.6,
                },
            ],
            "awards": {"highest_scorer": {"player_name": "A", "points": 120},
                       "lowest_scorer": {"player_name": "B", "points": 51},
                       "biggest_rise": None, "biggest_fall": None,
                       "captain_summary": {}, "chip_usage": [], "hit_takers": [],
                       "bench_disasters": []},
            "angles": {"streaks": [], "records": {}},
        }
        result = rank_storylines(report)
        counts = Counter(
            n for s in result if s["kind"] in _SCORE_FAMILY_KINDS for n in s["managers"]
        )
        assert counts["A"] <= 2
        assert any("B" in s["managers"] for s in result)
