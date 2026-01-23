import json
from pathlib import Path

from fpl.fpl_league import FPLLeague


class DummyAPI:
    def __init__(self, data_dir, chips=None, all_events_finished=False):
        self.data_dir = Path(data_dir)
        self._chips = chips
        self._all_events_finished = all_events_finished

    def get_bootstrap_static(self):
        data = json.loads((self.data_dir / "bootstrap-static_sample.json").read_text(encoding="utf-8"))
        if self._all_events_finished:
            # Mark all events as finished and no next event
            for event in data["events"]:
                event["finished"] = True
                event["is_next"] = False
        return data

    def get_league_standings(self, league_id):
        path = self.data_dir / f"leagues-classic_{league_id}_standings_sample.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def get_team_history(self, team_id):
        data = json.loads((self.data_dir / "entry_811114_history_sample.json").read_text(encoding="utf-8"))
        if self._chips is not None:
            data["chips"] = self._chips
        return data

    def get_team(self, team_id):
        return {}

    def get_team_picks(self, team_id, event_id):
        return {}

data_dir = Path(__file__).parent / "data_samples"
LEAGUE_ID = "1639886"

def test_fpl_league_summary():
    api = DummyAPI(data_dir)
    league = FPLLeague(LEAGUE_ID, api)
    summary = league.get_summary_as_dicts()
    assert summary["id"] == int(LEAGUE_ID)
    assert "participants" in summary
    assert isinstance(summary["participants"], list)
    assert summary["event_ids"]
    # Check participant fields - participants are dicts from get_summary_as_dicts()
    for p in summary["participants"]:
        assert "entry_id" in p
        assert "team_name" in p
        assert "manager_name" in p
        assert "total_score" in p
        assert "history" in p
        assert isinstance(p["history"], list)
        if p["history"]:
            h = p["history"][0]
            assert "event" in h
            assert "net_points" in h
            assert "round_rank" in h
            assert "league_rank" in h
            assert "league_rank_change" in h


def test_get_next_deadline_time_returns_none():
    api = DummyAPI(data_dir, all_events_finished=True)
    league = FPLLeague(LEAGUE_ID, api)
    assert league.info["next_event_deadline_time"] is None


def test_participant_with_chip():
    chips = [{"name": "wildcard", "event": 1}]
    api = DummyAPI(data_dir, chips=chips)
    league = FPLLeague(LEAGUE_ID, api)
    participants = league.get_participants()
    found_chip = False
    for p in participants:
        for h in p.history:
            if h.get("chip") == "WC":
                found_chip = True
    assert found_chip, "Wildcard chip abbreviation should be present in participant history"
