"""Tests for the NarrativeHTMLRenderer class."""

from __future__ import annotations

from pathlib import Path

from fpl.narrative_html_renderer import NarrativeHTMLRenderer

SAMPLE_NARRATIVE = """\
# Reidars Rapport — Runde 27

![Reidars Rapport](reidars_rapport_2.png)

**Det var en vill runde** i Fantasy Premier League denne uken, med store svingninger og uventede resultater.

## Ukens vinner

Ola toppet runden med **85 poeng**, takket være en strålende kapteinspick.

## Bunnkampen

Kari hadde en tøff uke med bare 32 poeng, men holder fortsatt tredjeplassen totalt.

> «Neste runde skal det bli bedre,» sa Kari i en kommentar.
"""

TEMPLATES_DIR = str(Path(__file__).resolve().parents[2] / "templates")


class TestRender:
    """Tests for NarrativeHTMLRenderer.render()."""

    def test_creates_output_file(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)

        assert path.is_file()

    def test_output_file_path(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)

        assert path == tmp_path / "reidars_rapport_123_gw27.html"

    def test_extracts_title_from_heading(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "Reidars Rapport — Runde 27" in html

    def test_fallback_title_when_no_heading(self, tmp_path: Path) -> None:
        narrative = "No heading here.\n\nJust some text."
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(narrative, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "Reidars Rapport" in html

    def test_strips_image_lines(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "![Reidars Rapport]" not in html

    def test_markdown_to_html_bold(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "<strong>" in html

    def test_markdown_to_html_subheadings(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "<h2>" in html

    def test_markdown_to_html_paragraphs(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "<p>" in html

    def test_output_contains_subtitle(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "Runde 27" in html

    def test_output_contains_nav_links(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "456", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "league_standings_456.html" in html
        assert "league_gameweek_history_456.html" in html
        assert "ranking_progression_456.html" in html

    def test_output_contains_article_body(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "Ola toppet runden" in html

    def test_output_contains_hero_image(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "reidars_rapport_2.png" in html

    def test_output_contains_footer(self, tmp_path: Path) -> None:
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)
        html = path.read_text(encoding="utf-8")

        assert "Test League" in html
        assert "2025-26" in html

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        deep_output = tmp_path / "a" / "b" / "c"
        renderer = NarrativeHTMLRenderer(template_dir=TEMPLATES_DIR, output_dir=str(deep_output))
        path = renderer.render(SAMPLE_NARRATIVE, "123", "Test League", "2025-26", 27)

        assert path.is_file()
        assert deep_output.is_dir()


class TestGetGithubPagesUrl:
    """Tests for NarrativeHTMLRenderer.get_github_pages_url()."""

    def test_returns_correct_url(self) -> None:
        url = NarrativeHTMLRenderer.get_github_pages_url("123456", 27)

        assert url == "https://torkiljohnsen.github.io/live_fpl_league/reidars_rapport_123456_gw27.html"

    def test_url_includes_league_id(self) -> None:
        url = NarrativeHTMLRenderer.get_github_pages_url("999", 1)

        assert "999" in url

    def test_url_includes_event_id(self) -> None:
        url = NarrativeHTMLRenderer.get_github_pages_url("123", 15)

        assert "gw15" in url
