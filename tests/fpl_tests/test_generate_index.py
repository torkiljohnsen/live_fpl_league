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
         patch.object(generate_index, "OUTPUT_FILE", output_file):

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
         patch.object(generate_index, "OUTPUT_FILE", output_file):

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
         patch.object(generate_index, "OUTPUT_FILE", output_file):

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
