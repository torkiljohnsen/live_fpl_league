import requests
import json
from pathlib import Path
from typing import Any


class FPL_API:
    """
    Handles all communication with the FPL API and manages sample data for dev mode.
    """
    BASE_URL = "https://fantasy.premierleague.com/api"
    DEFAULT_SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"


    def __init__(self, dev_mode: bool = False, sample_data_dir: Any = None):
        """
        :param dev_mode: If True, use sample data files instead of live API.
        :param sample_data_dir: Optional override for sample data directory (for testing).
        """
        self.dev_mode = dev_mode
        self.sample_data_dir = sample_data_dir if sample_data_dir is not None else self.DEFAULT_SAMPLE_DATA_DIR

    def _get(self, endpoint: str) -> dict:
        """
        Fetches data from the API or sample files, depending on dev_mode.
        :param endpoint: API endpoint string (e.g., '/entry/123/')
        :return: Parsed JSON response as a dict
        """
        if self.dev_mode:
            return self._read_sample_or_generate(endpoint)
        return self._call_api(endpoint)

    def _call_api(self, endpoint: str) -> dict:
        """
        Calls the FPL API and returns the JSON response.
        :param endpoint: API endpoint string
        :return: Parsed JSON response as a dict
        :raises requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def _read_sample_or_generate(self, endpoint: str) -> dict:
        """
        Reads sample data from disk, or generates it by calling the API if not present.
        :param endpoint: API endpoint string
        :return: Parsed JSON response as a dict
        """
        sample_name = endpoint.replace('/', '_').strip('_')
        sample_path = self.sample_data_dir / f"{sample_name}_sample.json"
        if not sample_path.exists():
            print(f"[dev_mode] API called and sample generated: {sample_path}")
            data = self._call_api(endpoint)
            sample_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            print(f"[dev_mode] Sample read: {sample_path}")
        return json.loads(sample_path.read_text(encoding="utf-8"))

    def get_league_standings(self, league_id: str) -> dict:
        """
        Get league standings for a given league ID.
        :param league_id: The league ID
        :return: League standings data as a dict
        """
        endpoint = f"/leagues-classic/{league_id}/standings/"
        return self._get(endpoint)

    def get_team(self, team_id: str) -> dict:
        """
        Get team data for a given team ID.
        :param team_id: The team ID
        :return: Team data as a dict
        """
        endpoint = f"/entry/{team_id}/"
        return self._get(endpoint)

    def get_team_history(self, team_id: str) -> dict:
        """
        Get team history for a given team ID.
        :param team_id: The team ID
        :return: Team history data as a dict
        """
        endpoint = f"/entry/{team_id}/history/"
        return self._get(endpoint)

    def get_team_picks(self, team_id: str, event_id: str) -> dict:
        """
        Get team picks for a given team ID and event ID.
        :param team_id: The team ID
        :param event_id: The event (gameweek) ID
        :return: Team picks data as a dict
        """
        endpoint = f"/entry/{team_id}/event/{event_id}/picks/"
        return self._get(endpoint)

    def get_bootstrap_static(self) -> dict:
        """
        Get the bootstrap static data (global FPL data).
        :return: Bootstrap static data as a dict
        """
        endpoint = "/bootstrap-static/"
        return self._get(endpoint)
