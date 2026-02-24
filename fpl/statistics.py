"""Statistics calculation module for FPL league data."""

from typing import Any

from .participant import Participant


def get_highest_team_value(participants: list[Participant]) -> dict[str, Any] | None:
    """Calculate the highest team value among participants.

    Args:
        participants: List of Participant objects or dicts with 'team_name', 'player_first_name',
                     and 'history' containing 'bank' and 'value' fields.

    Returns:
        Dictionary with 'team_name', 'player_name', and 'value' (in millions),
        or None if no valid data is available.
    """
    if not participants:
        return None

    highest = None
    highest_value = 0

    for participant in participants:
        history = participant.history
        if not history:
            continue

        # Get latest event data (last item in history)
        latest_event = history[-1]
        value = latest_event.get('value', 0)

        # Calculate team value: value / 10
        team_value = value / 10

        if team_value > highest_value:
            highest_value = team_value
            highest = {
                'team_name': participant.team_name,
                'player_name': participant.player_first_name,
                'value': team_value
            }

    return highest


def get_in_form_players(participants: list[Participant]) -> dict[str, Any] | None:
    """Calculate players with most consecutive overall_rank improvements (green arrows).

    A green arrow means the overall_rank decreased (improved) from the previous event.

    Args:
        participants: List of Participant objects with 'player_first_name'
                     and 'history' containing 'event' and 'overall_rank' fields.

    Returns:
        Dictionary with 'count' (int) and 'players' (list of first names),
        or None if no players have green arrows.
    """
    if not participants:
        return None

    max_consecutive = 0
    players_with_max = []

    for participant in participants:
        history = participant.history
        if len(history) < 2:
            continue

        # Calculate consecutive green arrows ending at the latest event
        current_consecutive = 0
        for i in range(len(history) - 1, 0, -1):
            current_rank = history[i].get('overall_rank')
            previous_rank = history[i - 1].get('overall_rank')

            if current_rank is None or previous_rank is None:
                break

            # Green arrow = rank decreased (improved)
            if current_rank < previous_rank:
                current_consecutive += 1
            else:
                break

        if current_consecutive > 0:
            player_name = participant.player_first_name
            if current_consecutive > max_consecutive:
                max_consecutive = current_consecutive
                players_with_max = [player_name]
            elif current_consecutive == max_consecutive:
                players_with_max.append(player_name)

    if max_consecutive == 0:
        return None

    return {
        'count': max_consecutive,
        'players': players_with_max
    }


def should_show_in_form_stat(current_event: int) -> bool:
    """Determine if the in-form statistic should be displayed.

    Args:
        current_event: The current gameweek number.

    Returns:
        True if current_event >= 3, False otherwise.
    """
    return current_event >= 3


def get_player_with_highest_rank_loss(
    participants: list[Participant],
    current_event: int
) -> dict[str, Any] | None:
    """Calculate which player has lost the most % of ranking in the past 5 weeks.

    Args:
        participants: List of Participant objects with 'player_first_name'
                     and 'history' containing 'event' and 'overall_rank' fields.
        current_event: The current gameweek number.

    Returns:
        Dictionary with 'player_name', 'rank_loss_percent', 'num_rounds', 'old_rank', 'new_rank',
        or None if no player has rank loss or current_event <= 1.
    """
    # Don't calculate for event 1 (no comparison possible)
    if current_event <= 1:
        return None

    if not participants:
        return None

    # Determine comparison event: max(1, current_event - 5)
    comparison_event = max(1, current_event - 5)
    num_rounds = current_event - comparison_event

    highest_loss = None
    highest_loss_percent = 0

    for participant in participants:
        history = participant.history

        if len(history) < 2:
            continue

        # Find the ranks at comparison_event and current_event
        old_rank = None
        new_rank = None

        for event_data in history:
            event = event_data.get('event')
            rank = event_data.get('overall_rank')

            if event == comparison_event:
                old_rank = rank
            if event == current_event:
                new_rank = rank

        # Skip if we don't have both ranks
        if old_rank is None or new_rank is None:
            continue

        # Calculate rank loss (only if new_rank > old_rank, meaning worsened)
        if new_rank > old_rank:
            rank_loss_percent = ((new_rank - old_rank) / old_rank) * 100

            if rank_loss_percent > highest_loss_percent:
                highest_loss_percent = rank_loss_percent
                highest_loss = {
                    'player_name': participant.player_first_name,
                    'rank_loss_percent': rank_loss_percent,
                    'num_rounds': num_rounds,
                    'old_rank': old_rank,
                    'new_rank': new_rank
                }

    return highest_loss


def get_closest_overall_rank_gap(participants: list[Participant]) -> dict[str, Any] | None:
    """Find the two players with the smallest overall points difference.

    This function identifies players who are closest in the overall standings by
    comparing their total points accumulated across all gameweeks.

    Args:
        participants: List of Participant objects with 'player_first_name'
                     and 'history' containing 'total_points' field.

    Returns:
        Dictionary with 'leader_name', 'chaser_name', and 'points_gap',
        or None if not enough participants or no valid data.
    """
    if len(participants) < 2:
        return None

    # Get latest total points for each participant
    participants_with_points = []
    for participant in participants:
        history = participant.history
        if not history:
            continue

        # Get latest event data (last item in history)
        latest_event = history[-1]
        total_points = latest_event.get('total_points')

        if total_points is not None:
            participants_with_points.append({
                'name': participant.player_first_name,
                'points': total_points
            })

    # Need at least 2 participants with valid points
    if len(participants_with_points) < 2:
        return None

    # Sort by points descending (highest first)
    participants_with_points.sort(key=lambda x: x['points'], reverse=True)

    # Find the smallest gap between consecutive participants
    smallest_gap = None
    smallest_gap_pair = None

    for i in range(len(participants_with_points) - 1):
        leader = participants_with_points[i]
        chaser = participants_with_points[i + 1]
        gap = leader['points'] - chaser['points']

        # Skip zero or negative gaps:
        # - Zero gap means players are tied, so "Haien kommer" doesn't apply
        # - Negative gap should never occur with proper sorting (highest points first)
        if gap <= 0:
            continue

        if smallest_gap is None or gap < smallest_gap:
            smallest_gap = gap
            smallest_gap_pair = (leader, chaser)

    if smallest_gap_pair is None:
        return None

    leader, chaser = smallest_gap_pair
    return {
        'leader_name': leader['name'],
        'chaser_name': chaser['name'],
        'points_gap': smallest_gap
    }


def get_best_gameweek_score(participants: list[Participant]) -> dict[str, Any] | None:
    """Find the highest single-gameweek points score among all participants.

    Handles ties — multiple players can share the record if they scored the
    same max points (possibly in different gameweeks).

    Returns:
        Dictionary with 'points' and 'players' list of {'name', 'event'},
        or None if no valid data.
    """
    if not participants:
        return None

    max_points = -1
    best_players: list[dict[str, Any]] = []

    for participant in participants:
        for event_data in participant.history:
            points = event_data.get('points')
            if points is None:
                continue
            if points > max_points:
                max_points = points
                best_players = [{'name': participant.player_first_name, 'event': event_data['event']}]
            elif points == max_points:
                best_players.append({'name': participant.player_first_name, 'event': event_data['event']})

    if max_points < 0:
        return None

    return {'points': max_points, 'players': best_players}


def get_best_gameweek_rank(
    participants: list[Participant], total_players: int
) -> dict[str, Any] | None:
    """Find the best (lowest) global gameweek rank among all participants.

    Handles ties — multiple players can share the record if they achieved the
    same best rank (possibly in different gameweeks).

    Returns:
        Dictionary with 'rank', 'percentile', and 'players' list of {'name', 'event'},
        or None if no valid data.
    """
    if not participants:
        return None

    best_rank = float('inf')
    best_players: list[dict[str, Any]] = []

    for participant in participants:
        for event_data in participant.history:
            rank = event_data.get('rank')
            if rank is None:
                continue
            if rank < best_rank:
                best_rank = rank
                best_players = [{'name': participant.player_first_name, 'event': event_data['event']}]
            elif rank == best_rank:
                best_players.append({'name': participant.player_first_name, 'event': event_data['event']})

    if best_rank == float('inf'):
        return None

    percentile = (best_rank / total_players) * 100

    return {'rank': best_rank, 'percentile': percentile, 'players': best_players}


def get_worst_gameweek_score(participants: list[Participant]) -> dict[str, Any] | None:
    """Find the lowest single-gameweek points score among all participants.

    Handles ties — multiple players can share the record if they scored the
    same min points (possibly in different gameweeks).

    Returns:
        Dictionary with 'points' and 'players' list of {'name', 'event'},
        or None if no valid data.
    """
    if not participants:
        return None

    min_points = float('inf')
    worst_players: list[dict[str, Any]] = []

    for participant in participants:
        for event_data in participant.history:
            points = event_data.get('points')
            if points is None:
                continue
            if points < min_points:
                min_points = points
                worst_players = [{'name': participant.player_first_name, 'event': event_data['event']}]
            elif points == min_points:
                worst_players.append({'name': participant.player_first_name, 'event': event_data['event']})

    if min_points == float('inf'):
        return None

    return {'points': int(min_points), 'players': worst_players}


def get_worst_gameweek_rank(
    participants: list[Participant], total_players: int
) -> dict[str, Any] | None:
    """Find the worst (highest) global gameweek rank among all participants.

    Handles ties — multiple players can share the record if they achieved the
    same worst rank (possibly in different gameweeks).

    Returns:
        Dictionary with 'rank', 'percentile', and 'players' list of {'name', 'event'},
        or None if no valid data.
    """
    if not participants:
        return None

    worst_rank = -1
    worst_players: list[dict[str, Any]] = []

    for participant in participants:
        for event_data in participant.history:
            rank = event_data.get('rank')
            if rank is None:
                continue
            if rank > worst_rank:
                worst_rank = rank
                worst_players = [{'name': participant.player_first_name, 'event': event_data['event']}]
            elif rank == worst_rank:
                worst_players.append({'name': participant.player_first_name, 'event': event_data['event']})

    if worst_rank == -1:
        return None

    percentile = ((total_players - worst_rank) / total_players) * 100

    return {'rank': worst_rank, 'percentile': percentile, 'players': worst_players}
