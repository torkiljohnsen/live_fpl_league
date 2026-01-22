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
