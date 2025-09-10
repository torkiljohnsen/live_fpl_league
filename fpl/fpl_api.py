import requests
import json
from pathlib import Path
from typing import Any


class FPL_API:
    BASE_URL = "https://fantasy.premierleague.com/api"
    SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"

    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode

    def _get(self, endpoint: str) -> Any:
        if self.dev_mode:
            return self._read_sample_or_generate(endpoint)
        return self._call_api(endpoint)

    def _call_api(self, endpoint: str) -> Any:
        url = f"{self.BASE_URL}{endpoint}"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def _read_sample_or_generate(self, endpoint: str) -> Any:
        # Generate sample_name from endpoint by replacing slashes with underscores and stripping leading/trailing underscores
        sample_name = endpoint.replace('/', '_').strip('_')
        sample_path = self.SAMPLE_DATA_DIR / f"{sample_name}_sample.json"
        if not sample_path.exists():
            data = self._call_api(endpoint)
            sample_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return json.loads(sample_path.read_text(encoding="utf-8"))

    def get_league_standings(self, league_id: str) -> Any:
        endpoint = f"/leagues-classic/{league_id}/standings/"
        return self._get(endpoint)

    def get_team(self, team_id: str) -> Any:
        endpoint = f"/entry/{team_id}/"
        return self._get(endpoint)

    def get_team_history(self, team_id: str) -> Any:
        endpoint = f"/entry/{team_id}/history/"
        return self._get(endpoint)

    def get_team_picks(self, team_id: str, event_id: str) -> Any:
        endpoint = f"/entry/{team_id}/event/{event_id}/picks/"
        return self._get(endpoint)

    def get_bootstrap_static(self) -> Any:
        endpoint = "/bootstrap-static/"
        return self._get(endpoint)
