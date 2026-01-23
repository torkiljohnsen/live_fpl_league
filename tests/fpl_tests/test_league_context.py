"""Tests for league context chart integration."""

import json
from pathlib import Path

from fpl.league_context import LeagueContext


class DummyAPI:
    """Dummy API for testing that returns sample data."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def get_bootstrap_static(self):
        return json.loads((self.data_dir / "bootstrap-static_sample.json").read_text(encoding="utf-8"))

    def get_league_standings(self, league_id):
        path = self.data_dir / f"leagues-classic_{league_id}_standings_sample.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def get_team_history(self, team_id):
        return json.loads((self.data_dir / "entry_811114_history_sample.json").read_text(encoding="utf-8"))

    def get_team(self, team_id):
        return {}

    def get_team_picks(self, team_id, event_id):
        return {}


data_dir = Path(__file__).parent / "data_samples"
LEAGUE_ID = "1639886"


def test_includes_chart_data():
    """Test that LeagueContext.build() includes chart data in context dict."""
    api = DummyAPI(data_dir)

    # Build league context with dev mode
    context = LeagueContext.build(
        league_id=LEAGUE_ID,
        dev_mode=True,
        league_join_code=None,
        fpl_api=api
    )

    # Get context as dict
    context_dict = context.as_dict()

    # Assert chart data is present
    assert "rank_progression_chart" in context_dict, "Context should include rank_progression_chart"

    # Assert chart is SVG string
    chart_data = context_dict["rank_progression_chart"]
    assert isinstance(chart_data, str), "Chart data should be a string"
    assert chart_data.startswith("<svg"), "Chart should be SVG format starting with <svg tag"
    assert "</svg>" in chart_data, "Chart should contain closing </svg> tag"

def test_formats_highest_team_value():
    """Test that LeagueContext formats highest team value correctly."""
    api = DummyAPI(data_dir)

    # Build league context
    context = LeagueContext.build(
        league_id=LEAGUE_ID,
        dev_mode=True,
        league_join_code=None,
        fpl_api=api
    )

    context_dict = context.as_dict()

    # Assert highest_team_value is formatted as expected
    assert "highest_team_value" in context_dict, "Context should include highest_team_value"
    highest_value = context_dict["highest_team_value"]

    if highest_value:
        # Should be formatted as: "Team name (Player name) - £XXX.XM"
        assert " - £" in highest_value, "Should contain currency format"
        assert "M" in highest_value, "Should end with M for millions"
        assert "(" in highest_value, "Should contain opening parenthesis"
        assert ")" in highest_value, "Should contain closing parenthesis"


def test_formats_in_form_players():
    """Test that LeagueContext formats in-form players correctly."""
    api = DummyAPI(data_dir)

    # Build league context
    context = LeagueContext.build(
        league_id=LEAGUE_ID,
        dev_mode=True,
        league_join_code=None,
        fpl_api=api
    )

    context_dict = context.as_dict()

    # Assert in_form_players is present
    assert "in_form_players" in context_dict, "Context should include in_form_players"
    in_form = context_dict["in_form_players"]

    if in_form:
        # Should be a dict with 'triangle' and 'text' keys
        assert isinstance(in_form, dict), "in_form_players should be a dict"
        assert "triangle" in in_form, "Should contain triangle key"
        assert "text" in in_form, "Should contain text key"
        assert in_form["triangle"] == "▲", "Triangle should be up arrow"
        assert "▲" in in_form["text"], "Text should contain arrow symbol"
        assert "runder på rad" in in_form["text"], "Text should be in Norwegian"
