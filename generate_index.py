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
MANIFEST_FILE = DOCS_DIR / "narratives" / "index.json"

UNKNOWN_SEASON = "Ukjent sesong"
CURRENT_SEASON_VISIBLE_ROUNDS = 8

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

def group_by_season(
    files: list[Path], seasons: list[dict], manifest: dict | None = None
) -> list[dict]:
    """Group dashboard files into season sections, newest season first.

    Returns a list of dicts with 'season', 'report_url' (or None),
    'league_files' (list of (filename, title) tuples), and 'report_rounds_visible'
    / 'report_rounds_hidden' (lists of (gw, url) tuples — see report_rounds_for).
    Sections without any generated dashboard are omitted.
    """
    season_of_league = {
        league["id"]: season["season"]
        for season in seasons
        for league in season.get("leagues", [])
    }
    gameweeks_by_season = {
        s["season"]: s["gameweeks"] for s in (manifest or {}).get("seasons", [])
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
        is_current = bool(season.get("current"))
        visible, hidden = report_rounds_for(
            name, is_current, gameweeks_by_season.get(name, [])
        )
        sections.append({
            "season": name,
            "report_url": (
                f"reidars_rapport.html?season={name}" if report_league else None
            ),
            "league_files": grouped.pop(name),
            "report_rounds_visible": visible,
            "report_rounds_hidden": hidden,
        })

    for name, league_files in grouped.items():
        sections.append({
            "season": name,
            "report_url": None,
            "league_files": league_files,
            "report_rounds_visible": [],
            "report_rounds_hidden": [],
        })

    return sections

def find_gameweeks(season: str, league_id: str) -> list[int]:
    """Gameweek numbers with a published narrative for a season/league, ascending."""
    season_dir = DOCS_DIR / "narratives" / season / league_id
    if not season_dir.is_dir():
        return []
    gameweeks = []
    for f in season_dir.glob("gw*.md"):
        match = re.fullmatch(r"gw(\d+)", f.stem)
        if match:
            gameweeks.append(int(match.group(1)))
    return sorted(gameweeks)

def build_narrative_manifest(seasons: list[dict]) -> dict:
    """Build the manifest of published narratives, newest season first.

    Walks docs/narratives/{season}/{league_id}/gw*.md on disk. Seasons and their
    report league come from leagues.json (in the order given); a narrative
    directory found on disk with no matching entry there is appended at the end
    rather than dropped.
    """
    result = []
    known: set[tuple[str, str]] = set()
    for season in seasons:
        name = season["season"]
        league_id = season.get("report_league")
        if not league_id:
            continue
        known.add((name, league_id))
        gameweeks = find_gameweeks(name, league_id)
        if gameweeks:
            result.append({
                "season": name, "league_id": league_id, "gameweeks": gameweeks
            })

    narratives_root = DOCS_DIR / "narratives"
    if narratives_root.is_dir():
        for season_dir in sorted(p for p in narratives_root.iterdir() if p.is_dir()):
            for league_dir in sorted(p for p in season_dir.iterdir() if p.is_dir()):
                key = (season_dir.name, league_dir.name)
                if key in known:
                    continue
                gameweeks = find_gameweeks(season_dir.name, league_dir.name)
                if gameweeks:
                    result.append({
                        "season": season_dir.name,
                        "league_id": league_dir.name,
                        "gameweeks": gameweeks,
                    })
                    known.add(key)

    return {"seasons": result}

def report_gw_url(season: str, gw: int, is_current: bool) -> str:
    """Link to a single report. The current season omits the &season= suffix."""
    if is_current:
        return f"reidars_rapport.html?gw={gw}"
    return f"reidars_rapport.html?gw={gw}&season={season}"

def report_rounds_for(
    season: str, is_current: bool, gameweeks: list[int]
) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Split a season's rounds (newest first) into visible / collapsed lists.

    The current season shows its newest CURRENT_SEASON_VISIBLE_ROUNDS rounds
    inline; the rest (if any) is collapsed. Archive seasons collapse everything.
    """
    rounds = [
        (gw, report_gw_url(season, gw, is_current))
        for gw in sorted(gameweeks, reverse=True)
    ]
    if is_current:
        return rounds[:CURRENT_SEASON_VISIBLE_ROUNDS], rounds[CURRENT_SEASON_VISIBLE_ROUNDS:]
    return [], rounds

def main():
    files = get_league_html_files()
    seasons_config = load_seasons()

    manifest = build_narrative_manifest(seasons_config)
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Narrative manifest generated at {MANIFEST_FILE}")

    sections = group_by_season(files, seasons_config, manifest)
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
