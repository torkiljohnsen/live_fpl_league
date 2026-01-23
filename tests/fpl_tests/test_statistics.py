"""Tests for FPL statistics calculation module."""



from fpl.participant import Participant


def make_test_participant(
    first_name: str,
    history: list[dict],
    entry_id: int = 1,
    league_rank: int = 1
) -> Participant:
    """Helper to create test Participant objects."""
    return Participant(
        entry_id=entry_id,
        team_name=f"{first_name}'s Team",
        manager_name=f"{first_name} Doe",
        total_score=0,
        history=history,
        last_event={},
        league_rank=league_rank
    )

def test_highest_team_value_calculation():
    """Test that highest team value statistic is correctly calculated."""
    # Arrange
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000, 'bank': 5, 'value': 995},
                {'event': 2, 'overall_rank': 450000, 'bank': 10, 'value': 1000},  # Team value: 1000/10 = 100.0M
            ]
        ),
        make_test_participant(
            first_name='Anders',
            history=[
                {'event': 1, 'overall_rank': 600000, 'bank': 15, 'value': 990},
                # Team value: 1005/10 = 100.5M (highest)
                {'event': 2, 'overall_rank': 550000, 'bank': 20, 'value': 1005},
            ]
        ),
        make_test_participant(
            first_name='Eirin',
            history=[
                {'event': 1, 'overall_rank': 700000, 'bank': 0, 'value': 1000},
                {'event': 2, 'overall_rank': 650000, 'bank': 5, 'value': 995},  # Team value: 995/10 = 99.5M
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_highest_team_value
    result = get_highest_team_value(participants)

    # Assert
    assert result is not None, "Should return a result for participants with team value data"
    assert 'team_name' in result, "Result should contain team_name"
    assert 'player_name' in result, "Result should contain player_name"
    assert 'value' in result, "Result should contain value"

    # Verify highest team value is correctly identified
    assert result['team_name'] == "Anders's Team", "Should identify Anders's Team as having highest value"
    assert result['player_name'] == 'Anders', "Should identify Anders as the player"
    assert result['value'] == 100.5, f"Value should be 100.5M, got {result['value']}"


def test_highest_team_value_with_no_history():
    """Test that function handles participants with no history gracefully."""
    # Arrange
    participants = [
        make_test_participant(
            first_name='Nobody',
            history=[]
        ),
    ]

    # Act
    from fpl.statistics import get_highest_team_value
    result = get_highest_team_value(participants)

    # Assert
    assert result is None, "Should return None when no history data is available"


def test_in_form_consecutive_green_arrows():
    """Test that in-form statistic correctly counts consecutive rank decreases."""
    # Arrange
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 450000},  # ↓ (improvement)
                {'event': 3, 'overall_rank': 400000},  # ↓ (improvement) - 2 consecutive
                {'event': 4, 'overall_rank': 350000},  # ↓ (improvement) - 3 consecutive
                {'event': 5, 'overall_rank': 340000},  # ↓ (improvement) - 4 consecutive
            ]
        ),
        make_test_participant(
            first_name='Anders',
            history=[
                {'event': 1, 'overall_rank': 600000},
                {'event': 2, 'overall_rank': 550000},  # ↓ (improvement)
                {'event': 3, 'overall_rank': 500000},  # ↓ (improvement) - 2 consecutive
                {'event': 4, 'overall_rank': 510000},  # ↑ (worse) - streak ends
                {'event': 5, 'overall_rank': 500000},  # ↓ (improvement) - new streak of 1
            ]
        ),
        make_test_participant(
            first_name='Eirin',
            history=[
                {'event': 1, 'overall_rank': 700000},
                {'event': 2, 'overall_rank': 690000},  # ↓ (improvement)
                {'event': 3, 'overall_rank': 680000},  # ↓ (improvement) - 2 consecutive
                {'event': 4, 'overall_rank': 670000},  # ↓ (improvement) - 3 consecutive
                {'event': 5, 'overall_rank': 660000},  # ↓ (improvement) - 4 consecutive
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_in_form_players
    result = get_in_form_players(participants)

    # Assert
    assert result is not None, "Should return result for participants with history"
    assert 'count' in result, "Result should contain consecutive count"
    assert 'players' in result, "Result should contain list of players"

    # Both Torkil and Eirin have 4 consecutive green arrows
    assert result['count'] == 4, f"Should identify 4 consecutive green arrows, got {result['count']}"
    assert len(result['players']) == 2, f"Should identify 2 players tied at 4, got {len(result['players'])}"
    assert 'Torkil' in result['players'], "Torkil should be in the list"
    assert 'Eirin' in result['players'], "Eirin should be in the list"


def test_in_form_no_green_arrows():
    """Test that in-form statistic returns None when no team has green arrows."""
    # Arrange
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 510000},  # ↑ (worse)
                {'event': 3, 'overall_rank': 520000},  # ↑ (worse)
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_in_form_players
    result = get_in_form_players(participants)

    # Assert
    assert result is None, "Should return None when no team has green arrows"


def test_in_form_single_player():
    """Test that in-form statistic works with single player having green arrows."""
    # Arrange
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 450000},  # ↓ (improvement)
                {'event': 3, 'overall_rank': 400000},  # ↓ (improvement) - 2 consecutive
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_in_form_players
    result = get_in_form_players(participants)

    # Assert
    assert result is not None, "Should return result"
    assert result['count'] == 2, f"Should have 2 consecutive green arrows, got {result['count']}"
    assert len(result['players']) == 1, "Should have one player"
    assert 'Torkil' in result['players'], "Torkil should be in the list"


def test_in_form_before_event_3():
    """Test that in-form statistic is hidden before event 3."""
    # Arrange
    current_event = 2

    # Act
    from fpl.statistics import should_show_in_form_stat
    result = should_show_in_form_stat(current_event)

    # Assert
    assert result is False, "Should not show in-form stat before event 3"


def test_in_form_at_event_3():
    """Test that in-form statistic is shown from event 3 onwards."""
    # Arrange
    current_event = 3

    # Act
    from fpl.statistics import should_show_in_form_stat
    result = should_show_in_form_stat(current_event)

    # Assert
    assert result is True, "Should show in-form stat from event 3 onwards"
