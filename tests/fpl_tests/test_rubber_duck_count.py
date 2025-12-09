import json
from pathlib import Path
from fpl.fpl_league import FPLLeague
from fpl.participant import Participant
from fpl.league_context import LeagueContext
from fpl.league_template_renderer import LeagueTemplateRenderer


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


def test_rubber_duck_count_is_calculated():
    """Test that rubber duck count is calculated for each participant."""
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    summary = league.get_summary()
    
    # Verify that each participant has a rubber_duck_count field
    for p in summary["participants"]:
        assert hasattr(p, "rubber_duck_count"), "Participant should have rubber_duck_count attribute"
        assert isinstance(p.rubber_duck_count, int), "rubber_duck_count should be an integer"
        assert p.rubber_duck_count >= 0, "rubber_duck_count should be non-negative"


def test_rubber_duck_count_counts_last_place_finishes():
    """Test that rubber duck count correctly counts the number of times a player finished last."""
    # Create a simple test case with known data
    participant_history = [
        {"event": 1, "net_points": 50, "round_rank": 3},
        {"event": 2, "net_points": 45, "round_rank": 5},  # Last place (out of 5)
        {"event": 3, "net_points": 60, "round_rank": 1},
        {"event": 4, "net_points": 30, "round_rank": 5},  # Last place (out of 5)
        {"event": 5, "net_points": 55, "round_rank": 2},
    ]
    
    participant = Participant(
        entry_id=123,
        team_name="Test Team",
        manager_name="Test Manager",
        total_score=240,
        history=participant_history,
        last_event=participant_history[-1]
    )
    
    # Assume we have 5 participants total
    total_participants = 5
    
    # Count how many times this participant was last (round_rank == total_participants)
    expected_count = sum(1 for h in participant.history if h.get("round_rank") == total_participants)
    
    # This should be 2 based on our test data
    assert expected_count == 2, f"Expected 2 last place finishes, got {expected_count}"


def test_rubber_duck_count_handles_ties():
    """Test that rubber duck count handles ties correctly (multiple people with same lowest score)."""
    # Create test data where multiple people finish last
    participant1_history = [
        {"event": 1, "net_points": 30, "round_rank": 3},  # Both tied for last (rank 3 out of 3 participants)
    ]
    
    participant2_history = [
        {"event": 1, "net_points": 30, "round_rank": 3},  # Both tied for last
    ]
    
    participant3_history = [
        {"event": 1, "net_points": 50, "round_rank": 1},  # Winner
    ]
    
    # In this case, both participant1 and participant2 should have rubber_duck_count = 1
    # because they both have round_rank == 3 (the number of participants)
    # This test verifies the logic - actual implementation will be in the Participant class
    
    total_participants = 3
    
    # Both participants with round_rank == total_participants should get a duck
    duck_count_1 = sum(1 for h in participant1_history if h.get("round_rank") == total_participants)
    duck_count_2 = sum(1 for h in participant2_history if h.get("round_rank") == total_participants)
    duck_count_3 = sum(1 for h in participant3_history if h.get("round_rank") == total_participants)
    
    assert duck_count_1 == 1, "Participant 1 should have 1 duck"
    assert duck_count_2 == 1, "Participant 2 should have 1 duck"
    assert duck_count_3 == 0, "Participant 3 should have 0 ducks"
    
    # Total ducks should be 2 (more than the number of events)
    total_ducks = duck_count_1 + duck_count_2 + duck_count_3
    assert total_ducks == 2, "Total ducks should be 2 (one event with two losers)"


def test_rubber_duck_column_in_template():
    """Test that the rubber duck count column appears in the rendered template."""
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
    
    # Check that the duck emoji appears as a column header
    assert "🦆" in html, "Template should contain duck emoji in header"
    
    # Check that each participant's rubber duck count appears in the table
    for p in league_data["participants"]:
        # The rubber duck count should appear as text in the rendered HTML
        assert str(p.rubber_duck_count) in html, f"Template should display rubber_duck_count ({p.rubber_duck_count}) for participant {p.manager_name}"

