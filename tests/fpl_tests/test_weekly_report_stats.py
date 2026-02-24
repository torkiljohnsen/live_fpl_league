"""Tests for weekly report award calculation functions."""


from fpl.weekly_report_stats import (
    get_bench_disasters,
    get_biggest_rank_fall,
    get_biggest_rank_rise,
    get_captain_summary,
    get_chip_usage,
    get_highest_gameweek_scorer,
    get_hit_takers,
    get_lowest_gameweek_scorer,
    get_transfer_impact,
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
