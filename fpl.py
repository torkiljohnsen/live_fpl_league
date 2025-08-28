import requests


class FPL:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def get_league_standings(self, league_id):
        url = f"{self.BASE_URL}/leagues-classic/{league_id}/standings/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()


    def get_team(self, team_id):
        url = f"{self.BASE_URL}/entry/{team_id}/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()


    def get_team_history(self, team_id):
        url = f"{self.BASE_URL}/entry/{team_id}/history/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()


    def get_team_picks(self, team_id, event_id):
        url = f"{self.BASE_URL}/entry/{team_id}/event/{event_id}/picks/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def get_bootstrap_static(self):
        url = f"{self.BASE_URL}/bootstrap-static/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
