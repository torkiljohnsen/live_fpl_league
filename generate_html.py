import requests
import pandas as pd
import re
from pathlib import Path

# Config
COLOR_DEEP_BLUE = "#00143C"
FPL_LEAGUE_ID = "1639886"
LOGO_PATH = "assets/fpl_logo.svg"
OUTPUT_PATH = Path("docs/index.html")

# Fetch league data
url = f"https://fantasy.premierleague.com/api/leagues-classic/{FPL_LEAGUE_ID}/standings/"
r = requests.get(url)
data = r.json()

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
        return f'{row["rank"]}'
    if change > 0:
        return f'{row["rank"]} <span style="color:green">(+{change})</span>'
    else:
        return f'{row["rank"]} <span style="color:red">({change})</span>'

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
# Combine player and team name into one column
df["Spiller/Lag"] = df.apply(
    lambda row: f'<span class="player_name">{smart_title(row["player_name"])}</span><br>{row["entry_name"]}',
    axis=1
)
df["Runde"] = df["event_total"]
df["Poeng"] = df["total"].apply(lambda x: f"<b>{x}</b>")
df["Runderank"] = df["Runde"].rank(method="min", ascending=False).astype(int)
df["Runderank"] = df["Runderank"].apply(add_medal)
# Only keep the new combined column, remove separate Lag/Spiller
df = df[["Rank", "Spiller/Lag", "Runde", "Runderank", "Poeng"]]

def df_to_html_table(df):
    headers = df.columns.tolist()
    html = "<table>\n<tr>"
    for h in headers:
        if h == "Rank":
            html += '<th class="left"></th>'  # Blank header for Rank
        elif h in ["Spiller/Lag"]:
            html += f'<th class="left">{h}</th>'
        elif h == "Poeng":
            html += f'<th class="right">{h}</th>'
        else:
            html += f'<th>{h}</th>'
    html += "</tr>\n"
    for _, row in df.iterrows():
        html += "<tr>"
        for h, cell in zip(headers, row):
            if h in ["Rank", "Spiller/Lag"]:
                html += f'<td class="left">{cell}</td>'
            elif h == "Poeng":
                html += f'<td class="right">{cell}</td>'
            else:
                html += f'<td>{cell}</td>'
        html += "</tr>\n"
    html += "</table>"
    return html

# Read and style SVG logo
logo_svg = ""
try:
    with open(LOGO_PATH, "r", encoding="utf-8") as f:
        logo_svg = f.read()
    # Remove width/height and add id for CSS
    logo_svg = re.sub(r'(<svg)([^>]*)(>)', lambda m: '<svg id="logo"' + re.sub(r'\\s(width|height)="[^"]*"', '', m.group(2)) + '>', logo_svg, count=1)
    # Style only the logo SVG
    logo_svg = re.sub(r'(<svg[^>]*id="logo"[^>]*>)', r'\1<style>#logo * { fill: #fff !important; } #logo { width: 100% !important; height: auto !important; display: block; }</style>', logo_svg, count=1)
except Exception as e:
    logo_svg = f'<div style="color:red">Logo not found: {e}</div>'

# HTML template
html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{league_name}</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Sora:wght@700&display=swap\" rel=\"stylesheet\">
    <style>
        body {{
            background: {COLOR_DEEP_BLUE};
            color: #fff;
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
        }}
        h1 {{
            font-family: 'Sora', sans-serif;
            text-align: center;
            font-size: 2.2rem;
            margin-bottom: 1.5rem;
        }}
        .logo-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin-bottom: 0.5rem;
            margin-top: 2rem;
        }}
        .logo-container > div {{
            width: 250px;
            max-width: 100vw;
        }}
        table {{
            margin: 2rem auto;
            border-collapse: collapse;
            font-size: 1.2rem;
            background: #0A2540;
            border-radius: 8px;
            overflow: hidden;
            max-width: 95vw;
        }}
        th, td {{
            padding: 0.7rem 1.2rem;
            text-align: center;
            line-height: 1rem;
        }}
        th.left, td.left {{
            text-align: left;
        }}
        th.right, td.right {{
            text-align: right;
        }}
        th {{
            background: #1E90FF;
            color: #fff;
            font-family: 'Sora', sans-serif;
            font-size: 1.1em;
        }}
        tr:nth-child(even) {{
            background: #112a4d;
        }}
        tr:nth-child(odd) {{
            background: #0A2540;
        }}
        .player_name {{
            font-weight: bold;
            display: block;
        }}
        @media (max-width: 768px) {{
            table {{
                font-size: 1rem;
            }}
            th, td {{
                padding: 0.5rem 0.7rem;
            }}
        }}
    </style>
</head>
<body>
    <div class=\"logo-container\"><div>{logo_svg}</div></div>
    <h1>{league_name}</h1>
    {df_to_html_table(df)}
</body>
</html>
"""

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Static HTML generated at {OUTPUT_PATH}")
