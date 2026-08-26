"""Weekly report data collection, assembly, and JSON output.

Orchestrates data collection from the FPL API, builds
GameweekParticipantData dicts for each league participant,
calculates awards, and assembles the final report dict.
"""

from __future__ import annotations

import json
import sys
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


def _is_golden(event_id: int) -> bool:
    """Golden gameweeks carry a cash prize and fall every 4th GW."""
    return event_id % 4 == 0


def detect_current_gameweek(api: FPLAPIProtocol) -> int:
    """Find the latest locked gameweek from bootstrap-static data.

    Scans events in reverse for the most recent one that is both
    finished and data_checked. FPL locks gameweek points at 09:00 UK on
    the day after the gameweek's final match, and data_checked is what
    marks that lock — before it, BPS and Defensive Contribution points
    can still be amended by Opta's post-match review.

    Raises SystemExit if no locked gameweek is found.
    """
    bootstrap = api.get_bootstrap_static()
    events = bootstrap.get("events", [])

    for event in reversed(events):
        if event.get("finished", False) and event.get("data_checked", False):
            return int(event["id"])

    print("Error: No locked gameweek found.", file=sys.stderr)
    sys.exit(1)


def get_report_path(
    output_dir: str, league_id: str, season: str, event_id: int
) -> Path:
    """Return the canonical path for a gameweek report JSON."""
    return (
        Path(output_dir)
        / "weekly_report"
        / "reports"
        / league_id
        / season
        / f"gw{event_id}.json"
    )


def get_narrative_path(
    output_dir: str, league_id: str, season: str, event_id: int
) -> Path:
    """Return the canonical path for a gameweek narrative markdown."""
    return (
        Path(output_dir)
        / "docs"
        / "narratives"
        / season
        / league_id
        / f"gw{event_id}.md"
    )


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
        self._histories: dict[int, list[dict[str, Any]]] = {}
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
        self._histories = {}
        bootstrap_chips = self._bootstrap.get("chips", [])
        global_block = self._build_global()

        for team in teams:
            entry_id = team["entry"]
            picks_data = self._api.get_team_picks(
                str(entry_id), str(self._event_id)
            )
            all_transfers = self._api.get_transfers(str(entry_id))
            gw_transfers = [
                t for t in all_transfers if t.get("event") == self._event_id
            ]
            team_history = self._api.get_team_history(str(entry_id))
            history_current = team_history.get("current", [])
            history_chips = team_history.get("chips", [])
            self._histories[entry_id] = history_current

            participant = self._build_participant_data(
                team,
                picks_data,
                gw_transfers,
                live_points,
                registry,
                history_current,
                history_chips,
                bootstrap_chips,
                global_block,
            )
            self._participants_data.append(participant)

        # Sort standings by league rank
        self._participants_data.sort(key=lambda p: p.get("league_rank", 0))

        # league_vs_world needs the fully built participant list, which
        # didn't exist yet when global_block was first assembled above.
        global_block["league_vs_world"] = self._compute_league_vs_world(
            global_block.get("average_score")
        )

        # Assemble the full report
        self._report = {
            "meta": self._build_meta(),
            "standings": self._participants_data,
            "awards": self._build_awards(),
            "league_summary": self._build_league_summary(global_block),
            "global": global_block,
            "angles": self._build_angles(),
        }
        self._report["storylines"] = stats.rank_storylines(self._report)

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

        events = self._bootstrap.get("events", [])
        next_event = None
        for event in events:
            if event.get("id") == self._event_id + 1:
                next_event = {
                    "id": event["id"],
                    "deadline_time": event.get("deadline_time"),
                    "is_golden": _is_golden(event["id"]),
                }
                break

        return {
            "league_id": self._league_id,
            "league_name": self._league_name,
            "season": season,
            "event_id": self._event_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "previous_report": previous_report,
            "previous_narrative": previous_narrative,
            "next_event": next_event,
            "is_golden": _is_golden(self._event_id),
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
            "biggest_rise": stats.get_biggest_rank_rise(p, event_id=self._event_id),
            "biggest_fall": stats.get_biggest_rank_fall(p, event_id=self._event_id),
            "bench_disasters": stats.get_bench_disasters(p),
            "best_transfer": best_transfer,
            "worst_transfer": worst_transfer,
            "captain_summary": stats.get_captain_summary(p),
            "chip_usage": stats.get_chip_usage(p),
            "hit_takers": stats.get_hit_takers(p),
        }

    def _build_global(self) -> dict[str, Any]:
        """Build the global (world-context) section.

        Pulls this gameweek's average/highest score and the total
        player count from bootstrap-static, per issue #40 workstream K.
        `league_vs_world` is filled in later, once participants exist —
        see `_compute_league_vs_world()`.
        """
        events = self._bootstrap.get("events", [])
        event: dict[str, Any] = next(
            (e for e in events if e.get("id") == self._event_id), {}
        )
        return {
            "average_score": event.get("average_entry_score"),
            "highest_score": event.get("highest_score"),
            "total_players": self._bootstrap.get("total_players"),
            "league_vs_world": None,
        }

    def _compute_league_vs_world(self, average_score: float | None) -> float | None:
        """League's average net score minus the global average score."""
        net_scores = [p.get("net_points", 0) for p in self._participants_data]
        if average_score is None or not net_scores:
            return None
        league_avg = sum(net_scores) / len(net_scores)
        return round(league_avg - average_score, 1)

    def _build_angles(self) -> dict[str, Any]:
        """Build the new data-angle hooks (issue #40 workstream F)."""
        p = self._participants_data
        return {
            "head_to_head": stats.get_head_to_head(p, self._histories),
            "differentials": stats.get_differentials(p),
            "captain_that_would_have_won": stats.get_captain_that_would_have_won(p),
            "streaks": stats.get_streaks(p, self._histories),
            "records": stats.get_records(p, self._histories),
            "chip_tracker": stats.get_chip_tracker(p),
        }

    def _build_league_summary(self, global_block: dict[str, Any]) -> dict[str, Any]:
        """Build the league summary section."""
        total = len(self._participants_data)
        global_average = global_block.get("average_score")
        if total == 0:
            return {
                "average_score": 0,
                "leader": None,
                "total_participants": 0,
                "global_average": global_average,
                "managers_above_global_average": 0,
            }

        net_scores = [p.get("net_points", 0) for p in self._participants_data]
        avg = sum(net_scores) / total

        leader = self._participants_data[0]

        managers_above_global_average = sum(
            1
            for p in self._participants_data
            if global_average is not None and p.get("event_total", 0) > global_average
        )

        return {
            "average_score": round(avg, 1),
            "leader": {
                "player_name": leader["player_first_name"],
                "total_points": leader["total_points"],
            },
            "total_participants": total,
            "global_average": global_average,
            "managers_above_global_average": managers_above_global_average,
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
        history_current: list[dict[str, Any]],
        history_chips: list[dict[str, Any]],
        bootstrap_chips: list[dict[str, Any]],
        global_block: dict[str, Any],
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

        overall_rank = entry_history.get("overall_rank", 0)
        total_players = global_block.get("total_players")

        event_rank = entry_history.get("rank")
        event_percentile = (
            round(event_rank / total_players * 100, 1)
            if event_rank and total_players
            else None
        )
        overall_percentile = (
            round(overall_rank / total_players * 100, 1)
            if overall_rank and total_players
            else None
        )

        starters = sum(1 for p in squad if p.get("multiplier", 0) > 0)
        points_per_starter = (
            round(event_total / starters, 1) if starters else None
        )

        global_average = global_block.get("average_score")
        vs_global_average = (
            round(event_total - global_average)
            if global_average is not None
            else None
        )

        form_last_5 = None
        if self._event_id > 1:
            past_points = [
                h["points"]
                for h in history_current
                if h.get("event", 0) <= self._event_id and h.get("points") is not None
            ]
            recent = past_points[-5:]
            if recent:
                form_last_5 = round(sum(recent) / len(recent), 1)

        bench_points_season = sum(
            h.get("points_on_bench", 0) or 0
            for h in history_current
            if h.get("event", 0) <= self._event_id
        )
        hit_cost_season = sum(
            h.get("event_transfers_cost", 0) or 0
            for h in history_current
            if h.get("event", 0) <= self._event_id
        )

        chips_remaining = stats.get_chips_remaining(
            bootstrap_chips, history_chips, self._event_id
        )
        chips_played_season = stats.get_chips_played_to_date(
            history_chips, self._event_id
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
            "overall_rank": overall_rank,
            # Global context (issue #40 workstream K)
            "event_rank": event_rank,
            "event_percentile": event_percentile,
            "overall_percentile": overall_percentile,
            "points_per_starter": points_per_starter,
            "vs_global_average": vs_global_average,
            "form_last_5": form_last_5,
            "bench_points_season": bench_points_season,
            "hit_cost_season": hit_cost_season,
            "chips_remaining": chips_remaining,
            "chips_played_season": chips_played_season,
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

            player_info = registry.get_player_info(element_id)
            squad.append({
                "element_id": element_id,
                "name": player_info["name"],
                "club": player_info["team"],
                "position": pick["position"],
                "points": raw_points,
                "is_captain": is_captain,
                "multiplier": multiplier,
            })

            if is_captain:
                captain_data = {
                    "name": player_info["name"],
                    "club": player_info["team"],
                    "points": raw_points * multiplier,
                    "element_id": element_id,
                }

            if is_vice_captain:
                vice_captain_data = {
                    "name": player_info["name"],
                    "club": player_info["team"],
                    "points": raw_points,
                    "element_id": element_id,
                }

            # Bench: players with multiplier 0 (didn't contribute to score)
            if multiplier == 0:
                bench_points += raw_points
                bench_players.append({
                    "name": player_info["name"],
                    "club": player_info["team"],
                    "points": raw_points,
                    "element_id": element_id,
                })

        # Detect captain substitution: captain didn't play (multiplier 0)
        # and vice-captain received the armband (multiplier > 1)
        captain_multiplier = 0
        vc_multiplier = 0
        for p in squad:
            if p["is_captain"]:
                captain_multiplier = p["multiplier"]
            if p["element_id"] == vice_captain_data["element_id"]:
                vc_multiplier = p["multiplier"]

        if captain_multiplier == 0 and vc_multiplier > 1:
            captain_data["did_not_play"] = True
            vice_captain_data["substituted_in"] = True
            captain_data["effective_captain"] = vice_captain_data["name"]
            captain_data["effective_points"] = (
                vice_captain_data["points"] * vc_multiplier
            )
        else:
            captain_data["did_not_play"] = False

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
            in_info = registry.get_player_info(t["element_in"])
            out_info = registry.get_player_info(t["element_out"])
            transfer_list.append({
                "player_in": in_info["name"],
                "player_in_club": in_info["team"],
                "player_out": out_info["name"],
                "player_out_club": out_info["team"],
                "player_in_points": live_points.get(t["element_in"], 0),
                "player_out_points": live_points.get(t["element_out"], 0),
            })
        return transfer_list
