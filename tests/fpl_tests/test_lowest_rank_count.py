import json
from pathlib import Path

from fpl.fpl_league import FPLLeague
from fpl.league_context import LeagueContext
from fpl.league_template_renderer import LeagueTemplateRenderer
from fpl.participant import Participant
from fpl.rank_calculator import RankCalculator


class DummyAPI:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def get_bootstrap_static(self):
        return json.loads((self.data_dir / "bootstrap-static_sample.json").read_text(encoding="utf-8"))

    def get_league_standings(self, league_id):
        return json.loads((self.data_dir / f"leagues-classic_{league_id}_standings_sample.json").read_text(encoding="utf-8"))

    def get_team_history(self, team_id):
        return json.loads((self.data_dir / "entry_811114_history_sample.json").read_text(encoding="utf-8"))

    def get_team(self, team_id):
        return {}

    def get_team_picks(self, team_id, event_id):
        return {}


data_dir = Path(__file__).parent / "data_samples"
LEAGUE_ID = "1639886"


def test_lowest_rank_count_is_calculated():
    """Test that lowest rank count is calculated for each participant."""
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    participants = league.get_participants()

    # Verify that each participant has a lowest_rank_count field
    for p in participants:
        assert hasattr(p, "lowest_rank_count"), "Participant should have lowest_rank_count attribute"
        assert isinstance(p.lowest_rank_count, int), "lowest_rank_count should be an integer"
        assert p.lowest_rank_count >= 0, "lowest_rank_count should be non-negative"


def test_lowest_rank_count_counts_last_place_finishes():
    """Test that lowest rank count correctly counts the number of times a player finished last."""
    # This test uses sample data where all participants have the same scores
    # so they should all tie for last in each event they participated in
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    participants = league.get_participants()

    # In the sample data, all participants have identical scores, so they all tie for last
    # Each event should contribute to all participants' lowest_rank_count
    if participants:
        # All participants should have the same lowest_rank_count since they have identical scores
        first_count = participants[0].lowest_rank_count
        for p in participants:
            assert p.lowest_rank_count == first_count, "All participants should have same count in this test data"


def test_lowest_rank_count_handles_ties():
    """Test that lowest rank count handles ties correctly (multiple people with same lowest score)."""
    # Create a scenario where 2 participants tie for last place in an event
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=100,
        history=[
            {"event": 1, "net_points": 50, "total_points": 50}
        ],
        last_event={"event": 1, "net_points": 50, "total_points": 50}
    )

    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=100,
        history=[
            {"event": 1, "net_points": 50, "total_points": 50}
        ],
        last_event={"event": 1, "net_points": 50, "total_points": 50}
    )

    participant3 = Participant(
        entry_id=3, team_name="Team 3", manager_name="Player 3", total_score=120,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70}
        ],
        last_event={"event": 1, "net_points": 70, "total_points": 70}
    )

    participants = [participant1, participant2, participant3]

    # Apply ranks and calculate lowest rank counts
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_lowest_rank_counts(participants)

    # In this case, both participant1 and participant2 should have lowest_rank_count = 1
    assert participant1.lowest_rank_count == 1, "Participant1 should have lowest_rank_count = 1"
    assert participant2.lowest_rank_count == 1, "Participant2 should have lowest_rank_count = 1"
    assert participant3.lowest_rank_count == 0, "Participant3 should have lowest_rank_count = 0"


def test_lowest_rank_column_in_template():
    """Test that the lowest rank count column appears in the rendered template."""
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    league_data = league.get_summary()

    # Build the context
    logo_svg = "<svg></svg>"
    context = LeagueContext(
        league_data=league_data,
        league_join_code=None,
        logo_svg=logo_svg,
        dev_mode=True
    )

    # Render the template
    renderer = LeagueTemplateRenderer(context, "gw_history")
    template = renderer.env.get_template(renderer.get_template_name())
    html = template.render(**context.as_dict(), output_type="gw_history")

    # Check that the duck image appears as a column header
    assert 'The Duck liten.png' in html, "Template should contain duck image in header"
    assert 'alt="🦆"' in html, "Duck image should have duck emoji as alt text"

    # Check that each participant's lowest rank count appears in the table
    for p in league_data["participants"]:
        # The lowest rank count should appear as text in the rendered HTML
        count_text = str(p.lowest_rank_count)
        name_text = p.manager_name
        msg = f"Template should display lowest_rank_count ({count_text}) for {name_text}"
        assert count_text in html, msg


def test_duck_icons_appear_for_tied_losers():
    """Test that duck icons appear in cells when multiple participants tie for last place."""
    # Create test data with 2 participants tied for last in an event
    participants = [
        Participant(
            entry_id=1, team_name="Team A", manager_name="Alice", total_score=50,
            history=[{"event": 1, "net_points": 50, "total_points": 50, "overall_rank": 100}],
            last_event={"event": 1, "net_points": 50, "total_points": 50}
        ),
        Participant(
            entry_id=2, team_name="Team B", manager_name="Bob", total_score=50,
            history=[{"event": 1, "net_points": 50, "total_points": 50, "overall_rank": 100}],
            last_event={"event": 1, "net_points": 50, "total_points": 50}
        ),
        Participant(
            entry_id=3, team_name="Team C", manager_name="Carol", total_score=70,
            history=[{"event": 1, "net_points": 70, "total_points": 70, "overall_rank": 50}],
            last_event={"event": 1, "net_points": 70, "total_points": 70}
        ),
    ]

    # Apply ranks and calculate lowest rank counts
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_lowest_rank_counts(participants)

    # Build league data and context
    league_data = {
        "id": 12345,
        "name": "Test League",
        "participants": participants,
        "event_ids": [1],
        "finished_event_ids": [1],
        "current_event_id": 1,
        "is_current_finished": True,
        "generated_time": "2024-01-01T12:00:00Z"
    }

    logo_svg = "<svg></svg>"
    context = LeagueContext(
        league_data=league_data,
        league_join_code=None,
        logo_svg=logo_svg,
        dev_mode=False
    )

    # Render template
    renderer = LeagueTemplateRenderer(context, "gw_history")
    template = renderer.env.get_template(renderer.get_template_name())
    html = template.render(**context.as_dict(), output_type="gw_history")

    # Count occurrences of "is_loser" class - should be 2 (one for each tied loser)
    is_loser_count = html.count('is_loser')
    assert is_loser_count == 2, f"Expected 2 cells with 'is_loser' class (tied losers), but found {is_loser_count}"
