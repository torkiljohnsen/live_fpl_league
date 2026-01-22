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


def format_highest_team_value(participants):
    """Format the highest team value as a string.

    Args:
        participants: List of participant dictionaries.

    Returns:
        Formatted string: "Team name (Player name) - £XXX.XM"
        or None if no data is available.
    """
    result = get_highest_team_value(participants)
    if result is None:
        return None

    # Format: "Team name (Player name) - £XXX.XM"
    return f"{result['team_name']} ({result['player_name']}) - £{result['value']:.1f}M"
