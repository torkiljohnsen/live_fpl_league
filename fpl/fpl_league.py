from fpl import FPL_API
from datetime import datetime, timezone
import pandas as pd

class FPLLeague:
    CHIP_ABBREVIATIONS = {
        "wildcard": "WC",
        "freehit": "FH",
        "bboost": "BB",
        "3xc": "TC",
    }
    def __init__(self, league_id: str, dev_mode: bool = False):
        self.league_id = league_id
        self.fpl_api = FPL_API(dev_mode=dev_mode)
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
        self._apply_history_ranks(results)
        return results

    def _apply_history_ranks(self, participants):
        # Flatten all histories into a DataFrame
        rows = []
        for p in participants:
            for h in p["history"]:
                row = dict(h)
                row["entry_id"] = p["entry_id"]
                rows.append(row)
        df = pd.DataFrame(rows)

        # Calculate round_rank (by net_points) and league_rank (by total_points) per event
        df["round_rank"] = df.groupby("event")["net_points"].rank(method="min", ascending=False).astype(int)
        df["league_rank"] = df.groupby("event")["total_points"].rank(method="min", ascending=False).astype(int)

        # Calculate league_rank_change per participant
        df = df.sort_values(["entry_id", "event"])
        df["league_rank_change"] = df.groupby("entry_id")["league_rank"].diff().fillna(0).astype(int) * -1

        # Write back to participants' history
        for p in participants:
            entry_id = p["entry_id"]
            p_hist = df[df["entry_id"] == entry_id]
            for h, row in zip(p["history"], p_hist.to_dict(orient="records")):
                h["round_rank"] = row["round_rank"]
                h["league_rank"] = row["league_rank"]
                h["league_rank_change"] = row["league_rank_change"]

    def _build_participant(self, entry):
        history = self.fpl_api.get_team_history(str(entry["entry"]))
        finished_history = self._get_finished_history(history["current"])
        chips = history.get("chips", [])
        if chips:
            finished_history = self._add_chips(chips, finished_history)

        last_event = next((e for e in finished_history if e["event"] == self.info["latest_finished_event_id"]), None)
        return {
            "entry_id": entry["entry"],
            "team_name": entry["entry_name"],
            "manager_name": entry["player_name"],
            "total_score": last_event.get("total_points", 0) if last_event else 0,
            "history": finished_history,
            "last_event": last_event,
        }

    def _add_chips(self, chips, finished_history):
        for chip in chips:
            abbr = self.CHIP_ABBREVIATIONS.get(chip.get("name"))
            for event in finished_history:
                if event["event"] == chip.get("event") and abbr:
                    event["chip"] = abbr
        return finished_history

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