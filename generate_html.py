
import requests
import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import sys
import json


FPL_LEAGUE_ID = "1639886"
LOGO_PATH = "assets/fpl_logo.svg"
TEMPLATE_PATH = Path("template.html")

def get_output_path(dev_mode: bool):
    if dev_mode:
        return Path("docs/index-dev.html")
    else:
        return Path("docs/index.html")

class FPL:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, league_id):
        self.league_id = league_id

    def get_league_standings(self):
        url = f"{self.BASE_URL}/leagues-classic/{self.league_id}/standings/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_entry(self, entry_id):
        url = f"{self.BASE_URL}/entry/{entry_id}/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_entry_history(self, entry_id):
        url = f"{self.BASE_URL}/entry/{entry_id}/history/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_entry_picks(self, entry_id, event_id):
        url = f"{self.BASE_URL}/entry/{entry_id}/event/{event_id}/picks/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_bootstrap_static(self):
        url = f"{self.BASE_URL}/bootstrap-static/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

def load_league_data(dev_mode: bool, fpl: FPL):
    if dev_mode:
        print("Loading sample data for development.")
        with open('sample_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("Loading live data from API.")
        data = fpl.get_league_standings()
    return data

def prepare_league_standings(data):
    df = pd.DataFrame(data["standings"]["results"])
    df["rank_change"] = df["last_rank"] - df["rank_sort"]
    df["round_rank"] = df["event_total"].rank(method="min", ascending=False).astype(int)
    return df.to_dict(orient="records")


def render_html():
    dev_mode = '--dev' in sys.argv
    fpl = FPL(FPL_LEAGUE_ID)
    data = load_league_data(dev_mode, fpl)
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

    output_path = get_output_path(dev_mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Static HTML generated at {output_path}")

if __name__ == "__main__":
    render_html()
