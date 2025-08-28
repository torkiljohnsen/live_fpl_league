
import requests
import pandas as pd
import re
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
df = df[["rank_sort", "last_rank", "entry_name", "player_name", "total", "event_total"]]
df = df.rename(columns={"rank_sort": "rank", "last_rank": "previous rank"})

# Helper to capitalize all words and words after hyphens
def smart_title(name):
    return re.sub(r'(^|[\s-])([\wæøåÆØÅéÉäöüßçñ]+)', lambda m: m.group(1) + m.group(2).capitalize(), name, flags=re.UNICODE)

def rank_with_change_html(row):
    change = row["previous rank"] - row["rank"]
    if row["previous rank"] == 0 or change == 0:
        return f'<span class="rank">{row["rank"]}</span>'
    if change > 0:
        return f'<span class="rank">{row["rank"]}</span> <span class="positive_rank_change">(+{change})</span>'
    else:
        return f'<span class="rank">{row["rank"]}</span> <span class="negative_rank_change">({change})</span>'

def add_medal(rank):
    if rank == 1:
        return "1 🥇"
    elif rank == 2:
        return "2 🥈"
    elif rank == 3:
        return "3 🥉"
    else:
        return str(rank)

df["Rank"] = df.apply(rank_with_change_html, axis=1)
df["Spiller/Lag_player_name"] = df["player_name"].apply(smart_title)
df["Spiller/Lag_entry_name"] = df["entry_name"]
df["Runde"] = df["event_total"]
df["Poeng"] = df["total"].apply(lambda x: f"<b>{x}</b>")
df["Runderank"] = df["Runde"].rank(method="min", ascending=False).astype(int)

# Prepend medal emoji to "Runde" if Runderank is 1, 2, or 3
def medal_for_rank(rank):
    if rank == 1:
        return "🥇 "
    elif rank == 2:
        return "🥈 "
    elif rank == 3:
        return "🥉 "
    else:
        return ""
df["Runde"] = df.apply(
    lambda row: medal_for_rank(row["Runderank"]) + f"<b>{row['Runde']}</b>",
    axis=1
)

# Build league_standings as a list of dicts for the template
league_standings = []
for _, row in df.iterrows():
    league_standings.append({
        "rank_html": row["Rank"],
        "player_name": row["Spiller/Lag_player_name"],
        "team_name": row["Spiller/Lag_entry_name"],
        "round_score_html": row["Runde"],
        "total_points_html": row["Poeng"]
    })

# Read and style SVG logo
logo_svg = ""
try:
    with open(LOGO_PATH, "r", encoding="utf-8") as f:
        logo_svg = f.read()
    # Remove width/height and add id for CSS
    logo_svg = re.sub(r'(<svg)([^>]*)(>)', lambda m: '<svg id="logo"' + re.sub(r'\s(width|height)="[^"]*"', '', m.group(2)) + '>', logo_svg, count=1)
    # Style only the logo SVG
    logo_svg = re.sub(r'(<svg[^>]*id="logo"[^>]*>)', r'\1<style>#logo * { fill: #fff !important; } #logo { width: 100% !important; height: auto !important; display: block; }</style>', logo_svg, count=1)
except Exception as e:
    logo_svg = f'<div style="color:red">Logo not found: {e}</div>'

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
