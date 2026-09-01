"""Guards on how docs/ is published to GitHub Pages."""

from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def test_nojekyll_marker_exists():
    """Pages must serve docs/ verbatim, not through Jekyll.

    Without this marker Jekyll renders every ``.md`` file that starts with a
    YAML front-matter block into ``.html`` and drops the source, so the
    narratives that ``reidars_rapport.html`` fetches would 404.
    """
    assert (DOCS_DIR / ".nojekyll").is_file(), (
        "docs/.nojekyll is missing — GitHub Pages would run Jekyll and stop "
        "serving narrative .md files that carry front matter"
    )
