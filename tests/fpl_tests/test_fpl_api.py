import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fpl import FPL_API


@pytest.fixture(autouse=True)
def patch_requests_get():
	with patch("requests.get") as mock_get:
		mock_response = MagicMock()
		mock_response.json.return_value = {}
		mock_response.raise_for_status.return_value = None
		mock_get.return_value = mock_response
		yield mock_get

class TestFPLAPIDevMode:
	def setup_method(self):
		# Create a temp dir for sample data
		self.temp_dir = tempfile.mkdtemp()
		self.api = FPL_API(dev_mode=True, sample_data_dir=Path(self.temp_dir))

	def teardown_method(self):
		shutil.rmtree(self.temp_dir)

	def test_read_sample_or_generate_creates_sample(self, monkeypatch):
		# Simulate API call returns dummy data
		dummy_data = {"foo": "bar"}
		monkeypatch.setattr(self.api, "_call_api", lambda endpoint: dummy_data)
		# File should not exist yet
		sample_file = Path(self.temp_dir) / "bootstrap-static_sample.json"
		assert not sample_file.exists()
		# Call get_bootstrap_static (triggers _read_sample_or_generate)
		data = self.api.get_bootstrap_static()
		assert sample_file.exists()
		assert json.loads(sample_file.read_text(encoding="utf-8")) == dummy_data
		assert data == dummy_data

	def test_read_sample_or_generate_reads_existing_sample(self, monkeypatch):
		# Write a sample file first
		sample_file = Path(self.temp_dir) / "bootstrap-static_sample.json"
		sample_content = {"baz": 123}
		sample_file.write_text(json.dumps(sample_content), encoding="utf-8")
		# _call_api should not be called
		def raise_error(endpoint):
			raise Exception("Should not call API")
		monkeypatch.setattr(self.api, "_call_api", raise_error)
		data = self.api.get_bootstrap_static()
		assert data == sample_content

	def test_get_transfers_dev_mode(self, monkeypatch):
		transfers_data = [{"element_in": 1, "element_out": 2, "event": 1}]
		sample_file = Path(self.temp_dir) / "entry_811114_transfers_sample.json"
		sample_file.write_text(json.dumps(transfers_data), encoding="utf-8")
		monkeypatch.setattr(self.api, "_call_api", lambda e: (_ for _ in ()).throw(Exception("Should not call API")))
		data = self.api.get_transfers("811114")
		assert isinstance(data, list)
		assert data == transfers_data

	def test_get_event_live_dev_mode(self, monkeypatch):
		live_data = {"elements": [{"id": 1, "stats": {"total_points": 6}}]}
		sample_file = Path(self.temp_dir) / "event_1_live_sample.json"
		sample_file.write_text(json.dumps(live_data), encoding="utf-8")
		monkeypatch.setattr(self.api, "_call_api", lambda e: (_ for _ in ()).throw(Exception("Should not call API")))
		data = self.api.get_event_live("1")
		assert isinstance(data, dict)
		assert "elements" in data
		assert data == live_data

class TestFPLAPI:
	def setup_method(self):
		self.api = FPL_API(dev_mode=False)

	def test_get_bootstrap_static_calls_correct_url(self, patch_requests_get):
		self.api.get_bootstrap_static()
		patch_requests_get.assert_called_once_with("https://fantasy.premierleague.com/api/bootstrap-static/")

	def test_get_league_standings_calls_correct_url(self, patch_requests_get):
		league_id = "123456"
		self.api.get_league_standings(league_id)
		patch_requests_get.assert_called_once_with(f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/")

	def test_get_team_calls_correct_url(self, patch_requests_get):
		team_id = "654321"
		self.api.get_team(team_id)
		patch_requests_get.assert_called_once_with(f"https://fantasy.premierleague.com/api/entry/{team_id}/")

	def test_get_team_history_calls_correct_url(self, patch_requests_get):
		team_id = "654321"
		self.api.get_team_history(team_id)
		patch_requests_get.assert_called_once_with(f"https://fantasy.premierleague.com/api/entry/{team_id}/history/")

	def test_get_team_picks_calls_correct_url(self, patch_requests_get):
		team_id = "654321"
		event_id = "1"
		self.api.get_team_picks(team_id, event_id)
		patch_requests_get.assert_called_once_with(f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{event_id}/picks/")

	def test_get_transfers_calls_correct_url(self, patch_requests_get):
		team_id = "654321"
		mock_response = MagicMock()
		mock_response.json.return_value = []
		mock_response.raise_for_status.return_value = None
		patch_requests_get.return_value = mock_response
		self.api.get_transfers(team_id)
		patch_requests_get.assert_called_once_with(f"https://fantasy.premierleague.com/api/entry/{team_id}/transfers/")

	def test_get_event_live_calls_correct_url(self, patch_requests_get):
		event_id = "1"
		self.api.get_event_live(event_id)
		patch_requests_get.assert_called_once_with(f"https://fantasy.premierleague.com/api/event/{event_id}/live/")
