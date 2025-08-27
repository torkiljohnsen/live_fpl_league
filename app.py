import streamlit as st
import pandas as pd
import requests

st.title("My FPL Mini-League Dashboard")

# Example: Fetch sample data from FPL API
LEAGUE_ID = "1639886"  # replace with your league ID

@st.cache_data(ttl=3600)  # cache for 1 hour
def fetch_standings():
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"
    r = requests.get(url)
    data = r.json()
    standings = data["standings"]["results"]
    df = pd.DataFrame(standings)
    return df[["entry_name", "player_name", "total"]]

df = fetch_standings()
st.dataframe(df.sort_values("total", ascending=False).reset_index(drop=True))
