import pandas as pd
from typing import Any, List
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
        for p in participants:
            entry_id = p.entry_id
            p_hist = df[df["entry_id"] == entry_id]
            for h, row in zip(p.history, p_hist.to_dict(orient="records")):
                h["round_rank"] = row["round_rank"]
                h["league_rank"] = row["league_rank"]
                h["league_rank_change"] = row["league_rank_change"]
