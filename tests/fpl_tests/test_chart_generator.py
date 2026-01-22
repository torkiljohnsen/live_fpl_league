"""Tests for chart generator functionality."""

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


def test_multiple_participants_3_traces():
    """Test that chart plots three participants' rank progressions."""
    # Arrange
    participants = [
        {
            'player_first_name': 'John',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
                {'event': 3, 'overall_rank': 900000},
            ]
        },
        {
            'player_first_name': 'Jane',
            'history': [
                {'event': 1, 'overall_rank': 800000},
                {'event': 2, 'overall_rank': 750000},
                {'event': 3, 'overall_rank': 700000},
            ]
        },
        {
            'player_first_name': 'Bob',
            'history': [
                {'event': 1, 'overall_rank': 1200000},
                {'event': 2, 'overall_rank': 1150000},
                {'event': 3, 'overall_rank': 1100000},
            ]
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants)

    # Assert
    assert len(fig.data) == 3, "Figure should have exactly three traces for three participants"

    # Check first participant's data
    trace_0 = fig.data[0]
    assert list(trace_0.x) == [1, 2, 3], "First trace X-axis should match events"
    assert list(trace_0.y) == [1000000, 950000, 900000], "First trace Y-axis should match John's ranks"

    # Check second participant's data
    trace_1 = fig.data[1]
    assert list(trace_1.x) == [1, 2, 3], "Second trace X-axis should match events"
    assert list(trace_1.y) == [800000, 750000, 700000], "Second trace Y-axis should match Jane's ranks"

    # Check third participant's data
    trace_2 = fig.data[2]
    assert list(trace_2.x) == [1, 2, 3], "Third trace X-axis should match events"
    assert list(trace_2.y) == [1200000, 1150000, 1100000], "Third trace Y-axis should match Bob's ranks"


def test_multiple_participants_10_traces():
    """Test that chart plots ten participants' rank progressions."""
    # Arrange
    participants = []
    for i in range(10):
        participants.append({
            'player_first_name': f'Player{i}',
            'history': [
                {'event': 1, 'overall_rank': 1000000 + (i * 100000)},
                {'event': 2, 'overall_rank': 950000 + (i * 100000)},
            ]
        })

    # Act
    fig = generate_rank_progression_chart(participants)

    # Assert
    assert len(fig.data) == 10, "Figure should have exactly ten traces for ten participants"

    # Verify each trace has correct data
    for i, trace in enumerate(fig.data):
        expected_x = [1, 2]
        expected_y = [1000000 + (i * 100000), 950000 + (i * 100000)]
        assert list(trace.x) == expected_x, f"Trace {i} X-axis should match events"
        assert list(trace.y) == expected_y, f"Trace {i} Y-axis should match Player{i}'s ranks"


def test_light_theme_colors():
    """Test that light theme uses light background and dark lines."""
    # Arrange
    participants = [
        {
            'player_first_name': 'John',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
            ]
        },
        {
            'player_first_name': 'Jane',
            'history': [
                {'event': 1, 'overall_rank': 800000},
                {'event': 2, 'overall_rank': 750000},
            ]
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants, theme="light")

    # Assert
    # Check background is light colored (white or near-white)
    bg_color = fig.layout.plot_bgcolor
    assert bg_color is not None, "Background color should be set"
    # Accept various light color formats: white, #ffffff, #fff, rgb(255,255,255), or None (default white)
    # For light theme, we expect white or near-white
    light_colors = ['white', '#ffffff', '#fff', 'rgb(255,255,255)', 'rgb(255, 255, 255)', None, '']
    is_light = (bg_color in light_colors) or (isinstance(bg_color, str) and bg_color.startswith('#f'))
    assert is_light, f"Light theme should use light background, got: {bg_color}"

    # Check that line colors are dark/visible
    # Line colors should be distinguishable and dark for good visibility on light background
    for i, trace in enumerate(fig.data):
        line_color = trace.line.color
        assert line_color is not None, f"Trace {i} should have a line color set"
        # Dark colors should not be white or very light
        assert line_color not in ['white', '#ffffff', '#fff'], \
            f"Trace {i} should not use white/light color on light background: {line_color}"


def test_dark_theme_colors():
    """Test that dark theme uses dark background and light/bright lines."""
    # Arrange
    participants = [
        {
            'player_first_name': 'John',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
            ]
        },
        {
            'player_first_name': 'Jane',
            'history': [
                {'event': 1, 'overall_rank': 800000},
                {'event': 2, 'overall_rank': 750000},
            ]
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants, theme="dark")

    # Assert
    # Check background is dark colored
    bg_color = fig.layout.plot_bgcolor
    assert bg_color is not None, "Background color should be set"
    # For dark theme, we expect dark colors (black, dark gray, etc.)
    dark_colors = ['black', '#000000', '#000', '#1a1a1a', '#2b2b2b', '#333333', '#222222']
    is_dark = bg_color in dark_colors
    assert is_dark, f"Dark theme should use dark background, got: {bg_color}"

    # Check that line colors are light/bright for visibility on dark background
    for i, trace in enumerate(fig.data):
        line_color = trace.line.color
        assert line_color is not None, f"Trace {i} should have a line color set"
        # Light/bright colors should not be from the standard dark palette
        # We expect colors that are bright and visible on dark backgrounds
        dark_palette_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        assert line_color not in dark_palette_colors, \
            f"Trace {i} should not use dark palette color on dark background: {line_color}"
