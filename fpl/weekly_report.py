"""Weekly report data collection, assembly, and JSON output.

Orchestrates data collection from the FPL API, builds
GameweekParticipantData dicts for each league participant,
calculates awards, and assembles the final report dict.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import weekly_report_stats as stats
from .fpl_api_protocol import FPLAPIProtocol
from .player_registry import PlayerRegistry


def get_season_from_bootstrap(bootstrap: dict[str, Any]) -> str:
    """Derive season string (e.g. '2025-26') from bootstrap data.

    Shared by WeeklyReport and CLI skip-existing logic.
    """
    events = bootstrap.get("events", [])
    if not events:
        return "unknown"
    first_deadline = events[0].get("deadline_time", "")
    if not first_deadline:
        return "unknown"
    year = int(first_deadline[:4])
    next_year_short = str(year + 1)[-2:]
    return f"{year}-{next_year_short}"


class WeeklyReport:
    """Collects gameweek data and builds participant data dicts.

    Constructor takes an API client, league ID, and event (gameweek) ID.
    The build() method fetches all required data and stores participant
    data internally for later assembly (report output, awards, etc.).
    """

    def __init__(
        self, api: FPLAPIProtocol, league_id: str, event_id: int
    ) -> None:
        self._api = api
        self._league_id = league_id
        self._event_id = event_id
        self._participants_data: list[dict[str, Any]] = []
        self._bootstrap: dict[str, Any] = {}
        self._league_name: str = ""
        self._report: dict[str, Any] = {}

    def build(self) -> dict[str, Any]:
        """Fetch all data, build participant data, and assemble the report.

        Fetches bootstrap, league standings, event live data, and
        per-participant picks and transfers. Builds GameweekParticipantData
        dicts, calculates awards, and returns the complete report dict
        with meta, standings, awards, and league_summary sections.
        """
        self._bootstrap = self._api.get_bootstrap_static()
        registry = PlayerRegistry(self._bootstrap)

        standings = self._api.get_league_standings(self._league_id)
        self._league_name = standings.get("league", {}).get("name", "")

        live_data = self._api.get_event_live(str(self._event_id))
        live_points = self._build_live_points_map(live_data)

        teams = standings.get("standings", {}).get("results", [])
        self._participants_data = []

        for team in teams:
            entry_id = team["entry"]
            picks_data = self._api.get_team_picks(
                str(entry_id), str(self._event_id)
            )
            all_transfers = self._api.get_transfers(str(entry_id))
            gw_transfers = [
                t for t in all_transfers if t.get("event") == self._event_id
            ]

            participant = self._build_participant_data(
                team, picks_data, gw_transfers, live_points, registry
            )
            self._participants_data.append(participant)

        # Sort standings by league rank
        self._participants_data.sort(key=lambda p: p.get("league_rank", 0))

        # Assemble the full report
        self._report = {
            "meta": self._build_meta(),
            "standings": self._participants_data,
            "awards": self._build_awards(),
            "league_summary": self._build_league_summary(),
        }

        return self._report

    def save_report(self, output_dir: str) -> str:
        """Write the report JSON to disk.

        Saves to {output_dir}/weekly_report/reports/{league_id}/{season}/gw{N}.json,
        creating directories as needed.

        Returns the path to the written file.
        """
        season = self._get_season()
        path = (
            Path(output_dir)
            / "weekly_report"
            / "reports"
            / self._league_id
            / season
            / f"gw{self._event_id}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(path)

    def _get_season(self) -> str:
        """Derive season string (e.g. '2025-26') from bootstrap events."""
        return get_season_from_bootstrap(self._bootstrap)

    def _build_meta(self) -> dict[str, Any]:
        """Build the meta section of the report."""
        season = self._get_season()
        prev_event = self._event_id - 1

        previous_report: str | None = None
        previous_narrative: str | None = None
        if prev_event >= 1:
            previous_report = (
                f"weekly_report/reports/{self._league_id}/{season}/gw{prev_event}.json"
            )
            previous_narrative = (
                f"docs/narratives/{season}/{self._league_id}/gw{prev_event}.md"
            )

        return {
            "league_id": self._league_id,
            "league_name": self._league_name,
            "season": season,
            "event_id": self._event_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "previous_report": previous_report,
            "previous_narrative": previous_narrative,
        }

    def _build_awards(self) -> dict[str, Any]:
        """Calculate all awards from participant data."""
        p = self._participants_data
        transfer_impact = stats.get_transfer_impact(p)
        best_transfer = transfer_impact["best"] if transfer_impact else None
        worst_transfer = transfer_impact["worst"] if transfer_impact else None

        return {
            "highest_scorer": stats.get_highest_gameweek_scorer(p),
            "lowest_scorer": stats.get_lowest_gameweek_scorer(p),
            "biggest_rise": stats.get_biggest_rank_rise(p),
            "biggest_fall": stats.get_biggest_rank_fall(p),
            "bench_disasters": stats.get_bench_disasters(p),
            "best_transfer": best_transfer,
            "worst_transfer": worst_transfer,
            "captain_summary": stats.get_captain_summary(p),
            "chip_usage": stats.get_chip_usage(p),
            "hit_takers": stats.get_hit_takers(p),
        }

    def _build_league_summary(self) -> dict[str, Any]:
        """Build the league summary section."""
        total = len(self._participants_data)
        if total == 0:
            return {
                "average_score": 0,
                "leader": None,
                "total_participants": 0,
            }

        net_scores = [p.get("net_points", 0) for p in self._participants_data]
        avg = sum(net_scores) / total

        leader = self._participants_data[0]

        return {
            "average_score": round(avg, 1),
            "leader": {
                "player_name": leader["player_first_name"],
                "total_points": leader["total_points"],
            },
            "total_participants": total,
        }

    def _build_live_points_map(
        self, live_data: dict[str, Any]
    ) -> dict[int, int]:
        """Build a map of element_id -> total_points from live event data."""
        points_map: dict[int, int] = {}
        for element in live_data.get("elements", []):
            points_map[element["id"]] = element["stats"]["total_points"]
        return points_map

    def _build_participant_data(
        self,
        team: dict[str, Any],
        picks_data: dict[str, Any],
        gw_transfers: list[dict[str, Any]],
        live_points: dict[int, int],
        registry: PlayerRegistry,
    ) -> dict[str, Any]:
        """Build a GameweekParticipantData dict for a single participant."""
        entry_history = picks_data.get("entry_history", {})
        picks = picks_data.get("picks", [])

        squad, captain_data, vice_captain_data, bench_points, bench_players = (
            self._build_squad_data(picks, live_points, registry)
        )

        event_total = entry_history.get("points", 0)
        transfer_cost = entry_history.get("event_transfers_cost", 0)
        net_points = event_total - transfer_cost

        chip_played = picks_data.get("active_chip")

        transfer_list = self._build_transfer_list(
            gw_transfers, live_points, registry
        )

        league_rank = team.get("rank", 0)
        league_rank_previous = team.get("last_rank", 0)
        # Positive change means climbed (e.g., 5->3 = +2)
        league_rank_change = league_rank_previous - league_rank

        manager_name = team.get("player_name", "Unknown")
        player_first_name = (
            manager_name.split()[0] if manager_name else "Unknown"
        )

        return {
            "entry_id": team["entry"],
            "team_name": team.get("entry_name", "Unknown"),
            "manager_name": manager_name,
            "player_first_name": player_first_name,
            # Points
            "event_total": event_total,
            "net_points": net_points,
            "total_points": team.get("total", 0),
            # Rank
            "league_rank": league_rank,
            "league_rank_previous": league_rank_previous,
            "league_rank_change": league_rank_change,
            "overall_rank": entry_history.get("overall_rank", 0),
            # Value
            "team_value": entry_history.get("value", 0) / 10,
            "bank": entry_history.get("bank", 0) / 10,
            # Bench
            "bench_points": bench_points,
            "bench_players": bench_players,
            # Chip
            "chip_played": chip_played,
            # Captain
            "captain": captain_data,
            "vice_captain": vice_captain_data,
            # Squad
            "squad": squad,
            # Transfers
            "transfers": transfer_list,
            "transfer_cost": transfer_cost,
            "transfers_made": entry_history.get("event_transfers", 0),
        }

    def _build_squad_data(
        self,
        picks: list[dict[str, Any]],
        live_points: dict[int, int],
        registry: PlayerRegistry,
    ) -> tuple[
        list[dict[str, Any]],
        dict[str, Any],
        dict[str, Any],
        int,
        list[dict[str, Any]],
    ]:
        """Build squad, captain, vice-captain, and bench data from picks.

        Returns (squad, captain_data, vice_captain_data, bench_points,
        bench_players).
        """
        squad: list[dict[str, Any]] = []
        captain_data: dict[str, Any] = {
            "name": "Unknown",
            "points": 0,
            "element_id": 0,
        }
        vice_captain_data: dict[str, Any] = {
            "name": "Unknown",
            "points": 0,
            "element_id": 0,
        }
        bench_points = 0
        bench_players: list[dict[str, Any]] = []

        for pick in picks:
            element_id = pick["element"]
            multiplier = pick.get("multiplier", 1)
            is_captain = pick.get("is_captain", False)
            is_vice_captain = pick.get("is_vice_captain", False)
            raw_points = live_points.get(element_id, 0)

            squad.append({
                "element_id": element_id,
                "name": registry.get_player_name(element_id),
                "position": pick["position"],
                "points": raw_points,
                "is_captain": is_captain,
                "multiplier": multiplier,
            })

            if is_captain:
                captain_data = {
                    "name": registry.get_player_name(element_id),
                    "points": raw_points * multiplier,
                    "element_id": element_id,
                }

            if is_vice_captain:
                vice_captain_data = {
                    "name": registry.get_player_name(element_id),
                    "points": raw_points,
                    "element_id": element_id,
                }

            # Bench: players with multiplier 0 (didn't contribute to score)
            if multiplier == 0:
                bench_points += raw_points
                bench_players.append({
                    "name": registry.get_player_name(element_id),
                    "points": raw_points,
                    "element_id": element_id,
                })

        return squad, captain_data, vice_captain_data, bench_points, bench_players

    def _build_transfer_list(
        self,
        gw_transfers: list[dict[str, Any]],
        live_points: dict[int, int],
        registry: PlayerRegistry,
    ) -> list[dict[str, Any]]:
        """Build transfer list with player names and point impact."""
        transfer_list: list[dict[str, Any]] = []
        for t in gw_transfers:
            transfer_list.append({
                "player_in": registry.get_player_name(t["element_in"]),
                "player_out": registry.get_player_name(t["element_out"]),
                "player_in_points": live_points.get(t["element_in"], 0),
                "player_out_points": live_points.get(t["element_out"], 0),
            })
        return transfer_list
