import json
from pathlib import Path

from fpl.fpl_league import FPLLeague
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
        data = json.loads((self.data_dir / "entry_811114_history_sample.json").read_text(encoding="utf-8"))
        # Add a transfer cost to simulate the issue scenario (61 points - 4 hit = 57 net points)
        if data["current"]:
            # Modify the first event to have a transfer cost
            data["current"][0]["points"] = 61
            data["current"][0]["event_transfers_cost"] = 4
        return data

    def get_team(self, team_id):
        return {}

    def get_team_picks(self, team_id, event_id):
        return {}


data_dir = Path(__file__).parent / "data_samples"
LEAGUE_ID = "1639886"


def test_gameweek_history_shows_net_points():
    """Test that the gameweek history page displays net_points (after transfer costs) instead of gross points."""
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    league_data = league.get_summary()

    # Get a participant with transfer costs
    participant = league_data["participants"][0]

    # Find an event with transfer costs
    event_with_cost = None
    for h in participant.history:
        if h.get("event_transfers_cost", 0) > 0:
            event_with_cost = h
            break

    # Verify we have data with transfer costs to test
    assert event_with_cost is not None, "Test data should have at least one event with transfer costs"

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

    # The HTML should contain net_points values, not gross points for events with transfer costs
    # For the event with transfer cost, verify net_points is shown
    gross_points = event_with_cost["points"]
    net_points = event_with_cost["net_points"]
    transfer_cost = event_with_cost["event_transfers_cost"]

    # Verify net_points calculation is correct
    expected_net = gross_points - transfer_cost
    msg = f"net_points should be {gross_points} - {transfer_cost} = {expected_net}"
    assert net_points == expected_net, msg

    # The rendered HTML should show net_points, not gross points
    # We need to find the cell value for this participant and event
    # This is a basic check - in the real HTML, the net_points value should appear in the table cell
    msg2 = f"Template should display net_points ({net_points}) for events with transfer costs"
    assert str(net_points) in html, msg2

    # Additionally verify that gross_points and net_points are different for this event
    assert gross_points != net_points, "Test data should have gross_points different from net_points to verify the fix"
