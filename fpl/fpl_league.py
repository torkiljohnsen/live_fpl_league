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
    event_ids: List[int]  # All events
    finished_event_ids: List[int]  # Events that are finished
    current_event_id: Optional[int]  # Event that is current (ongoing)
    info: Dict[str, Any]
    teams: List[Dict[str, Any]]

    def __init__(self, league_id: str, fpl_api: FPLAPIProtocol) -> None:
        self.league_id = league_id
        self.fpl_api = fpl_api
        self.bootstrap = self.fpl_api.get_bootstrap_static()
        self._set_events_list()
        self._set_event_status_markers()
        self._init_league_data()

    def _set_events_list(self) -> None:
        self.event_ids = sorted(event['id'] for event in self.bootstrap['events'])

    def _set_event_status_markers(self) -> None:
        """Set up markers for event status: finished events and current event."""
        self.finished_event_ids = [event["id"] for event in self.bootstrap["events"] if event["finished"]]
        # Find the single current event
        for event in self.bootstrap["events"]:
            if event.get("is_current", False):
                self.current_event_id = event["id"]
                break
        else:
            # If no current event found, use the latest finished event
            self.current_event_id = max(self.finished_event_ids) if self.finished_event_ids else None

    def _init_league_data(self) -> None:
        league_data = self.fpl_api.get_league_standings(self.league_id)
        self.info = league_data["league"]
        self.teams = league_data["standings"]["results"]
        self.get_next_event()

    def get_next_event(self) -> None:
        """Find the next event and set deadline time with CET timezone conversion."""
        from datetime import datetime, timezone, timedelta
        
        # Find the event with is_next = true
        next_event = next((event for event in self.bootstrap["events"] if event.get("is_next", False)), None)
        
        if next_event:
            self.info["next_event_id"] = next_event["id"]
            # Convert from GMT to CET (GMT+1, or GMT+2 during daylight saving)
            # For now, assuming CET = GMT+2 (daylight saving)
            cet_timezone = timezone(timedelta(hours=2))
            deadline_utc = datetime.fromisoformat(next_event["deadline_time"].replace('Z', '+00:00'))
            deadline_cet = deadline_utc.astimezone(cet_timezone)
            self.info["next_event_deadline_time"] = deadline_cet.isoformat()
        else:
            self.info["next_event_id"] = None
            self.info["next_event_deadline_time"] = None

    def get_participants(self) -> List[Participant]:
        results: List[Participant] = []
        for entry in self.teams:
            participant = self._build_participant(entry)
            results.append(participant)
        results.sort(key=lambda p: p.total_score, reverse=True)
        RankCalculator.apply_history_ranks(results)
        self._calculate_rubber_duck_counts(results)
        return results

    def _build_participant(self, entry: Dict[str, Any]) -> Participant:
        history = self.fpl_api.get_team_history(str(entry["entry"]))
        complete_history = self._get_complete_history(history["current"])
        chips: List[Dict[str, Any]] = history.get("chips", [])
        if chips:
            complete_history = ChipAnnotator.add_chips(chips, complete_history)
        
        # Find the latest event with activity (current or finished)
        latest_active_event_id = self.current_event_id if self.current_event_id else (max(self.finished_event_ids) if self.finished_event_ids else 0)
        last_event = next((e for e in complete_history if e["event"] == latest_active_event_id), None)
        
        # Ensure last_event is never None by creating a default event
        if last_event is None:
            last_event = {
                "event": latest_active_event_id,
                "points": 0,
                "total_points": 0,
                "event_transfers_cost": 0,
                "net_points": 0,
                "chip": None,
            }
            # Add the default event to history so RankCalculator can process it
            complete_history.append(last_event)
        
        return Participant(
            entry_id=entry["entry"],
            team_name=entry["entry_name"],
            manager_name=entry["player_name"],
            total_score=last_event.get("total_points", 0),
            history=complete_history,
            last_event=last_event,
        )

    def _get_complete_history(self, history_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get complete history with net_points calculation."""
        complete: List[Dict[str, Any]] = []
        for e in history_list:
            event_copy = dict(e)
            event_copy["net_points"] = e.get("points", 0) - e.get("event_transfers_cost", 0)
            complete.append(event_copy)
        return complete

    def _calculate_rubber_duck_counts(self, participants: List[Participant]) -> None:
        """Calculate rubber duck count for each participant.
        
        A participant gets a rubber duck for each event where they had the lowest score.
        This handles ties correctly - if multiple participants have the same lowest score,
        they all get a rubber duck for that event.
        """
        # Build a map of event -> min_net_points
        from collections import defaultdict
        event_min_points: Dict[int, float] = {}
        
        # First pass: find minimum net_points for each event
        for participant in participants:
            for history_entry in participant.history:
                event_id = history_entry.get("event")
                net_points = history_entry.get("net_points", 0)
                if event_id is not None:
                    if event_id not in event_min_points:
                        event_min_points[event_id] = net_points
                    else:
                        event_min_points[event_id] = min(event_min_points[event_id], net_points)
        
        # Second pass: count rubber ducks for each participant
        for participant in participants:
            rubber_duck_count = 0
            for history_entry in participant.history:
                event_id = history_entry.get("event")
                net_points = history_entry.get("net_points", 0)
                # A participant gets a duck if they have the minimum score for that event
                if event_id in event_min_points and net_points == event_min_points[event_id]:
                    rubber_duck_count += 1
            participant.rubber_duck_count = rubber_duck_count


    def get_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = dict(self.info)
        summary["generated_time"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        summary["participants"] = self.get_participants()
        summary["event_ids"] = self.event_ids  # All events
        summary["finished_event_ids"] = self.finished_event_ids  # Finished events marker
        summary["current_event_id"] = self.current_event_id  # Current event marker
        summary["is_current_finished"] = self.current_event_id in self.finished_event_ids if self.current_event_id else False
        return summary