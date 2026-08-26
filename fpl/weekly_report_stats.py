"""Weekly report award calculation functions.

Pure functions: participant data dicts in, result dicts out.
No formatting, no side effects.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def get_highest_gameweek_scorer(participants_data: list[dict]) -> dict | None:
    """Find the participant with the highest net gameweek points."""
    if not participants_data:
        return None

    best = max(participants_data, key=lambda p: p.get("net_points", 0))
    return {
        "player_name": best["player_first_name"],
        "points": best["net_points"],
        "team_name": best["team_name"],
    }


def get_lowest_gameweek_scorer(participants_data: list[dict]) -> dict | None:
    """Find the participant with the lowest net gameweek points."""
    if not participants_data:
        return None

    worst = min(participants_data, key=lambda p: p.get("net_points", 0))
    return {
        "player_name": worst["player_first_name"],
        "points": worst["net_points"],
        "team_name": worst["team_name"],
    }


def _rank_change_threshold(event_id: int | None) -> int:
    """Early gameweeks are noisy: everyone's previous rank is fresh, so a
    modest swing means nothing. GW2-5 require a bigger move than usual
    (#35); GW1 has no previous rank at all and is handled by the caller.
    """
    if event_id is not None and 2 <= event_id <= 5:
        return 3
    return 2


def get_biggest_rank_rise(
    participants_data: list[dict], event_id: int | None = None
) -> dict | None:
    """Find the participant who gained the most league positions.

    Returns None outright in gameweek 1 (there is no previous rank to
    rise from) and skips any candidate with no previous rank (0 or
    None) even in later gameweeks (#35). GW2-5 require a change of at
    least 3 positions instead of 2 (early-season damping). Otherwise
    only returns a result if the change is >= 2 positions.
    league_rank_change is positive for rises.
    """
    if not participants_data or event_id == 1:
        return None

    threshold = _rank_change_threshold(event_id)
    best = None
    best_change = 0

    for p in participants_data:
        if not p.get("league_rank_previous"):
            continue
        change = p.get("league_rank_change", 0)
        if change >= threshold and change > best_change:
            best_change = change
            best = p

    if best is None:
        return None

    return {
        "player_name": best["player_first_name"],
        "old_rank": best["league_rank_previous"],
        "new_rank": best["league_rank"],
        "change": best["league_rank_change"],
    }


def get_biggest_rank_fall(
    participants_data: list[dict], event_id: int | None = None
) -> dict | None:
    """Find the participant who lost the most league positions.

    Returns None outright in gameweek 1 (there is no previous rank to
    fall from) and skips any candidate with no previous rank (0 or
    None) even in later gameweeks (#35). GW2-5 require a fall of at
    least 3 positions instead of 2 (early-season damping). Otherwise
    only returns a result if the fall is >= 2 positions.
    league_rank_change is negative for falls.
    """
    if not participants_data or event_id == 1:
        return None

    threshold = _rank_change_threshold(event_id)
    worst = None
    worst_change = 0

    for p in participants_data:
        if not p.get("league_rank_previous"):
            continue
        change = p.get("league_rank_change", 0)
        if change <= -threshold and change < worst_change:
            worst_change = change
            worst = p

    if worst is None:
        return None

    return {
        "player_name": worst["player_first_name"],
        "old_rank": worst["league_rank_previous"],
        "new_rank": worst["league_rank"],
        "change": worst["league_rank_change"],
    }


def get_bench_disasters(
    participants_data: list[dict], threshold: int = 20
) -> list[dict]:
    """Find participants who left significant points on the bench.

    Excludes participants who played the bench_boost chip (those bench
    points actually counted).
    """
    results = []
    for p in participants_data:
        if p.get("chip_played") == "bboost":
            continue
        bench_points = p.get("bench_points", 0)
        if bench_points >= threshold:
            results.append({
                "player_name": p["player_first_name"],
                "bench_points": bench_points,
                "event_total": p.get("event_total", 0),
            })
    return results


def _calculate_transfer_net(participant: dict) -> int | None:
    """Calculate net transfer point impact for a participant.

    Net = sum(player_in_points - player_out_points) - transfer_cost.
    Returns None if no transfers were made.
    """
    transfers = participant.get("transfers", [])
    if not transfers:
        return None

    net = sum(
        t.get("player_in_points", 0) - t.get("player_out_points", 0)
        for t in transfers
    )
    net -= participant.get("transfer_cost", 0)
    return net


def get_transfer_impact(participants_data: list[dict]) -> dict | None:
    """Find the best and worst transfer results across participants.

    Calculates net transfer impact per participant including hit cost.
    Returns dict with 'best' and 'worst' keys, or None if no transfers.
    """
    if not participants_data:
        return None

    scored: list[tuple[dict, int]] = []
    for p in participants_data:
        net = _calculate_transfer_net(p)
        if net is not None:
            scored.append((p, net))

    if not scored:
        return None

    best_p, best_net = max(scored, key=lambda x: x[1])
    worst_p, worst_net = min(scored, key=lambda x: x[1])

    return {
        "best": {
            "player_name": best_p["player_first_name"],
            "net_gain": best_net,
            "transfers": best_p.get("transfers", []),
        },
        "worst": {
            "player_name": worst_p["player_first_name"],
            "net_loss": worst_net,
            "transfers": worst_p.get("transfers", []),
        },
    }


def _captain_effective_points(captain: dict) -> int:
    """Return effective points for a captain pick.

    Uses effective_points (from VC substitution) when present,
    otherwise falls back to the captain's own points.
    """
    if "effective_points" in captain:
        return captain["effective_points"]
    return captain.get("points", 0)


def get_captain_summary(participants_data: list[dict]) -> dict:
    """Summarize captain picks across all participants.

    Returns dict with most_popular, best_pick, worst_pick,
    and vice_captain_substitutions.
    Returns empty dict if no participants.
    """
    if not participants_data:
        return {}

    captain_names: list[str] = []
    for p in participants_data:
        captain = p.get("captain", {})
        captain_names.append(captain.get("name", "Unknown"))

    counter = Counter(captain_names)
    most_common_name, most_common_count = counter.most_common(1)[0]

    best = max(
        participants_data,
        key=lambda p: _captain_effective_points(p.get("captain", {})),
    )
    worst = min(
        participants_data,
        key=lambda p: _captain_effective_points(p.get("captain", {})),
    )

    best_captain = best.get("captain", {})
    worst_captain = worst.get("captain", {})

    # Build list of VC substitutions
    vice_captain_substitutions: list[dict] = []
    for p in participants_data:
        captain = p.get("captain", {})
        if captain.get("did_not_play"):
            vice_captain_substitutions.append({
                "manager": p["player_first_name"],
                "original_captain": captain.get("name", "Unknown"),
                "effective_captain": captain.get("effective_captain", "Unknown"),
                "effective_points": captain.get("effective_points", 0),
            })

    return {
        "most_popular": {
            "player": most_common_name,
            "count": most_common_count,
        },
        "best_pick": {
            "manager": best["player_first_name"],
            "captain": best_captain.get("name", "Unknown"),
            "points": _captain_effective_points(best_captain),
        },
        "worst_pick": {
            "manager": worst["player_first_name"],
            "captain": worst_captain.get("name", "Unknown"),
            "points": _captain_effective_points(worst_captain),
        },
        "vice_captain_substitutions": vice_captain_substitutions,
    }


def get_chip_usage(participants_data: list[dict]) -> list[dict]:
    """Find participants who played a chip this gameweek.

    Only includes entries where chip_played is not None.
    """
    results = []
    for p in participants_data:
        chip = p.get("chip_played")
        if chip is not None:
            results.append({
                "player_name": p["player_first_name"],
                "chip": chip,
                "points": p.get("net_points", 0),
            })
    return results


def get_hit_takers(participants_data: list[dict]) -> list[dict]:
    """Find participants who took point hits for transfers.

    Only includes entries where transfer_cost > 0.
    """
    results = []
    for p in participants_data:
        cost = p.get("transfer_cost", 0)
        if cost > 0:
            results.append({
                "player_name": p["player_first_name"],
                "cost": cost,
                "net_points": p.get("net_points", 0),
            })
    return results


# ---------------------------------------------------------------------------
# New data angles (issue #40 workstream F)
#
# Same pure-function pattern as the awards above: list[dict] in, dict/list
# out, no side effects. `histories` (where used) is dict[entry_id ->
# history.current list] from FPLAPIProtocol.get_team_history().
# ---------------------------------------------------------------------------


def get_chips_remaining(
    bootstrap_chips: list[dict], chips_played: list[dict], event_id: int
) -> list[str]:
    """Chip names still available in the half-season window containing
    event_id.

    bootstrap_chips is bootstrap-static's chips[] (each entry has name,
    start_event, stop_event — two windows per name across a season).
    chips_played is a team's history.chips (each entry has name, event).
    A chip counts as played if it was used within the *same* window.
    Windows that open later in the same half-season still count as
    available (the first-half wildcard opens at GW2, but a manager at
    GW1 has not lost it), so a window matches when it has not yet
    closed and it belongs to the half that contains event_id.
    """
    half_end = 19 if event_id <= 19 else 38
    available = []
    for chip in bootstrap_chips:
        name = chip.get("name")
        start = chip.get("start_event")
        stop = chip.get("stop_event")
        if name is None or start is None or stop is None:
            continue
        if stop < event_id or start > half_end:
            continue
        already_played = any(
            cp.get("name") == name and start <= cp.get("event", -1) <= stop
            for cp in chips_played
        )
        if not already_played:
            available.append(name)
    return available


def get_chips_played_to_date(
    chips_played: list[dict], event_id: int
) -> list[dict]:
    """Chips played this season up to and including event_id."""
    return [
        {"name": c.get("name"), "event": c.get("event")}
        for c in chips_played
        if c.get("event") is not None and c["event"] <= event_id
    ]


def get_head_to_head(
    participants_data: list[dict],
    histories: dict[int, list[dict]] | None = None,
) -> list[dict]:
    """Per-manager head-to-head record: this GW plus the season so far.

    This GW: how many others each manager outscored (beat) and lost to,
    by event_total. Season record (wins/losses) is derived from
    `histories` — every prior gameweek all managers share data for.
    """
    results = []
    for p in participants_data:
        score = p.get("event_total", 0)
        beat = sum(
            1
            for other in participants_data
            if other is not p and other.get("event_total", 0) < score
        )
        lost_to = sum(
            1
            for other in participants_data
            if other is not p and other.get("event_total", 0) > score
        )
        results.append({
            "player_name": p["player_first_name"],
            "beat": beat,
            "lost_to": lost_to,
            "season_record": {"wins": 0, "losses": 0},
        })

    if not histories:
        return results

    entry_to_index = {p["entry_id"]: i for i, p in enumerate(participants_data)}

    # event -> {entry_id: points}
    scores_by_event: dict[int, dict[int, int]] = {}
    for entry_id, hist in histories.items():
        for h in hist:
            event = h.get("event")
            points = h.get("points")
            if event is None or points is None:
                continue
            scores_by_event.setdefault(event, {})[entry_id] = points

    wins: Counter = Counter()
    losses: Counter = Counter()
    for scores in scores_by_event.values():
        for entry_a, points_a in scores.items():
            for entry_b, points_b in scores.items():
                if entry_a == entry_b:
                    continue
                if points_a > points_b:
                    wins[entry_a] += 1
                elif points_a < points_b:
                    losses[entry_a] += 1

    for entry_id, idx in entry_to_index.items():
        results[idx]["season_record"] = {
            "wins": wins.get(entry_id, 0),
            "losses": losses.get(entry_id, 0),
        }

    return results


def get_differentials(participants_data: list[dict]) -> dict:
    """Players owned by exactly one manager across all 15 picks.

    Returns {"top": [...5], "bottom": [...3]} sorted by points, each
    entry {player_name, owner, points}.
    """
    ownership: dict[int, list[tuple[str, str, int]]] = {}
    for p in participants_data:
        owner = p["player_first_name"]
        for sq in p.get("squad", []):
            ownership.setdefault(sq["element_id"], []).append(
                (owner, sq["name"], sq.get("points", 0))
            )

    diffs: list[dict[str, Any]] = [
        {"player_name": owners[0][1], "owner": owners[0][0], "points": owners[0][2]}
        for owners in ownership.values()
        if len(owners) == 1
    ]
    diffs.sort(key=lambda d: d["points"], reverse=True)

    return {"top": diffs[:5], "bottom": diffs[-3:] if diffs else []}


def get_captain_that_would_have_won(participants_data: list[dict]) -> dict | None:
    """The highest-scoring player in any league squad this GW, and how
    many managers actually captained him."""
    best_player = None
    best_points = -1
    for p in participants_data:
        for sq in p.get("squad", []):
            if sq.get("points", 0) > best_points:
                best_points = sq["points"]
                best_player = sq

    if best_player is None:
        return None

    captained_by = sum(
        1
        for p in participants_data
        if p.get("captain", {}).get("element_id") == best_player["element_id"]
    )

    return {
        "player_name": best_player["name"],
        "points": best_points,
        "captained_by": captained_by,
    }


def get_streaks(
    participants_data: list[dict], histories: dict[int, list[dict]]
) -> list[dict]:
    """Per-manager longest *active* streaks (ending at the latest shared
    gameweek): GWs above the league average, consecutive round wins,
    consecutive green arrows (overall_rank improving). Only streaks
    >= 3 are reported.
    """
    if not histories:
        return []

    entry_to_name = {p["entry_id"]: p["player_first_name"] for p in participants_data}

    events_by_entry: dict[int, dict[int, dict]] = {
        entry_id: {h["event"]: h for h in hist if h.get("event") is not None}
        for entry_id, hist in histories.items()
    }

    all_events = sorted({
        event for events in events_by_entry.values() for event in events
    })

    avg_by_event: dict[int, float] = {}
    for event in all_events:
        event_points = [
            events[event]["points"]
            for events in events_by_entry.values()
            if event in events and events[event].get("points") is not None
        ]
        if event_points:
            avg_by_event[event] = sum(event_points) / len(event_points)

    results = []
    for entry_id, name in entry_to_name.items():
        events = events_by_entry.get(entry_id, {})
        entry_events = sorted(events)
        if not entry_events:
            continue

        streak = 0
        for event in reversed(entry_events):
            avg = avg_by_event.get(event)
            points = events[event].get("points")
            if avg is None or points is None or points <= avg:
                break
            streak += 1
        if streak >= 3:
            results.append({
                "player_name": name, "kind": "above_average", "length": streak
            })

        streak = 0
        for event in reversed(entry_events):
            points = events[event].get("points")
            if points is None:
                break
            max_points = max(
                other_events[event]["points"]
                for other_events in events_by_entry.values()
                if event in other_events
                and other_events[event].get("points") is not None
            )
            if points != max_points:
                break
            streak += 1
        if streak >= 3:
            results.append({
                "player_name": name, "kind": "round_wins", "length": streak
            })

        streak = 0
        for i in range(len(entry_events) - 1, 0, -1):
            cur_rank = events[entry_events[i]].get("overall_rank")
            prev_rank = events[entry_events[i - 1]].get("overall_rank")
            if cur_rank is None or prev_rank is None or cur_rank >= prev_rank:
                break
            streak += 1
        if streak >= 3:
            results.append({
                "player_name": name, "kind": "green_arrows", "length": streak
            })

    return results


def get_records(
    participants_data: list[dict], histories: dict[int, list[dict]]
) -> dict:
    """Season best/worst GW score so far, across the whole league's
    shared history."""
    entry_to_name = {p["entry_id"]: p["player_first_name"] for p in participants_data}

    best: tuple[int, str, int] | None = None
    worst: tuple[int, str, int] | None = None
    for entry_id, hist in (histories or {}).items():
        name = entry_to_name.get(entry_id)
        if name is None:
            continue
        for h in hist:
            points = h.get("points")
            event = h.get("event")
            if points is None or event is None:
                continue
            if best is None or points > best[0]:
                best = (points, name, event)
            if worst is None or points < worst[0]:
                worst = (points, name, event)

    return {
        "best": (
            {"player_name": best[1], "event_id": best[2], "points": best[0]}
            if best
            else None
        ),
        "worst": (
            {"player_name": worst[1], "event_id": worst[2], "points": worst[0]}
            if worst
            else None
        ),
    }


def get_chip_tracker(participants_data: list[dict]) -> list[dict]:
    """Per-manager chips remaining and chips played this season.

    Reads `chips_remaining` and `chips_played_season`, which
    WeeklyReport attaches to each participant when it assembles the
    report — this is the GGW/chip fact-box data.
    """
    return [
        {
            "player_name": p["player_first_name"],
            "chips_remaining": p.get("chips_remaining", []),
            "chips_played": p.get("chips_played_season", []),
        }
        for p in participants_data
    ]


def _storyline(
    kind: str, score: int, managers: list[str], facts: dict, summary: str
) -> dict:
    return {
        "kind": kind,
        "score": score,
        "managers": managers,
        "facts": facts,
        "summary": summary,
    }


_SCORE_FAMILY_KINDS = frozenset({
    "gw_rank_extreme",
    "gw_rank_notable",
    "overall_top_tier",
    "score_far_above_average",
    "score_far_below_average",
})


def rank_storylines(report: dict) -> list[dict]:
    """Rank notability hooks from an assembled (or report-like) dict —
    same shape as WeeklyReport.build() produces (meta, standings,
    global, awards, angles). Returns at most 6, sorted by score
    descending, so the narrative prompt sees the strongest few hooks
    rather than a fixed table of awards.
    """
    meta = report.get("meta", {}) or {}
    event_id = meta.get("event_id")
    is_golden = meta.get("is_golden", False)

    global_block = report.get("global", {}) or {}
    avg = global_block.get("average_score")

    standings = report.get("standings", []) or []
    awards = report.get("awards", {}) or {}
    angles = report.get("angles", {}) or {}
    records = angles.get("records", {}) or {}

    storylines: list[dict] = []

    for p in standings:
        name = p.get("player_first_name", "Unknown")
        event_total = p.get("event_total", 0)
        event_pct = p.get("event_percentile")
        overall_pct = p.get("overall_percentile")
        pps = p.get("points_per_starter")
        chip = p.get("chip_played")

        if event_pct is not None:
            if event_pct <= 1 or event_pct >= 99:
                storylines.append(_storyline(
                    "gw_rank_extreme", 95, [name],
                    {"event_total": event_total, "event_percentile": event_pct},
                    f"{name} {event_total} pts, GW rank in the "
                    f"{'top' if event_pct <= 1 else 'bottom'} 1% of the field.",
                ))
            elif event_pct <= 5 or event_pct >= 95:
                storylines.append(_storyline(
                    "gw_rank_notable", 70, [name],
                    {"event_total": event_total, "event_percentile": event_pct},
                    f"{name} {event_total} pts, GW rank in the "
                    f"{'top' if event_pct <= 5 else 'bottom'} 5% of the field.",
                ))

        if overall_pct is not None and overall_pct <= 0.5:
            storylines.append(_storyline(
                "overall_top_tier", 85, [name],
                {"overall_percentile": overall_pct},
                f"{name} sits in the top 0.5% of all managers overall "
                f"({overall_pct}%).",
            ))

        if avg is not None:
            if event_total < avg / 2:
                pps_txt = f", {pps} per starter" if pps is not None else ""
                storylines.append(_storyline(
                    "score_far_below_average", 90, [name],
                    {"event_total": event_total, "global_average": avg},
                    f"{name} {event_total} pts{pps_txt}, less than half the "
                    f"global average of {avg}.",
                ))
            elif event_total >= avg * 1.5:
                storylines.append(_storyline(
                    "score_far_above_average", 80, [name],
                    {"event_total": event_total, "global_average": avg},
                    f"{name} {event_total} pts, at least 1.5x the global "
                    f"average of {avg}.",
                ))

        after_gw3 = event_id is not None and event_id > 3
        record_score = 60 if after_gw3 else 20
        best = records.get("best")
        worst = records.get("worst")
        if best and best.get("player_name") == name and best.get("event_id") == event_id:
            storylines.append(_storyline(
                "season_record_best", record_score, [name],
                {"points": best.get("points")},
                f"{name} set the season-best GW score so far: {best.get('points')} pts.",
            ))
        if worst and worst.get("player_name") == name and worst.get("event_id") == event_id:
            storylines.append(_storyline(
                "season_record_worst", record_score, [name],
                {"points": worst.get("points")},
                f"{name} set the season-worst GW score so far: {worst.get('points')} pts.",
            ))

        if chip:
            chip_score = 50
            top_scorer = awards.get("highest_scorer") or {}
            low_scorer = awards.get("lowest_scorer") or {}
            was_extreme = (
                top_scorer.get("player_name") == name
                or low_scorer.get("player_name") == name
            )
            if was_extreme:
                chip_score += 20
            storylines.append(_storyline(
                "chip_played", chip_score, [name],
                {"chip": chip, "event_total": event_total},
                f"{name} played {chip} for {event_total} pts"
                + (" — the round's extreme score." if was_extreme else "."),
            ))
            if chip in ("3xc", "bboost") and avg is not None and event_total < avg:
                storylines.append(_storyline(
                    "chip_underperformed", 65, [name],
                    {"chip": chip, "event_total": event_total, "global_average": avg},
                    f"{name}'s {chip} returned {event_total} pts, below the "
                    f"global average of {avg}.",
                ))

        if p.get("captain", {}).get("did_not_play"):
            captain = p["captain"]
            storylines.append(_storyline(
                "captain_benched", 55, [name],
                {
                    "original_captain": captain.get("name"),
                    "effective_captain": captain.get("effective_captain"),
                },
                f"{name}'s captain ({captain.get('name')}) didn't play — "
                f"the armband passed to {captain.get('effective_captain')}.",
            ))

        bench_points = p.get("bench_points", 0)
        if bench_points >= 20:
            storylines.append(_storyline(
                "bench_points_high", 40, [name], {"bench_points": bench_points},
                f"{name} left {bench_points} points on the bench.",
            ))

        hit_cost = p.get("transfer_cost", 0)
        if hit_cost >= 8:
            storylines.append(_storyline(
                "hit_cost_high", 45, [name], {"hit_cost": hit_cost},
                f"{name} took a {hit_cost}-point hit.",
            ))

    for s in angles.get("streaks", []):
        storylines.append(_storyline(
            "streak", 50, [s["player_name"]], s,
            f"{s['player_name']}: {s['length']} straight "
            f"{s['kind'].replace('_', ' ')}.",
        ))

    if standings:
        winner = max(standings, key=lambda p: p.get("event_total", 0))
        winner_name = winner.get("player_first_name", "Unknown")
        storylines.append(_storyline(
            "round_win", 30, [winner_name],
            {"event_total": winner.get("event_total", 0)},
            f"{winner_name} won the round with {winner.get('event_total', 0)} pts.",
        ))
        if is_golden:
            storylines.append(_storyline(
                "golden_winner", 75, [winner_name],
                {"event_total": winner.get("event_total", 0)},
                f"{winner_name} won this golden gameweek's cash prize with "
                f"{winner.get('event_total', 0)} pts.",
            ))

    for award_key, kind in (("biggest_rise", "biggest_rise"), ("biggest_fall", "biggest_fall")):
        award = awards.get(award_key)
        if award:
            storylines.append(_storyline(
                kind, 25, [award["player_name"]], award,
                f"{award['player_name']} moved from rank {award['old_rank']} "
                f"to {award['new_rank']} ({award['change']:+d}).",
            ))

    storylines.sort(key=lambda s: s["score"], reverse=True)
    # The score-family kinds are different views of the same round, so a
    # manager gets at most two of them; distinct facts (chip, golden win,
    # bench, streak) are always kept. Stops one big round crowding
    # everyone else out of the six slots the prompt sees.
    per_manager: Counter[str] = Counter()
    kept: list[dict] = []
    for story in storylines:
        names = story.get("managers") or []
        if story["kind"] in _SCORE_FAMILY_KINDS:
            if any(per_manager[n] >= 2 for n in names):
                continue
            for n in names:
                per_manager[n] += 1
        kept.append(story)
    return kept[:6]
