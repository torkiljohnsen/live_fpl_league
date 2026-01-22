from typing import Any

from .chart_generator import generate_rank_progression_chart
from .fpl_api import FPL_API
from .fpl_league import FPLLeague

LOGO_PATH = "assets/fpl_logo.svg"


class LeagueContext:
    league_data: dict[str, Any]
    league_join_code: str | None
    logo_svg: str
    dev_mode: bool

    def __init__(
        self, league_data: dict[str, Any], league_join_code: str | None, logo_svg: str, dev_mode: bool = False
    ) -> None:
        self.league_data = league_data
        self.league_join_code = league_join_code
        self.logo_svg = logo_svg
        self.dev_mode = dev_mode

    @classmethod
    def build(
        cls,
        league_id: str,
        dev_mode: bool,
        league_join_code: str | None,
        fpl_api: Any = None,
    ) -> "LeagueContext":
        if fpl_api is None:
            fpl_api = FPL_API(dev_mode=dev_mode)
        league = FPLLeague(league_id, fpl_api)
        league_data = league.get_summary()
        logo_svg = cls._get_logo_svg()
        return cls(
            league_data=league_data,
            league_join_code=league_join_code,
            logo_svg=logo_svg,
            dev_mode=dev_mode
        )

    @staticmethod
    def _get_logo_svg() -> str:
        with open(LOGO_PATH, encoding="utf-8") as f:
            return f.read()

    @property
    def id(self) -> Any:
        return self.league_data.get("id") or self.league_data.get("league", {}).get("id")

    @staticmethod
    def get_gw_column_sets(event_ids, last_event=None, max_cols=15):
        # Only consider events up to last_event for hiding
        if last_event is not None:
            visible_event_ids = [e for e in event_ids if e <= last_event]
        else:
            visible_event_ids = list(event_ids)

        golden_event_ids = [e for e in visible_event_ids if e % 4 == 0]
        non_golden_event_ids = [e for e in visible_event_ids if e % 4 != 0]

        # Only start hiding after max_cols events
        if len(visible_event_ids) <= max_cols:
            hidden_event_ids = set()
        else:
            num_to_hide = len(visible_event_ids) - max_cols
            # Hide the oldest non-golden events first
            non_golden_sorted = sorted(non_golden_event_ids)
            hidden_event_ids = set(non_golden_sorted[:num_to_hide])
        return set(golden_event_ids), hidden_event_ids

    def get_last_event(self) -> int | None:
        """Get the last active event (current event or latest finished event)."""
        current_event_id = self.league_data.get("current_event_id")
        finished_event_ids = self.league_data.get("finished_event_ids", [])
        # Use current event if it exists, otherwise fall back to max finished event
        return current_event_id if current_event_id else (max(finished_event_ids) if finished_event_ids else None)

    def as_dict(self) -> dict[str, Any]:
        d = dict(self.league_data)
        d["league_join_code"] = self.league_join_code
        d["logo_svg"] = self.logo_svg
        d["dev_mode"] = self.dev_mode
        event_ids = d.get("event_ids", [])
        last_event = self.get_last_event()
        golden_event_ids, hidden_event_ids = self.get_gw_column_sets(event_ids, last_event=last_event)
        d["golden_event_ids"] = golden_event_ids
        d["hidden_event_ids"] = hidden_event_ids

        # Generate rank progression chart
        participants = d.get("participants", [])
        if participants:
            # Convert Participant objects to dictionaries for chart generator
            participants_for_chart = []
            for p in participants:
                # Extract first name from manager_name
                first_name = p.manager_name.split()[0] if p.manager_name else 'Unknown'
                participants_for_chart.append({
                    'player_first_name': first_name,
                    'history': p.history
                })

            chart_svg = generate_rank_progression_chart(
                participants=participants_for_chart,
                theme="light",
                output_format="svg"
            )
            d["rank_progression_chart"] = chart_svg

        return d
