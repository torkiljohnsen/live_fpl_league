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
        path = self.data_dir / f"leagues-classic_{league_id}_standings_sample.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def get_team_history(self, team_id):
        return json.loads((self.data_dir / "entry_811114_history_sample.json").read_text(encoding="utf-8"))

    def get_team(self, team_id):
        return {}

    def get_team_picks(self, team_id, event_id):
        return {}

    def get_transfers(self, team_id):
        return []

    def get_fixtures(self, event_id=None):
        return []

    def get_event_live(self, event_id):
        return {}


data_dir = Path(__file__).parent / "data_samples"
LEAGUE_ID = "1639886"


def test_standings_uses_icon_files_instead_of_emojis():
    """Test that the standings page uses icon files instead of emoji characters."""
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
    renderer = LeagueTemplateRenderer(context, "standings")
    template = renderer.env.get_template(renderer.get_template_name())
    html = template.render(**context.as_dict(), output_type="standings")

    # Verify that icon image files are used (at least first_place exists in sample data)
    assert '<img src="assets/first_place.png"' in html, "Template should use assets/first_place.png icon"

    # Verify that emojis are NOT used in the rendered HTML
    assert '🥇' not in html, "Template should not contain gold medal emoji"
    assert '🥈' not in html, "Template should not contain silver medal emoji"
    assert '🥉' not in html, "Template should not contain bronze medal emoji"
    assert '🚨' not in html, "Template should not contain alarm emoji"

    # Verify that the icons use the medal-icon CSS class
    assert 'class="medal-icon"' in html, "Icons should use the medal-icon CSS class"

    # Verify the template references all icon files by reading from the templates directory
    # Use the renderer's template loader to get the correct template directory
    from jinja2.loaders import FileSystemLoader
    loader = renderer.env.loader
    if isinstance(loader, FileSystemLoader) and loader.searchpath:
        templates_dir = Path(loader.searchpath[0])
        template_path = templates_dir / "league_standings.html"
        template_content = template_path.read_text(encoding="utf-8")
        assert 'second_place.png' in template_content, "Template should reference second_place.png"
        assert 'third_place.png' in template_content, "Template should reference third_place.png"
        assert 'alarm.png' in template_content, "Template should reference alarm.png"
