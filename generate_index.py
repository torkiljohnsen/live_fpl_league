"""Generate docs/index.html, grouping the dashboards by season.

Seasons come from leagues.json (newest first). Dashboards for a league
that is not listed there are collected under an "Ukjent sesong" section
rather than being dropped.
"""

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

DOCS_DIR = Path("docs")
TEMPLATES_DIR = Path("templates")
LEAGUES_FILE = Path("leagues.json")
OUTPUT_FILE = DOCS_DIR / "index.html"

UNKNOWN_SEASON = "Ukjent sesong"

def get_league_html_files():
    """
    Return league_*.html and ranking_progression_*.html files in docs/,
    excluding -dev.html, test files, and index.html.
    """
    league_files = [
        f for f in DOCS_DIR.glob("league_*.html")
        if not f.name.endswith("-dev.html") and f.name != "index.html"
    ]
    ranking_files = [
        f for f in DOCS_DIR.glob("ranking_progression_*.html")
        if not f.name.endswith("-dev.html") and not f.name.startswith("test_")
    ]
    return sorted(league_files + ranking_files)

def extract_title(filepath: Path) -> str:
    """Extract the <title> from an HTML file, or fallback to a cleaned filename."""
    try:
        with filepath.open(encoding="utf-8") as f:
            for line in f:
                match = re.search(r'<title>(.*?)</title>', line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    except Exception:
        pass
    # fallback: prettify filename
    return filepath.stem.replace('_', ' ').title()

def load_seasons() -> list[dict]:
    """Read the season/league configuration, newest season first."""
    if not LEAGUES_FILE.is_file():
        return []
    config = json.loads(LEAGUES_FILE.read_text(encoding="utf-8"))
    return config.get("seasons", [])

def extract_league_id(filepath: Path) -> str | None:
    """Pull the trailing league ID out of a dashboard filename."""
    match = re.search(r'_(\d+)$', filepath.stem)
    return match.group(1) if match else None

def group_by_season(files: list[Path], seasons: list[dict]) -> list[dict]:
    """Group dashboard files into season sections, newest season first.

    Returns a list of dicts with 'season', 'report_url' (or None) and
    'league_files' (list of (filename, title) tuples). Sections without
    any generated dashboard are omitted.
    """
    season_of_league = {
        league["id"]: season["season"]
        for season in seasons
        for league in season.get("leagues", [])
    }

    grouped: dict[str, list[tuple[str, str]]] = {}
    for f in files:
        league_id = extract_league_id(f)
        season = season_of_league.get(league_id or "", UNKNOWN_SEASON)
        grouped.setdefault(season, []).append((f.name, extract_title(f)))

    sections = []
    for season in seasons:
        name = season["season"]
        if name not in grouped:
            continue
        report_league = season.get("report_league")
        sections.append({
            "season": name,
            "report_url": (
                f"reidars_rapport.html?season={name}" if report_league else None
            ),
            "league_files": grouped.pop(name),
        })

    for name, league_files in grouped.items():
        sections.append({
            "season": name, "report_url": None, "league_files": league_files
        })

    return sections

def main():
    files = get_league_html_files()
    sections = group_by_season(files, load_seasons())
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("index.html")
    html = template.render(seasons=sections)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Index generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
