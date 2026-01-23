"""Statistics calculation module for FPL league data."""


def get_highest_team_value(participants):
    """Calculate the highest team value among participants.

    Args:
        participants: List of participant dictionaries with 'team_name', 'player_first_name',
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
        history = participant.get('history', [])
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
                'team_name': participant.get('team_name', ''),
                'player_name': participant.get('player_first_name', ''),
                'value': team_value
            }

    return highest


def get_in_form_players(participants):
    """Calculate players with most consecutive overall_rank improvements (green arrows).

    A green arrow means the overall_rank decreased (improved) from the previous event.

    Args:
        participants: List of participant dictionaries with 'player_first_name'
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
        history = participant.get('history', [])
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
            player_name = participant.get('player_first_name', '')
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


def should_show_in_form_stat(current_event):
    """Determine if the in-form statistic should be displayed.

    Args:
        current_event: The current gameweek number.

    Returns:
        True if current_event >= 3, False otherwise.
    """
    return current_event >= 3

