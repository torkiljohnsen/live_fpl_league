"""Weekly report data collection and participant building.

Orchestrates data collection from the FPL API and builds
GameweekParticipantData dicts for each league participant.
"""

from __future__ import annotations

from typing import Any

from .fpl_api_protocol import FPLAPIProtocol
from .player_registry import PlayerRegistry


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

    def build(self) -> dict[str, Any]:
        """Fetch all data and build participant data dicts.

        Fetches bootstrap, league standings, event live data, and
        per-participant picks and transfers. Builds a
        GameweekParticipantData dict for each participant.

        Returns a dict with standings (list of participant data dicts).
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

        return {"standings": self._participants_data}

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
