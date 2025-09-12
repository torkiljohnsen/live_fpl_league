from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .participant import Participant
from .rank_calculator import RankCalculator
from .fpl_api_protocol import FPLAPIProtocol
from .chip_annotator import ChipAnnotator

class FPLLeague:
    CHIP_ABBREVIATIONS: Dict[str, str] = {
        "wildcard": "WC",
        "freehit": "FH",
        "bboost": "BB",
        "3xc": "TC",
    }

    league_id: str
    fpl_api: FPLAPIProtocol
    bootstrap: Dict[str, Any]
    event_ids: List[int]
    finished_event_ids: List[int]
    info: Dict[str, Any]
    teams: List[Dict[str, Any]]

    def __init__(self, league_id: str, fpl_api: FPLAPIProtocol) -> None:
        self.league_id = league_id
        self.fpl_api = fpl_api
        self.bootstrap = self.fpl_api.get_bootstrap_static()
        self._set_events_list()
        self._set_finished_event_ids()
        self.latest_finished_event = max(self.finished_event_ids) if self.finished_event_ids else 0
        self._init_league_data()

    def _set_events_list(self) -> None:
        self.event_ids = sorted(event['id'] for event in self.bootstrap['events'])

    def _set_finished_event_ids(self) -> None:
        self.finished_event_ids = [event["id"] for event in self.bootstrap["events"] if event["finished"]]

    def _init_league_data(self) -> None:
        league_data = self.fpl_api.get_league_standings(self.league_id)
        self.info = league_data["league"]
        self.info["latest_finished_event_id"] = max(self.finished_event_ids)
        self.teams = league_data["standings"]["results"]
        self.info["next_event_deadline_time"] = self.get_next_deadline_time()

    def get_next_deadline_time(self) -> Optional[str]:
        latest_finished_event_id: int = self.info["latest_finished_event_id"]
        for event in sorted(self.bootstrap["events"], key=lambda e: e["id"]):
            if event["id"] > latest_finished_event_id and not event["finished"]:
                return event.get("deadline_time")
        return None

    def get_participants(self) -> List[Participant]:
        results: List[Participant] = []
        for entry in self.teams:
            participant = self._build_participant(entry)
            results.append(participant)
        results.sort(key=lambda p: p.total_score, reverse=True)
        RankCalculator.apply_history_ranks(results)
        return results

    def _build_participant(self, entry: Dict[str, Any]) -> Participant:
        history = self.fpl_api.get_team_history(str(entry["entry"]))
        finished_history = self._get_finished_history(history["current"])
        chips: List[Dict[str, Any]] = history.get("chips", [])
        if chips:
            finished_history = ChipAnnotator.add_chips(chips, finished_history)
        last_event = next((e for e in finished_history if e["event"] == self.info["latest_finished_event_id"]), None)
        return Participant(
            entry_id=entry["entry"],
            team_name=entry["entry_name"],
            manager_name=entry["player_name"],
            total_score=last_event.get("total_points", 0) if last_event else 0,
            history=finished_history,
            last_event=last_event,
        )

    def _get_finished_history(self, history_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        finished: List[Dict[str, Any]] = []
        for e in history_list:
            if e["event"] in self.finished_event_ids:
                event_copy = dict(e)
                event_copy["net_points"] = e.get("points", 0) - e.get("event_transfers_cost", 0)
                finished.append(event_copy)
        return finished


    def get_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = dict(self.info)
        summary["generated_time"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        summary["participants"] = self.get_participants()
        summary["event_ids"] = self.event_ids
        summary["latest_finished_event"] = self.latest_finished_event
        return summary