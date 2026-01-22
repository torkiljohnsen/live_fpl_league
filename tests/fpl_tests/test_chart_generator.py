"""Tests for chart generator functionality."""

import pytest
from fpl.chart_generator import generate_rank_progression_chart


def test_empty_chart_has_proper_axes():
    """Test that chart generator creates empty figure with proper axis setup."""
    # Arrange
    participants = []
    
    # Act
    fig = generate_rank_progression_chart(participants)
    
    # Assert
    assert fig is not None, "Function should return a figure object"
    
    # Check that it's a Plotly figure
    assert hasattr(fig, 'data'), "Should be a Plotly figure with data attribute"
    assert hasattr(fig, 'layout'), "Should be a Plotly figure with layout attribute"
    
    # Check X-axis label
    assert fig.layout.xaxis.title.text == "Gameweek", "X-axis should be labeled 'Gameweek'"
    
    # Check Y-axis label
    assert fig.layout.yaxis.title.text == "Overall Rank", "Y-axis should be labeled 'Overall Rank'"
    
    # Check Y-axis is inverted (reversed=True means lower rank at top)
    assert fig.layout.yaxis.autorange == "reversed", "Y-axis should be inverted (reversed=True)"


def test_single_participant_line():
    """Test that chart plots one participant's rank progression."""
    # Arrange
    participants = [
        {
            'player_first_name': 'John',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
                {'event': 3, 'overall_rank': 900000},
                {'event': 4, 'overall_rank': 875000},
            ]
        }
    ]
    
    # Act
    fig = generate_rank_progression_chart(participants)
    
    # Assert
    assert len(fig.data) == 1, "Figure should have exactly one trace for one participant"
    
    trace = fig.data[0]
    
    # Check that trace contains correct data points
    expected_events = [1, 2, 3, 4]
    expected_ranks = [1000000, 950000, 900000, 875000]
    
    assert list(trace.x) == expected_events, f"X-axis data should match events: {expected_events}"
    assert list(trace.y) == expected_ranks, f"Y-axis data should match ranks: {expected_ranks}"
