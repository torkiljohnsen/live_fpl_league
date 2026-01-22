"""Tests for generate_index.py"""

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


def test_main_includes_ranking_progression_in_index(mock_docs_files, tmp_path):
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
    {% for file, title in league_files %}
        <li><a href="{{ file }}">{{ title }}</a></li>
    {% endfor %}
    </ul>
</body>
</html>
""", encoding="utf-8")

    output_file = mock_docs_files / "index.html"

    with patch.object(generate_index, "DOCS_DIR", mock_docs_files), \
         patch.object(generate_index, "TEMPLATES_DIR", templates_dir), \
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


def test_ranking_progression_links_are_correctly_formatted(mock_docs_files, tmp_path):
    """Test that ranking_progression links in index are properly formatted as clickable links."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create index template
    (templates_dir / "index.html").write_text("""
{% for file, title in league_files %}
<a href="{{ file }}">{{ title }}</a>
{% endfor %}
""", encoding="utf-8")

    output_file = mock_docs_files / "index.html"

    with patch.object(generate_index, "DOCS_DIR", mock_docs_files), \
         patch.object(generate_index, "TEMPLATES_DIR", templates_dir), \
         patch.object(generate_index, "OUTPUT_FILE", output_file):

        generate_index.main()
        index_html = output_file.read_text(encoding="utf-8")

        # Check for properly formatted links
        assert '<a href="ranking_progression_1638989.html">' in index_html
        assert '<a href="ranking_progression_1639886.html">' in index_html
