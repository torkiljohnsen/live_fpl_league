import requests
import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import sys
import json

# Config
COLOR_DEEP_BLUE = "#00143C"
FPL_LEAGUE_ID = "1639886"
LOGO_PATH = "assets/fpl_logo.svg"
OUTPUT_PATH = Path("docs/index.html")
TEMPLATE_PATH = Path("template.html")


# Dev mode: use local sample_data.json if --dev flag is present
if '--dev' in sys.argv:
    with open('sample_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        print("Using local sample data")
else:
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{FPL_LEAGUE_ID}/standings/"
    r = requests.get(url)
    data = r.json()
    print("Fetched live data")

league_name = data.get("league", {}).get("name", "FPL Mini-League Dashboard")
standings = data["standings"]["results"]
df = pd.DataFrame(standings)

# Calculate rank_change and add round_rank for medals
df["rank_change"] = df["last_rank"] - df["rank_sort"]
df["round_rank"] = df["event_total"].rank(method="min", ascending=False).astype(int)
league_standings = df.to_dict(orient="records")

# Read SVG logo as string and inject id="logo"
logo_svg = ""
try:
    with open(LOGO_PATH, "r", encoding="utf-8") as f:
        logo_svg = f.read()
        if '<svg' in logo_svg:
            logo_svg = logo_svg.replace('<svg', '<svg id="logo"', 1)
except Exception as e:
    logo_svg = f'<div class="logo-error">Logo not found: {e}</div>'

# --- Jinja2 rendering ---
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
