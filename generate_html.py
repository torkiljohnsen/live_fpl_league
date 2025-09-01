
import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import sys
from fpl import FPL_API

FPL_LEAGUE_ID = "1639886"
LEAGUE_JOIN_CODE = "anblvx"
LOGO_PATH = "assets/fpl_logo.svg"
TEMPLATE_PATH = Path("template.html")

def get_output_path(dev_mode: bool):
    return Path("docs/index-dev.html") if dev_mode else Path("docs/index.html")


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


def generate_html(league_standings, league_name):
    # Read SVG logo as string
    with open(LOGO_PATH, "r", encoding="utf-8") as f:
        logo_svg = f.read()

    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(str(TEMPLATE_PATH))

    html = template.render(
        league_name=league_name,
        league_join_code=LEAGUE_JOIN_CODE,
        logo_svg=logo_svg,
        league_standings=league_standings
    )
    return html

if __name__ == "__main__":
    dev_mode = '--dev' in sys.argv
    fpl = FPL_API(dev_mode=dev_mode)
    data = fpl.get_league_standings(FPL_LEAGUE_ID)
    league_standings = prepare_league_standings(data)
    league_name = data.get("league", {}).get("name", "FPL Mini-League Dashboard")
    output_path = get_output_path(dev_mode)
    html = generate_html(league_standings, league_name)
    write_html_file(html, output_path)
