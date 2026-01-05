import pandas as pd
from typing import Any, Dict, List, Union
from .participant import Participant

class RankCalculator:
    @staticmethod
    def apply_history_ranks(participants: List[Participant]) -> None:
        rows: List[dict[str, Any]] = []
        for p in participants:
            for h in p.history:
                row = dict(h)
                row["entry_id"] = p.entry_id
                rows.append(row)
        df = pd.DataFrame(rows)
        if df.empty:
            return
        df["round_rank"] = df.groupby("event")["net_points"].rank(method="min", ascending=False).astype(int)
        df["league_rank"] = df.groupby("event")["total_points"].rank(method="min", ascending=False).astype(int)
        df = df.sort_values(["entry_id", "event"])
        df["league_rank_change"] = df.groupby("entry_id")["league_rank"].diff().fillna(0).astype(int) * -1
        
        # Calculate min and max net_points for each event to determine highest/lowest rank
        event_min_points = df.groupby("event")["net_points"].min().to_dict()
        event_max_points = df.groupby("event")["net_points"].max().to_dict()
        
        for p in participants:
            entry_id = p.entry_id
            p_hist = df[df["entry_id"] == entry_id]
            for h, row in zip(p.history, p_hist.to_dict(orient="records")):
                h["round_rank"] = row["round_rank"]
                h["league_rank"] = row["league_rank"]
                h["league_rank_change"] = row["league_rank_change"]
                
                # Add flags for highest/lowest rank based on net_points
                event_id = h.get("event")
                net_points = h.get("net_points", 0)
                h["is_lowest_rank"] = (event_id in event_min_points and net_points == event_min_points[event_id])
                h["is_highest_rank"] = (event_id in event_max_points and net_points == event_max_points[event_id])
    
    @staticmethod
    def calculate_lowest_rank_counts(participants: List[Participant]) -> None:
        """Calculate the count of times each participant achieved the lowest rank.
        
        This counts how many events each participant had the minimum net_points.
        Handles ties correctly - if multiple participants have the same lowest score,
        they all get counted.
        """
        for participant in participants:
            lowest_rank_count = 0
            for history_entry in participant.history:
                if history_entry.get("is_lowest_rank", False):
                    lowest_rank_count += 1
            participant.lowest_rank_count = lowest_rank_count
    
    @staticmethod
    def calculate_win_counts(participants: List[Participant]) -> None:
        """Calculate the count of gameweek wins for each participant.
        
        This counts how many events each participant had round_rank == 1 (winner).
        Also tracks golden gameweek wins (events where event % 4 == 0).
        Handles ties correctly - if multiple participants tie for first place,
        they all get counted as winners.
        """
        for participant in participants:
            win_count = 0
            golden_win_count = 0
            for history_entry in participant.history:
                if history_entry.get("round_rank") == 1:
                    win_count += 1
                    # Check if this is a golden gameweek (divisible by 4)
                    event_id = history_entry.get("event")
                    if event_id and event_id % 4 == 0:
                        golden_win_count += 1
            participant.win_count = win_count
            participant.golden_win_count = golden_win_count
