"""Tests for generate_index.py"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import generate_index


@pytest.fixture
def mock_docs_files(tmp_path):
    """Create mock HTML files in a temporary docs directory."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create league files
    (docs_dir / "league_standings_1638989.html").write_text(
        "<title>Sinkaberg administrasjon - Current standings</title>",
        encoding="utf-8"
    )
    (docs_dir / "league_gameweek_history_1638989.html").write_text(
        "<title>Sinkaberg administrasjon - Gameweek History</title>",
        encoding="utf-8"
    )

    # Create ranking progression files
    (docs_dir / "ranking_progression_1638989.html").write_text(
        "<title>Sinkaberg administrasjon - Rank Progression</title>",
        encoding="utf-8"
    )
    (docs_dir / "ranking_progression_1639886.html").write_text(
        "<title>Sinkaberg Superliga - Rank Progression</title>",
        encoding="utf-8"
    )

    # Create dev files (should be excluded)
    (docs_dir / "league_standings_1638989-dev.html").write_text(
        "<title>Dev file</title>",
        encoding="utf-8"
    )
    (docs_dir / "ranking_progression_1638989-dev.html").write_text(
        "<title>Dev ranking file</title>",
        encoding="utf-8"
    )

    # Create test file (should be excluded)
    (docs_dir / "test_ranking_progression.html").write_text(
        "<title>Test file</title>",
        encoding="utf-8"
    )

    return docs_dir


@pytest.fixture
def mock_leagues_file(tmp_path):
    """Season config covering the fixture leagues."""
    leagues_file = tmp_path / "leagues.json"
    leagues_file.write_text(json.dumps({
        "seasons": [
            {
                "season": "2026-27",
                "report_league": "848662",
                "leagues": [{"id": "848662", "name": "Sinkaberg The Office"}],
            },
            {
                "season": "2025-26",
                "report_league": "1638989",
                "leagues": [
                    {"id": "1638989", "name": "Sinkaberg administrasjon"},
                    {"id": "1639886", "name": "Sinkaberg Superliga"},
                ],
            },
        ]
    }), encoding="utf-8")
    return leagues_file


def test_get_league_html_files_includes_ranking_progression(mock_docs_files):
    """Test that get_league_html_files includes ranking_progression files."""
    with patch.object(generate_index, "DOCS_DIR", mock_docs_files):
        files = generate_index.get_league_html_files()
        file_names = [f.name for f in files]

        # Should include league files
        assert "league_standings_1638989.html" in file_names
        assert "league_gameweek_history_1638989.html" in file_names

        # Should include ranking progression files
        assert "ranking_progression_1638989.html" in file_names
        assert "ranking_progression_1639886.html" in file_names

        # Should exclude dev files
        assert "league_standings_1638989-dev.html" not in file_names
        assert "ranking_progression_1638989-dev.html" not in file_names

        # Should exclude test files
        assert "test_ranking_progression.html" not in file_names


def test_main_includes_ranking_progression_in_index(
    mock_docs_files, mock_leagues_file, tmp_path
):
    """Test that main() generates index with ranking_progression links."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create index template
    (templates_dir / "index.html").write_text("""
<!DOCTYPE html>
<html>
<body>
    <h1>Index</h1>
    <ul>
    {% for season in seasons %}
        <h2>{{ season.season }}</h2>
        {% for file, title in season.league_files %}
            <li><a href="{{ file }}">{{ title }}</a></li>
        {% endfor %}
    {% endfor %}
    </ul>
</body>
</html>
""", encoding="utf-8")

    output_file = mock_docs_files / "index.html"

    with patch.object(generate_index, "DOCS_DIR", mock_docs_files), \
         patch.object(generate_index, "TEMPLATES_DIR", templates_dir), \
         patch.object(generate_index, "LEAGUES_FILE", mock_leagues_file), \
         patch.object(generate_index, "OUTPUT_FILE", output_file), \
         patch.object(
             generate_index, "MANIFEST_FILE", mock_docs_files / "narratives" / "index.json"
         ):

        generate_index.main()

        # Verify index file was created
        assert output_file.exists()

        # Read generated index
        index_html = output_file.read_text(encoding="utf-8")

        # Should include ranking progression links
        assert "ranking_progression_1638989.html" in index_html
        assert "ranking_progression_1639886.html" in index_html
        assert "Sinkaberg administrasjon - Rank Progression" in index_html
        assert "Sinkaberg Superliga - Rank Progression" in index_html

        # Should include league links
        assert "league_standings_1638989.html" in index_html
        assert "league_gameweek_history_1638989.html" in index_html

        # Should NOT include dev or test files
        assert "-dev.html" not in index_html
        assert "test_ranking_progression.html" not in index_html


def test_ranking_progression_links_are_correctly_formatted(
    mock_docs_files, mock_leagues_file, tmp_path
):
    """Test that ranking_progression links in index are properly formatted as clickable links."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create index template
    (templates_dir / "index.html").write_text("""
{% for season in seasons %}
{% for file, title in season.league_files %}
<a href="{{ file }}">{{ title }}</a>
{% endfor %}
{% endfor %}
""", encoding="utf-8")

    output_file = mock_docs_files / "index.html"

    with patch.object(generate_index, "DOCS_DIR", mock_docs_files), \
         patch.object(generate_index, "TEMPLATES_DIR", templates_dir), \
         patch.object(generate_index, "LEAGUES_FILE", mock_leagues_file), \
         patch.object(generate_index, "OUTPUT_FILE", output_file), \
         patch.object(
             generate_index, "MANIFEST_FILE", mock_docs_files / "narratives" / "index.json"
         ):

        generate_index.main()
        index_html = output_file.read_text(encoding="utf-8")

        # Check for properly formatted links
        assert '<a href="ranking_progression_1638989.html">' in index_html
        assert '<a href="ranking_progression_1639886.html">' in index_html


# ---------------------------------------------------------------------------
# Season grouping
# ---------------------------------------------------------------------------


def test_index_groups_files_under_their_season(
    mock_docs_files, mock_leagues_file, tmp_path
):
    """Each dashboard is listed under the season its league belongs to."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text("""
{% for season in seasons %}
<h2>{{ season.season }}</h2>
{% for file, title in season.league_files %}<a href="{{ file }}">{{ title }}</a>
{% endfor %}
{% if season.report_url %}<a href="{{ season.report_url }}">Reidars Rapport</a>{% endif %}
{% endfor %}
""", encoding="utf-8")
    output_file = mock_docs_files / "index.html"

    with patch.object(generate_index, "DOCS_DIR", mock_docs_files), \
         patch.object(generate_index, "TEMPLATES_DIR", templates_dir), \
         patch.object(generate_index, "LEAGUES_FILE", mock_leagues_file), \
         patch.object(generate_index, "OUTPUT_FILE", output_file), \
         patch.object(
             generate_index, "MANIFEST_FILE", mock_docs_files / "narratives" / "index.json"
         ):

        generate_index.main()
        index_html = output_file.read_text(encoding="utf-8")

    assert "<h2>2025-26</h2>" in index_html
    # No 2026-27 dashboards exist in the fixture, so that season is omitted
    assert "<h2>2026-27</h2>" not in index_html
    assert "reidars_rapport.html?season=2025-26" in index_html


def test_unknown_league_gets_its_own_section():
    """A league missing from leagues.json is still listed, not dropped."""
    seasons = [{"season": "2026-27", "leagues": [{"id": "848662", "name": "X"}]}]
    files = [Path("docs/league_standings_999999.html")]

    sections = generate_index.group_by_season(files, seasons)

    assert len(sections) == 1
    assert sections[0]["season"] == generate_index.UNKNOWN_SEASON
    assert sections[0]["league_files"][0][0] == "league_standings_999999.html"


def test_extract_league_id():
    assert generate_index.extract_league_id(
        Path("docs/ranking_progression_848662.html")
    ) == "848662"
    assert generate_index.extract_league_id(Path("docs/index.html")) is None


# ---------------------------------------------------------------------------
# Narrative manifest
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_narratives_dir(tmp_path):
    """Populate docs/narratives/{season}/{league_id}/gw*.md for two seasons."""
    docs_dir = tmp_path / "docs"
    narratives_dir = docs_dir / "narratives"
    for season, league_id, gws in (
        ("2026-27", "848662", [1]),
        ("2025-26", "1638989", [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]),
    ):
        league_dir = narratives_dir / season / league_id
        league_dir.mkdir(parents=True)
        for gw in gws:
            (league_dir / f"gw{gw}.md").write_text("# Runde", encoding="utf-8")
    return docs_dir


def test_find_gameweeks_returns_ascending_ints(mock_narratives_dir):
    with patch.object(generate_index, "DOCS_DIR", mock_narratives_dir):
        assert generate_index.find_gameweeks("2025-26", "1638989") == list(range(27, 39))
        assert generate_index.find_gameweeks("2026-27", "848662") == [1]


def test_find_gameweeks_missing_dir_returns_empty(mock_narratives_dir):
    with patch.object(generate_index, "DOCS_DIR", mock_narratives_dir):
        assert generate_index.find_gameweeks("2024-25", "000000") == []


def test_build_narrative_manifest_shape(mock_narratives_dir):
    seasons = [
        {"season": "2026-27", "current": True, "report_league": "848662"},
        {"season": "2025-26", "report_league": "1638989"},
    ]
    with patch.object(generate_index, "DOCS_DIR", mock_narratives_dir):
        manifest = generate_index.build_narrative_manifest(seasons)

    assert manifest == {
        "seasons": [
            {"season": "2026-27", "league_id": "848662", "gameweeks": [1]},
            {
                "season": "2025-26",
                "league_id": "1638989",
                "gameweeks": list(range(27, 39)),
            },
        ]
    }


def test_build_narrative_manifest_omits_season_without_narratives(tmp_path):
    """A season with no report_league, or none published yet, is skipped."""
    docs_dir = tmp_path / "docs"
    (docs_dir / "narratives" / "2026-27" / "848662").mkdir(parents=True)
    # 2026-27 has a directory but no gw*.md files yet — no reports published.
    seasons = [
        {"season": "2027-28", "current": True},  # no report_league at all
        {"season": "2026-27", "report_league": "848662"},
    ]
    with patch.object(generate_index, "DOCS_DIR", docs_dir):
        manifest = generate_index.build_narrative_manifest(seasons)

    assert manifest["seasons"] == []


def test_build_narrative_manifest_appends_unknown_season(mock_narratives_dir):
    """A narrative directory on disk with no matching leagues.json entry is kept."""
    extra_dir = mock_narratives_dir / "narratives" / "2024-25" / "111111"
    extra_dir.mkdir(parents=True)
    (extra_dir / "gw5.md").write_text("# Runde", encoding="utf-8")

    seasons = [{"season": "2026-27", "current": True, "report_league": "848662"}]
    with patch.object(generate_index, "DOCS_DIR", mock_narratives_dir):
        manifest = generate_index.build_narrative_manifest(seasons)

    assert {"season": "2024-25", "league_id": "111111", "gameweeks": [5]} in (
        manifest["seasons"]
    )


# ---------------------------------------------------------------------------
# Per-season report rounds (front page list)
# ---------------------------------------------------------------------------


def test_report_rounds_for_current_season_caps_at_eight():
    gameweeks = list(range(1, 13))  # 12 rounds
    visible, hidden = generate_index.report_rounds_for("2026-27", True, gameweeks)

    assert [gw for gw, _ in visible] == [12, 11, 10, 9, 8, 7, 6, 5]
    assert [gw for gw, _ in hidden] == [4, 3, 2, 1]
    # Current season links have no &season= suffix
    assert visible[0][1] == "reidars_rapport.html?gw=12"


def test_report_rounds_for_current_season_no_overflow_when_eight_or_fewer():
    gameweeks = [1, 2, 3]
    visible, hidden = generate_index.report_rounds_for("2026-27", True, gameweeks)

    assert [gw for gw, _ in visible] == [3, 2, 1]
    assert hidden == []


def test_report_rounds_for_archive_season_all_hidden():
    gameweeks = [27, 28, 29]
    visible, hidden = generate_index.report_rounds_for("2025-26", False, gameweeks)

    assert visible == []
    assert [gw for gw, _ in hidden] == [29, 28, 27]
    # Archive season links carry the &season= suffix
    assert hidden[0][1] == "reidars_rapport.html?gw=29&season=2025-26"


def test_group_by_season_attaches_report_rounds(mock_docs_files, mock_leagues_file):
    """group_by_season splits report rounds using each season's 'current' flag."""
    leagues_config = json.loads(mock_leagues_file.read_text(encoding="utf-8"))
    manifest = {
        "seasons": [
            {"season": "2025-26", "league_id": "1638989", "gameweeks": [27, 28]},
        ]
    }
    leagues_config["seasons"][0]["current"] = True
    seasons = leagues_config["seasons"]

    sections = generate_index.group_by_season(
        list(mock_docs_files.glob("*.html")),
        seasons,
        manifest,
    )

    archive_section = next(s for s in sections if s["season"] == "2025-26")
    assert archive_section["report_rounds_visible"] == []
    assert [gw for gw, _ in archive_section["report_rounds_hidden"]] == [28, 27]


# ---------------------------------------------------------------------------
# Full main() run: manifest file + template rendering
# ---------------------------------------------------------------------------


def test_main_writes_narrative_manifest(
    mock_docs_files, mock_leagues_file, tmp_path, mock_narratives_dir
):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text(
        "{% for season in seasons %}{{ season.season }}{% endfor %}",
        encoding="utf-8",
    )
    output_file = mock_docs_files / "index.html"
    manifest_file = mock_docs_files / "narratives" / "index.json"

    # Merge the narrative fixture files into the docs dir used for dashboards
    for item in mock_narratives_dir.glob("narratives/**/*"):
        if item.is_file():
            dest = mock_docs_files / item.relative_to(mock_narratives_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")

    with patch.object(generate_index, "DOCS_DIR", mock_docs_files), \
         patch.object(generate_index, "TEMPLATES_DIR", templates_dir), \
         patch.object(generate_index, "LEAGUES_FILE", mock_leagues_file), \
         patch.object(generate_index, "OUTPUT_FILE", output_file), \
         patch.object(generate_index, "MANIFEST_FILE", manifest_file):

        generate_index.main()

        assert manifest_file.exists()
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    season_names = [s["season"] for s in manifest["seasons"]]
    assert season_names == ["2026-27", "2025-26"]
    assert manifest["seasons"][0]["gameweeks"] == [1]
    assert manifest["seasons"][1]["gameweeks"] == list(range(27, 39))


def test_index_template_lists_reports_grouped_and_capped():
    """Render templates/index.html against a fake sections list."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")

    sections = [
        {
            "season": "2026-27",
            "report_url": "reidars_rapport.html?season=2026-27",
            "league_files": [("league_standings_848662.html", "The Office")],
            "report_rounds_visible": [
                (n, f"reidars_rapport.html?gw={n}") for n in range(12, 4, -1)
            ],
            "report_rounds_hidden": [
                (n, f"reidars_rapport.html?gw={n}") for n in range(4, 0, -1)
            ],
        },
        {
            "season": "2025-26",
            "report_url": "reidars_rapport.html?season=2025-26",
            "league_files": [("league_standings_1638989.html", "Sinkaberg")],
            "report_rounds_visible": [],
            "report_rounds_hidden": [
                (n, f"reidars_rapport.html?gw={n}&season=2025-26")
                for n in range(38, 26, -1)
            ],
        },
    ]

    html = template.render(seasons=sections)

    # Current season: newest 8 rounds listed directly
    assert "Runde 12" in html
    assert "Runde 5" in html
    assert html.index("Runde 12") < html.index("Runde 5")
    assert '<a href="reidars_rapport.html?gw=12">Runde 12</a>' in html

    # Overflow tucked behind a native <details>/<summary>
    assert "<details>" in html
    assert "<summary>Alle runder</summary>" in html
    assert "Runde 4" in html
    assert "Runde 1" in html

    # Archive season: everything collapsed, nothing listed inline
    # (autoescape turns & into &amp; inside the href attribute)
    assert (
        '<a href="reidars_rapport.html?gw=38&amp;season=2025-26">Runde 38</a>'
        in html
    )
    archive_block = html[html.index("2025-26"):]
    assert "<details>" in archive_block
