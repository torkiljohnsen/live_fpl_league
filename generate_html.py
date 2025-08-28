import requests
import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import sys
import json


FPL_LEAGUE_ID = "1639886"
LOGO_PATH = "assets/fpl_logo.svg"
OUTPUT_PATH = Path("docs/index.html")
TEMPLATE_PATH = Path("template.html")

def load_league_data(dev_mode: bool):
    if dev_mode:
        print("Loading sample data for development.")
        with open('sample_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("Loading live data from API.")
        url = f"https://fantasy.premierleague.com/api/leagues-classic/{FPL_LEAGUE_ID}/standings/"
        r = requests.get(url)
        data = r.json()
    return data

def prepare_league_standings(data):
    df = pd.DataFrame(data["standings"]["results"])
    df["rank_change"] = df["last_rank"] - df["rank_sort"]
    df["round_rank"] = df["event_total"].rank(method="min", ascending=False).astype(int)
    return df.to_dict(orient="records")

def render_html():
    dev_mode = '--dev' in sys.argv
    data = load_league_data(dev_mode)
    league_standings = prepare_league_standings(data)

    # Read SVG logo as string
    with open(LOGO_PATH, "r", encoding="utf-8") as f:
        logo_svg = f.read()

    # --- Jinja2 rendering ---
    league_name = data.get("league", {}).get("name", "FPL Mini-League Dashboard")
    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(str(TEMPLATE_PATH))

    html = template.render(
        league_name=league_name,
        logo_svg=logo_svg,
        league_standings=league_standings
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Static HTML generated at {OUTPUT_PATH}")

if __name__ == "__main__":
    render_html()
