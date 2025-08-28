import requests
import json
from pathlib import Path
from typing import Any


class FPL:
    BASE_URL = "https://fantasy.premierleague.com/api"
    SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"
    SAMPLE_LEAGUE_ID = "1639886"
    SAMPLE_TEAM_ID = "811114"


    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode

    def _get(self, endpoint: str) -> Any:
        if self.dev_mode:
            sample_name = endpoint.replace('/', '_').strip('_')
            return self._read_sample_or_generate(endpoint, sample_name)
        return self._call_api(endpoint)

    def _call_api(self, endpoint: str) -> Any:
        url = f"{self.BASE_URL}{endpoint}"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def _read_sample_or_generate(self, endpoint: str, sample_name: str) -> Any:
        sample_path = self.SAMPLE_DATA_DIR / f"{sample_name}_sample.json"
        if not sample_path.exists():
            data = self._call_api(endpoint)
            sample_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return json.loads(sample_path.read_text(encoding="utf-8"))

    def get_league_standings(self, league_id: str) -> Any:
        endpoint = f"/leagues-classic/{self.SAMPLE_LEAGUE_ID if self.dev_mode else league_id}/standings/"
        return self._get(endpoint)

    def get_team(self, team_id: str) -> Any:
        endpoint = f"/entry/{self.SAMPLE_TEAM_ID if self.dev_mode else team_id}/"
        return self._get(endpoint)

    def get_team_history(self, team_id: str) -> Any:
        endpoint = f"/entry/{self.SAMPLE_TEAM_ID if self.dev_mode else team_id}/history/"
        return self._get(endpoint)

    def get_team_picks(self, team_id: str, event_id: str) -> Any:
        endpoint = f"/entry/{self.SAMPLE_TEAM_ID if self.dev_mode else team_id}/event/{event_id}/picks/"
        return self._get(endpoint)

    def get_bootstrap_static(self) -> Any:
        endpoint = "/bootstrap-static/"
        return self._get(endpoint)


if __name__ == "__main__":
    # Regenerate all sample data files using sample IDs
    fpl = FPL(dev_mode=True)
    # Delete all sample files
    for sample_file in fpl.SAMPLE_DATA_DIR.glob("*_sample.json"):
        sample_file.unlink()
    # Call each get_* method to regenerate
    print("Regenerating sample data files...")
    fpl.get_bootstrap_static()
    fpl.get_league_standings(FPL.SAMPLE_LEAGUE_ID)
    fpl.get_team(FPL.SAMPLE_TEAM_ID)
    fpl.get_team_history(FPL.SAMPLE_TEAM_ID)
    # For team_picks, use event_id=1 as a sample (can be changed if needed)
    fpl.get_team_picks(FPL.SAMPLE_TEAM_ID, "1")
    print("Sample data regeneration complete.")
