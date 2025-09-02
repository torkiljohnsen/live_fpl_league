import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fpl import FPL_API, FPLLeague

FPL_LEAGUE_ID = "1639886"
DEFAULT_LEAGUE_JOIN_CODE = "anblvx"  # Only used for default league if no join code is provided
LOGO_PATH = "assets/fpl_logo.svg"
TEMPLATE_PATH = Path("league_standings.html") 

def get_output_path(league_id: str, dev_mode: bool, template_path: Path):
    suffix = "-dev" if dev_mode else ""
    template_name = template_path.stem  # e.g., 'league_standings'
    filename = f"{template_name}_{league_id}{suffix}.html"
    return Path("docs") / filename

def prepare_league_standings(data):
    df = pd.DataFrame(data["standings"]["results"])
    df["rank_change"] = df["last_rank"] - df["rank_sort"]
    df["round_rank"] = df["event_total"].rank(method="min", ascending=False).astype(int)
    return df.to_dict(orient="records")

def write_html_file(html: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Static HTML generated at {output_path}")

def write_league_standings(league_standings, league_name, league_join_code):
    with open(LOGO_PATH, "r", encoding="utf-8") as f:
        logo_svg = f.read()

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(str(TEMPLATE_PATH))

    html = template.render(
        league_name=league_name,
        league_join_code=league_join_code,
        logo_svg=logo_svg,
        league_standings=league_standings
    )
    return html

def write_league_gameweek_history(fpl, league_id, dev_mode):
    league = FPLLeague(fpl, league_id)
    summary = league.get_summary()
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("league_gameweek_history.html")
    html = template.render(**summary)
    output_path = get_output_path(league_id, dev_mode, Path("league_gameweek_history.html"))
    write_html_file(html, output_path)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate static HTML for FPL mini-league dashboard.")
    parser.add_argument("-l", "--league_id", type=str, default=FPL_LEAGUE_ID, help="FPL league ID (default: %(default)s)")
    parser.add_argument("-j", "--join_code", type=str, default=None, help="League join code (optional, only shown if provided)")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode (use sample data)")
    args = parser.parse_args()

    league_id = args.league_id
    dev_mode = args.dev
    if args.join_code is not None:
        league_join_code = args.join_code
    elif league_id == FPL_LEAGUE_ID:
        league_join_code = DEFAULT_LEAGUE_JOIN_CODE
    else:
        league_join_code = None

    fpl = FPL_API(dev_mode=dev_mode)
    data = fpl.get_league_standings(league_id)
    league_standings = prepare_league_standings(data)
    league_name = data.get("league", {}).get("name", "FPL Mini-League Dashboard")
    output_path = get_output_path(league_id, dev_mode, TEMPLATE_PATH)  # Pass template path

    html = write_league_standings(league_standings, league_name, league_join_code)
    write_html_file(html, output_path)