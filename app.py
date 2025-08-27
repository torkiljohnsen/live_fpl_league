import streamlit as st
import pandas as pd
import requests
import re

# Config
COLOR_DEEP_BLUE = "#00143C"
FPL_LEAGUE_ID = "1639886"  # replace with your league ID

st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COLOR_DEEP_BLUE};
        }}
        .stMainBlockContainer {{ padding-top: 0 }}
    </style>
""", unsafe_allow_html=True)

# Inject Google Fonts and set font styles
st.markdown(
    '''
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Sora:wght@700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="st-"] {
            font-family: 'Inter', sans-serif !important;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Sora', sans-serif !important;
        }
    </style>
    ''',
    unsafe_allow_html=True
)

# Show logo above the title by embedding SVG contents
def show_svg_logo(svg_path, width=250):
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg = f.read()
        # Remove width/height attributes from SVG tag to allow CSS to control size
        import re
        svg = re.sub(r'(<svg)([^>]*)(>)', lambda m: '<svg id="logo"' + re.sub(r'\s(width|height)="[^"]*"', '', m.group(2)) + '>', svg, count=1)
        # Inject style to force only #logo and its children to fill white and scale responsively
        svg = re.sub(
            r'(<svg[^>]*id="logo"[^>]*>)',
            r'\1<style>#logo * { fill: #fff !important; } #logo { width: 100% !important; height: auto !important; display: block; }</style>',
            svg,
            count=1
        )
        st.markdown(
            f'<div style="display:flex; justify-content:center; align-items:center; width:100%; margin-bottom:0.5rem;">'
            f'<div style="width:{width}px; max-width:100vw;">{svg}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"Logo could not be loaded: {e}")

show_svg_logo("assets/fpl_logo.svg", width=250)

# Fetch and cache league data (standings and league name) for 1 hour
@st.cache_data(ttl=3600)
def fetch_league_data():
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{FPL_LEAGUE_ID}/standings/"
    r = requests.get(url)
    data = r.json()
    return data

league_data = fetch_league_data()

league_name = league_data.get("league", {}).get("name", "FPL Mini-League Dashboard")
st.markdown(f'<h1 style="text-align:center; margin-bottom: 1.5rem; font-size:2.2rem;">{league_name}</h1>', unsafe_allow_html=True)

standings = league_data["standings"]["results"]
df = pd.DataFrame(standings)
df = df[["rank_sort", "last_rank", "entry_name", "player_name", "total", "event_total"]]
df = df.rename(columns={"rank_sort": "rank", "last_rank": "previous rank"})

# Add movement indicator to rank column

# Show rank with rank change in parenthesis, color-coded
# Show rank with rank change in parenthesis, using HTML for color
def rank_with_change_html(row):
    change = row["previous rank"] - row["rank"]

    if row["previous rank"] == 0 or change == 0:
        return f'{row["rank"]}'

    if change > 0:
        # moved up
        return f'{row["rank"]} <span style="color:green">(+{change})</span>'
    else:
        # moved down
        return f'{row["rank"]} <span style="color:red">({change})</span>'


# Helper to capitalize all words and words after hyphens
def smart_title(name):
    # Capitalize first letter of each word and after hyphens, preserving non-ASCII
    def cap(match):
        return match.group(0).capitalize()
    # Capitalize after start or after space or hyphen
    return re.sub(r'(^|[\s-])([\wæøåÆØÅéÉäöüßçñ]+)', lambda m: m.group(1) + m.group(2).capitalize(), name, flags=re.UNICODE)
    return re.sub(r'(^|[\s-])([\wæøåÆØÅéÉäöüßçñ]+)', lambda m: m.group(1) + m.group(2).capitalize(), name, flags=re.UNICODE)

df["Rank"] = df.apply(rank_with_change_html, axis=1)
df["Lag"] = df["entry_name"]
df["Spiller"] = df["player_name"].apply(smart_title)
df["Runde"] = df["event_total"]
df["Poeng"] = df["total"].apply(lambda x: f"**{x}**")


# Calculate round rank (Runderank) based on 'Runde' score
df["Runderank"] = df["Runde"].rank(method="min", ascending=False).astype(int)

# Add medal emojis for top 3
def add_medal(rank):
    if rank == 1:
        return "1 🥇"
    elif rank == 2:
        return "2 🥈"
    elif rank == 3:
        return "3 🥉"
    else:
        return str(rank)
df["Runderank"] = df["Runderank"].apply(add_medal)

# Reorder columns: Rank, Lag, Spiller, Runde, Runderank, Poeng
df = df[["Rank", "Lag", "Spiller", "Runde", "Runderank", "Poeng"]]

# Build markdown table with HTML
def df_to_markdown_html(df):
    headers = df.columns.tolist()
    md = "| " + " | ".join(headers) + " |\n"
    md += "|" + "---|" * len(headers) + "\n"
    for _, row in df.iterrows():
        md += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    return md

st.markdown(df_to_markdown_html(df), unsafe_allow_html=True)
