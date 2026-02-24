import json
from pathlib import Path
from typing import Any

import requests


class FPL_API:
    """
    Handles all communication with the FPL API and manages sample data for dev mode.
    """
    BASE_URL: str = "https://fantasy.premierleague.com/api"
    DEFAULT_SAMPLE_DATA_DIR: Path = Path(__file__).parent / "sample_data"


    dev_mode: bool
    sample_data_dir: Path

    def __init__(self, dev_mode: bool = False, sample_data_dir: Any = None) -> None:
        """
        :param dev_mode: If True, use sample data files instead of live API.
        :param sample_data_dir: Optional override for sample data directory (for testing).
        """
        self.dev_mode = dev_mode
        self.sample_data_dir = sample_data_dir if sample_data_dir is not None else self.DEFAULT_SAMPLE_DATA_DIR

    def _get(self, endpoint: str) -> dict | list:
        """
        Fetches data from the API or sample files, depending on dev_mode.
        :param endpoint: API endpoint string (e.g., '/entry/123/')
        :return: Parsed JSON response as a dict or list
        """
        if self.dev_mode:
            return self._read_sample_or_generate(endpoint)
        return self._call_api(endpoint)

    def _call_api(self, endpoint: str) -> dict | list:
        """
        Calls the FPL API and returns the JSON response.
        :param endpoint: API endpoint string
        :return: Parsed JSON response as a dict or list
        :raises requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def _read_sample_or_generate(self, endpoint: str) -> dict | list:
        """
        Reads sample data from disk, or generates it by calling the API if not present.
        :param endpoint: API endpoint string
        :return: Parsed JSON response as a dict or list
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
        result = self._get(endpoint)
        assert isinstance(result, dict)
        return result

    def get_team(self, team_id: str) -> dict:
        """
        Get team data for a given team ID.
        :param team_id: The team ID
        :return: Team data as a dict
        """
        endpoint = f"/entry/{team_id}/"
        result = self._get(endpoint)
        assert isinstance(result, dict)
        return result

    def get_team_history(self, team_id: str) -> dict:
        """
        Get team history for a given team ID.
        :param team_id: The team ID
        :return: Team history data as a dict
        """
        endpoint = f"/entry/{team_id}/history/"
        result = self._get(endpoint)
        assert isinstance(result, dict)
        return result

    def get_team_picks(self, team_id: str, event_id: str) -> dict:
        """
        Get team picks for a given team ID and event ID.
        :param team_id: The team ID
        :param event_id: The event (gameweek) ID
        :return: Team picks data as a dict
        """
        endpoint = f"/entry/{team_id}/event/{event_id}/picks/"
        result = self._get(endpoint)
        assert isinstance(result, dict)
        return result

    def get_transfers(self, team_id: str) -> list:
        """
        Get transfer history for a given team ID.
        :param team_id: The team ID
        :return: Transfer history as a list of dicts
        """
        endpoint = f"/entry/{team_id}/transfers/"
        result = self._get(endpoint)
        assert isinstance(result, list)
        return result

    def get_event_live(self, event_id: str) -> dict:
        """
        Get live event data for a given event (gameweek) ID.
        :param event_id: The event (gameweek) ID
        :return: Live event data as a dict
        """
        endpoint = f"/event/{event_id}/live/"
        result = self._get(endpoint)
        assert isinstance(result, dict)
        return result

    def get_bootstrap_static(self) -> dict:
        """
        Get the bootstrap static data (global FPL data).
        :return: Bootstrap static data as a dict
        """
        endpoint = "/bootstrap-static/"
        result = self._get(endpoint)
        assert isinstance(result, dict)
        return result
