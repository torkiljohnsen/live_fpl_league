import json
from pathlib import Path
from typing import Dict, Union
from fpl.fpl_league import FPLLeague
from fpl.participant import Participant
from fpl.league_context import LeagueContext
from fpl.league_template_renderer import LeagueTemplateRenderer
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


def test_win_count_is_calculated():
    """Test that win count is calculated for each participant."""
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    participants = league.get_participants()
    
    # Verify that each participant has win_count and golden_win_count fields
    for p in participants:
        assert hasattr(p, "win_count"), "Participant should have win_count attribute"
        assert isinstance(p.win_count, int), "win_count should be an integer"
        assert p.win_count >= 0, "win_count should be non-negative"
        
        assert hasattr(p, "golden_win_count"), "Participant should have golden_win_count attribute"
        assert isinstance(p.golden_win_count, int), "golden_win_count should be an integer"
        assert p.golden_win_count >= 0, "golden_win_count should be non-negative"
        
        # Golden wins should never exceed total wins
        assert p.golden_win_count <= p.win_count, "golden_win_count should not exceed win_count"


def test_sum_of_wins_is_correct():
    """Test that the sum of wins across all participants equals the number of gameweeks."""
    # Create test data where we know the wins
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=200,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70},
            {"event": 2, "net_points": 65, "total_points": 135},
        ],
        last_event={"event": 2, "net_points": 65, "total_points": 135}
    )
    
    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=180,
        history=[
            {"event": 1, "net_points": 60, "total_points": 60},
            {"event": 2, "net_points": 70, "total_points": 130},
        ],
        last_event={"event": 2, "net_points": 70, "total_points": 130}
    )
    
    participant3 = Participant(
        entry_id=3, team_name="Team 3", manager_name="Player 3", total_score=150,
        history=[
            {"event": 1, "net_points": 55, "total_points": 55},
            {"event": 2, "net_points": 55, "total_points": 110},
        ],
        last_event={"event": 2, "net_points": 55, "total_points": 110}
    )
    
    participants = [participant1, participant2, participant3]
    
    # Apply ranks and calculate win counts
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_win_counts(participants)
    
    # participant1 should win event 1 (70 points), participant2 should win event 2 (70 points)
    assert participant1.win_count == 1, "Participant1 should have 1 win"
    assert participant2.win_count == 1, "Participant2 should have 1 win"
    assert participant3.win_count == 0, "Participant3 should have 0 wins"
    
    # Sum of all wins should equal number of gameweeks (2)
    total_wins = sum(p.win_count for p in participants)
    assert total_wins == 2, f"Total wins should be 2, but got {total_wins}"


def test_sum_of_wins_with_ties():
    """Test that the sum of wins is correct when multiple winners tie for a gameweek."""
    # Create test data where 2 participants tie for first place in an event
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=100,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70}
        ],
        last_event={"event": 1, "net_points": 70, "total_points": 70}
    )
    
    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=100,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70}
        ],
        last_event={"event": 1, "net_points": 70, "total_points": 70}
    )
    
    participant3 = Participant(
        entry_id=3, team_name="Team 3", manager_name="Player 3", total_score=90,
        history=[
            {"event": 1, "net_points": 60, "total_points": 60}
        ],
        last_event={"event": 1, "net_points": 60, "total_points": 60}
    )
    
    participants = [participant1, participant2, participant3]
    
    # Apply ranks and calculate win counts
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_win_counts(participants)
    
    # Both participant1 and participant2 should have win_count = 1 (tied for first)
    assert participant1.win_count == 1, "Participant1 should have win_count = 1"
    assert participant2.win_count == 1, "Participant2 should have win_count = 1"
    assert participant3.win_count == 0, "Participant3 should have win_count = 0"
    
    # Sum of wins can exceed number of gameweeks when there are ties
    total_wins = sum(p.win_count for p in participants)
    assert total_wins == 2, f"Total wins should be 2 (both tied winners), but got {total_wins}"


def test_wins_include_all_gameweeks():
    """Test that wins include all gameweeks, not just the visible ones in the table.
    
    If we are in gameweek 20, the first 5 gameweeks are not shown in the table 
    (only last 15), but any wins from gameweeks 1-5 should be counted.
    """
    # Create test data with 20 gameweeks where a participant wins gameweek 1 and gameweek 20
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=1400,
        history=[
            {"event": i, "net_points": 70, "total_points": 70 * i}
            for i in range(1, 21)
        ],
        last_event={"event": 20, "net_points": 70, "total_points": 1400}
    )
    
    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=1200,
        history=[
            {"event": i, "net_points": 60, "total_points": 60 * i}
            for i in range(1, 21)
        ],
        last_event={"event": 20, "net_points": 60, "total_points": 1200}
    )
    
    participants = [participant1, participant2]
    
    # Apply ranks and calculate win counts
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_win_counts(participants)
    
    # participant1 wins all 20 gameweeks (always 70 > 60)
    assert participant1.win_count == 20, f"Participant1 should have 20 wins, but got {participant1.win_count}"
    assert participant2.win_count == 0, f"Participant2 should have 0 wins, but got {participant2.win_count}"
    
    # Check that the win count includes gameweeks that wouldn't be visible in the table
    # (gameweeks 1-5 are hidden when current gameweek is 20, but should still be counted)


def test_golden_gameweek_wins_are_counted():
    """Test that golden gameweek wins (divisible by 4) are counted separately."""
    # Create test data with wins on both regular and golden gameweeks
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=400,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70},   # Regular win
            {"event": 2, "net_points": 60, "total_points": 130},  # Not a win
            {"event": 3, "net_points": 65, "total_points": 195},  # Regular win
            {"event": 4, "net_points": 75, "total_points": 270},  # Golden gameweek win
            {"event": 5, "net_points": 70, "total_points": 340},  # Regular win
            {"event": 8, "net_points": 80, "total_points": 420},  # Golden gameweek win
        ],
        last_event={"event": 8, "net_points": 80, "total_points": 420}
    )
    
    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=350,
        history=[
            {"event": 1, "net_points": 60, "total_points": 60},
            {"event": 2, "net_points": 70, "total_points": 130},  # Win
            {"event": 3, "net_points": 55, "total_points": 185},
            {"event": 4, "net_points": 65, "total_points": 250},
            {"event": 5, "net_points": 60, "total_points": 310},
            {"event": 8, "net_points": 60, "total_points": 370},
        ],
        last_event={"event": 8, "net_points": 60, "total_points": 370}
    )
    
    participants = [participant1, participant2]
    
    # Apply ranks and calculate win counts
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_win_counts(participants)
    
    # participant1 should have 5 wins, 2 of which are golden
    assert participant1.win_count == 5, f"Participant1 should have 5 wins, but got {participant1.win_count}"
    assert participant1.golden_win_count == 2, f"Participant1 should have 2 golden wins (events 4 and 8), but got {participant1.golden_win_count}"
    
    # participant2 should have 1 win (event 2), which is not golden
    assert participant2.win_count == 1, f"Participant2 should have 1 win, but got {participant2.win_count}"
    assert participant2.golden_win_count == 0, f"Participant2 should have 0 golden wins, but got {participant2.golden_win_count}"


def test_win_column_in_template():
    """Test that the win count column appears in the rendered template."""
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
    
    # Check that the trophy image appears as a column header
    assert 'trophy.png' in html, "Template should contain trophy image in header"
    assert 'alt="🏆"' in html, "Trophy image should have trophy emoji as alt text"
    assert 'height: 18px' in html, "Trophy image should have 18px height"
    
    # Check that each participant's win count appears in the table
    for p in league_data["participants"]:
        # The win count should appear as text in the rendered HTML
        assert str(p.win_count) in html, f"Template should display win_count ({p.win_count}) for participant {p.manager_name}"


def test_win_display_format_without_golden_wins():
    """Test that win count displays as just the number when there are no golden wins."""
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=200,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70},  # Win
            {"event": 2, "net_points": 60, "total_points": 130},
        ],
        last_event={"event": 2, "net_points": 60, "total_points": 130}
    )
    
    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=180,
        history=[
            {"event": 1, "net_points": 50, "total_points": 50},
            {"event": 2, "net_points": 70, "total_points": 120},  # Win
        ],
        last_event={"event": 2, "net_points": 70, "total_points": 120}
    )
    
    participants = [participant1, participant2]
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_win_counts(participants)
    
    # Build league data and context
    league_data = {
        "id": 12345,
        "name": "Test League",
        "participants": participants,
        "event_ids": [1, 2],
        "finished_event_ids": [1, 2],
        "current_event_id": 2,
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
    
    # Check that participant1 has 1 win and 0 golden wins
    assert participant1.win_count == 1
    assert participant1.golden_win_count == 0
    
    # In the HTML, we should see just "1" in the cell, not "1 (0)"
    # Since there are other "1"s in the table, we need to be more specific
    # We'll check that "(0)" doesn't appear in the HTML at all
    assert " (0)" not in html, "Template should not display golden win count when it's 0"


def test_win_display_format_with_golden_wins():
    """Test that win count displays as 'X (Y)' when there are golden wins."""
    participant1 = Participant(
        entry_id=1, team_name="Team 1", manager_name="Player 1", total_score=350,
        history=[
            {"event": 1, "net_points": 70, "total_points": 70},  # Win
            {"event": 2, "net_points": 65, "total_points": 135},
            {"event": 3, "net_points": 70, "total_points": 205},  # Win
            {"event": 4, "net_points": 75, "total_points": 280},  # Golden gameweek win
        ],
        last_event={"event": 4, "net_points": 75, "total_points": 280}
    )
    
    participant2 = Participant(
        entry_id=2, team_name="Team 2", manager_name="Player 2", total_score=300,
        history=[
            {"event": 1, "net_points": 60, "total_points": 60},
            {"event": 2, "net_points": 70, "total_points": 130},  # Win
            {"event": 3, "net_points": 60, "total_points": 190},
            {"event": 4, "net_points": 65, "total_points": 255},
        ],
        last_event={"event": 4, "net_points": 65, "total_points": 255}
    )
    
    participants = [participant1, participant2]
    RankCalculator.apply_history_ranks(participants)
    RankCalculator.calculate_win_counts(participants)
    
    # Build league data and context
    league_data = {
        "id": 12345,
        "name": "Test League",
        "participants": participants,
        "event_ids": [1, 2, 3, 4],
        "finished_event_ids": [1, 2, 3, 4],
        "current_event_id": 4,
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
    
    # Check that it shows "3 (1)" - 3 total wins with 1 golden
    assert participant1.win_count == 3
    assert participant1.golden_win_count == 1
    
    # In the HTML, we should see "3 (1)" (rendered as 3&nbsp;(1) in HTML)
    assert "3&nbsp;(1)" in html, "Template should display win count as '3 (1)' when there are golden wins"
