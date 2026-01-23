"""Tests for FPL statistics calculation module."""

from .test_utils import make_test_participant


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


def test_get_player_with_highest_rank_loss():
    """Test rank loss calculation over last 5 gameweeks (or fewer if fewer events have passed)."""
    # Test Case 1: Normal case with 20% rank loss over 5 gameweeks
    # Arrange
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 480000},
                {'event': 3, 'overall_rank': 460000},
                {'event': 4, 'overall_rank': 450000},
                {'event': 5, 'overall_rank': 500000},  # Rank 500k -> 500k, no change
                {'event': 6, 'overall_rank': 520000},  # Rank 450k -> 520k = 15.6% loss over 5 GWs
            ]
        ),
        make_test_participant(
            first_name='Anders',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 500000},
                {'event': 3, 'overall_rank': 500000},
                {'event': 4, 'overall_rank': 500000},
                {'event': 5, 'overall_rank': 500000},
                {'event': 6, 'overall_rank': 600000},  # Rank 500k -> 600k = 20% loss over 5 GWs (highest)
            ]
        ),
        make_test_participant(
            first_name='Eirin',
            history=[
                {'event': 1, 'overall_rank': 700000},
                {'event': 2, 'overall_rank': 680000},
                {'event': 3, 'overall_rank': 660000},
                {'event': 4, 'overall_rank': 640000},
                {'event': 5, 'overall_rank': 620000},
                {'event': 6, 'overall_rank': 610000},  # Rank 620k -> 610k, improvement
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_player_with_highest_rank_loss
    result = get_player_with_highest_rank_loss(participants, current_event=6)

    # Assert
    assert result is not None, "Should return a result when there is rank loss"
    assert 'player_name' in result, "Result should contain player_name"
    assert 'rank_loss_percent' in result, "Result should contain rank_loss_percent"
    assert 'num_rounds' in result, "Result should contain num_rounds"
    assert 'old_rank' in result, "Result should contain old_rank"
    assert 'new_rank' in result, "Result should contain new_rank"

    assert result['player_name'] == 'Anders', "Should identify Anders as having highest rank loss"
    assert result['rank_loss_percent'] == 20.0, f"Should be 20% loss, got {result['rank_loss_percent']}"
    assert result['num_rounds'] == 5, f"Should compare 5 rounds, got {result['num_rounds']}"
    assert result['old_rank'] == 500000, f"Old rank should be 500000, got {result['old_rank']}"
    assert result['new_rank'] == 600000, f"New rank should be 600000, got {result['new_rank']}"


def test_get_player_with_highest_rank_loss_no_losses():
    """Test that function returns None when no players have rank loss."""
    # Arrange - all players improved
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 480000},
                {'event': 3, 'overall_rank': 460000},
                {'event': 4, 'overall_rank': 450000},
                {'event': 5, 'overall_rank': 440000},
                {'event': 6, 'overall_rank': 430000},  # Improved
            ]
        ),
        make_test_participant(
            first_name='Anders',
            history=[
                {'event': 1, 'overall_rank': 600000},
                {'event': 2, 'overall_rank': 590000},
                {'event': 3, 'overall_rank': 580000},
                {'event': 4, 'overall_rank': 570000},
                {'event': 5, 'overall_rank': 560000},
                {'event': 6, 'overall_rank': 550000},  # Improved
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_player_with_highest_rank_loss
    result = get_player_with_highest_rank_loss(participants, current_event=6)

    # Assert
    assert result is None, "Should return None when no rank losses"


def test_get_player_with_highest_rank_loss_fewer_than_5_gameweeks():
    """Test that function works with fewer than 5 gameweeks (e.g., event 3)."""
    # Arrange - only 3 events available
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 510000},  # Small loss
                {'event': 3, 'overall_rank': 520000},  # Total: 500k -> 520k = 4% loss
            ]
        ),
        make_test_participant(
            first_name='Anders',
            history=[
                {'event': 1, 'overall_rank': 500000},
                {'event': 2, 'overall_rank': 550000},
                {'event': 3, 'overall_rank': 600000},  # Total: 500k -> 600k = 20% loss (highest)
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_player_with_highest_rank_loss
    result = get_player_with_highest_rank_loss(participants, current_event=3)

    # Assert
    assert result is not None, "Should work with fewer than 5 gameweeks"
    assert result['player_name'] == 'Anders', "Should identify Anders as having highest rank loss"
    assert result['rank_loss_percent'] == 20.0, f"Should be 20% loss, got {result['rank_loss_percent']}"
    assert result['num_rounds'] == 2, f"Should compare 2 rounds (event 1 to 3), got {result['num_rounds']}"


def test_get_player_with_highest_rank_loss_event_1():
    """Test that function returns None for event 1 (no comparison possible)."""
    # Arrange
    participants = [
        make_test_participant(
            first_name='Torkil',
            history=[
                {'event': 1, 'overall_rank': 500000},
            ]
        ),
    ]

    # Act
    from fpl.statistics import get_player_with_highest_rank_loss
    result = get_player_with_highest_rank_loss(participants, current_event=1)

    # Assert
    assert result is None, "Should return None for event 1 (no comparison possible)"
