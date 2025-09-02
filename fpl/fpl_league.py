from fpl.fpl_api import FPL_API
from datetime import datetime, timezone

class FPLLeague:
    def __init__(self, league_id: str, fpl_api: FPL_API):
        self.league_id = league_id
        self.fpl_api = fpl_api
        self.bootstrap = self.fpl_api.get_bootstrap_static()
        self._set_events_list()
        self._set_finished_event_ids()
        self._init_league_data()

    def _set_events_list(self):
        self.event_ids = sorted(event['id'] for event in self.bootstrap['events'])

    def _set_finished_event_ids(self):
        self.finished_event_ids = [event["id"] for event in self.bootstrap["events"] if event["finished"]]

    def _init_league_data(self):
        league_data = self.fpl_api.get_league_standings(self.league_id)
        self.info = league_data["league"]
        self.info["latest_finished_event_id"] = max(self.finished_event_ids)
        self.teams = league_data["standings"]["results"]
        self.info["next_event_deadline_time"] = self.get_next_deadline_time()

    def get_next_deadline_time(self):
        latest_finished_event_id = self.info["latest_finished_event_id"]
        for event in sorted(self.bootstrap["events"], key=lambda e: e["id"]):
            if event["id"] > latest_finished_event_id and not event["finished"]:
                return event.get("deadline_time")
        return None

    def get_participants(self):
        results = []
        for entry in self.teams:
            participant = self._build_participant(entry)
            results.append(participant)
        # Sort by total_score descending
        results.sort(key=lambda p: p["total_score"], reverse=True)
        return results

    def _build_participant(self, entry):
        history = self.fpl_api.get_team_history(str(entry["entry"]))
        finished_history = self._get_finished_history(history["current"])
        latest_finished_event_id = self.info["latest_finished_event_id"]
        last_event = next((e for e in finished_history if e["event"] == latest_finished_event_id), None)
        return {
            "entry_id": entry["entry"],
            "team_name": entry["entry_name"],
            "manager_name": entry["player_name"],
            "latest_gw": latest_finished_event_id,
            "latest_score": last_event["points"] if last_event else 0,
            "latest_net_score": last_event["net_points"] if last_event else 0,
            "latest_event_transfer_cost": last_event.get("event_transfers_cost", 0) if last_event else 0,
            "total_score": last_event.get("total_points", 0) if last_event else 0,
            "history": finished_history,
        }

    def _get_finished_history(self, history_list):
        finished = []
        for e in history_list:
            if e["event"] in self.finished_event_ids:
                event_copy = dict(e)
                event_copy["net_points"] = e.get("points", 0) - e.get("event_transfers_cost", 0)
                finished.append(event_copy)
        return finished

    def get_summary(self):
        summary = dict(self.info)
        summary["generated_time"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        summary["participants"] = self.get_participants()
        summary["event_ids"] = self.event_ids
        return summary