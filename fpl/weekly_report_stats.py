"""Weekly report award calculation functions.

Pure functions: participant data dicts in, result dicts out.
No formatting, no side effects.
"""

from __future__ import annotations

from collections import Counter


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


def get_biggest_rank_rise(participants_data: list[dict]) -> dict | None:
    """Find the participant who gained the most league positions.

    Only returns a result if the change is >= 2 positions.
    league_rank_change is positive for rises.
    """
    if not participants_data:
        return None

    best = None
    best_change = 0

    for p in participants_data:
        change = p.get("league_rank_change", 0)
        if change >= 2 and change > best_change:
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


def get_biggest_rank_fall(participants_data: list[dict]) -> dict | None:
    """Find the participant who lost the most league positions.

    Only returns a result if the fall is >= 2 positions.
    league_rank_change is negative for falls.
    """
    if not participants_data:
        return None

    worst = None
    worst_change = 0

    for p in participants_data:
        change = p.get("league_rank_change", 0)
        if change <= -2 and change < worst_change:
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
