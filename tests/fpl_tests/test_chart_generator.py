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


def test_custom_background_color_override():
    """Test that custom bg_color parameter overrides theme defaults."""
    # Arrange
    custom_color = "#ff0000"  # Red
    participants = [
        {
            'player_first_name': 'John',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
            ]
        }
    ]

    # Act
    fig_light = generate_rank_progression_chart(participants, theme="light", bg_color=custom_color)
    fig_dark = generate_rank_progression_chart(participants, theme="dark", bg_color=custom_color)

    # Assert
    # Custom color should override light theme default
    assert fig_light.layout.plot_bgcolor == custom_color, \
        f"Custom bg_color should override light theme default, got {fig_light.layout.plot_bgcolor}"

    # Custom color should override dark theme default
    assert fig_dark.layout.plot_bgcolor == custom_color, \
        f"Custom bg_color should override dark theme default, got {fig_dark.layout.plot_bgcolor}"


def test_configurable_chart_dimensions():
    """Test that width and height parameters control chart size."""
    # Arrange
    participants = [
        {
            'player_first_name': 'John',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
            ]
        }
    ]
    custom_width = 800
    custom_height = 400

    # Act
    fig = generate_rank_progression_chart(participants, width=custom_width, height=custom_height)

    # Assert
    assert fig.layout.width == custom_width, f"Chart width should be {custom_width}, got {fig.layout.width}"
    assert fig.layout.height == custom_height, f"Chart height should be {custom_height}, got {fig.layout.height}"


def test_legend_with_participant_names():
    """Test that legend shows participant first names and is visible."""
    # Arrange
    participants = [
        {
            'player_first_name': 'Alice',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
            ]
        },
        {
            'player_first_name': 'Bob',
            'history': [
                {'event': 1, 'overall_rank': 800000},
                {'event': 2, 'overall_rank': 750000},
            ]
        },
        {
            'player_first_name': 'Charlie',
            'history': [
                {'event': 1, 'overall_rank': 1200000},
                {'event': 2, 'overall_rank': 1100000},
            ]
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants)

    # Assert
    # Check that each trace has the correct name label
    assert len(fig.data) == 3, "Should have 3 traces"
    assert fig.data[0].name == 'Alice', f"First trace should be named 'Alice', got {fig.data[0].name}"
    assert fig.data[1].name == 'Bob', f"Second trace should be named 'Bob', got {fig.data[1].name}"
    assert fig.data[2].name == 'Charlie', f"Third trace should be named 'Charlie', got {fig.data[2].name}"

    # Check that legend is visible
    # By default, Plotly shows legend unless explicitly hidden
    # We check that showlegend is not False
    legend_visible = fig.layout.showlegend
    assert legend_visible is not False, f"Legend should be visible, got showlegend={legend_visible}"


def test_svg_export():
    """Test that chart can be exported as SVG string."""
    # Arrange
    participants = [
        {
            'player_first_name': 'Alice',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
                {'event': 3, 'overall_rank': 900000},
            ]
        },
        {
            'player_first_name': 'Bob',
            'history': [
                {'event': 1, 'overall_rank': 800000},
                {'event': 2, 'overall_rank': 750000},
                {'event': 3, 'overall_rank': 700000},
            ]
        }
    ]

    # Act
    svg_string = generate_rank_progression_chart(participants, output_format="svg")

    # Assert
    assert isinstance(svg_string, str), "SVG export should return a string"
    assert svg_string.startswith('<svg'), f"SVG string should start with '<svg' tag, got: {svg_string[:20]}"
    assert '</svg>' in svg_string, "SVG string should contain closing '</svg>' tag"

    # Verify it contains expected elements (basic sanity check)
    assert 'Gameweek' in svg_string, "SVG should contain X-axis label 'Gameweek'"
    assert 'Overall Rank' in svg_string, "SVG should contain Y-axis label 'Overall Rank'"


def test_png_export():
    """Test that chart can be exported as PNG file."""
    import os
    import tempfile

    # Arrange
    participants = [
        {
            'player_first_name': 'Alice',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
                {'event': 3, 'overall_rank': 900000},
            ]
        },
        {
            'player_first_name': 'Bob',
            'history': [
                {'event': 1, 'overall_rank': 800000},
                {'event': 2, 'overall_rank': 750000},
                {'event': 3, 'overall_rank': 700000},
            ]
        }
    ]

    # Create a temporary file for PNG output
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp_file:
        output_path = tmp_file.name

    try:
        # Act
        generate_rank_progression_chart(participants, output_format="png", output_path=output_path)

        # Assert
        assert os.path.exists(output_path), f"PNG file should be created at {output_path}"

        # Verify it's a valid PNG file (check PNG magic bytes)
        with open(output_path, 'rb') as f:
            header = f.read(8)
            # PNG files start with: 89 50 4E 47 0D 0A 1A 0A
            assert header[:4] == b'\x89PNG', "File should have valid PNG header"

        # Verify file has content
        file_size = os.path.getsize(output_path)
        assert file_size > 1000, f"PNG file should have substantial content, got {file_size} bytes"

    finally:
        # Cleanup: remove the temporary file
        if os.path.exists(output_path):
            os.remove(output_path)


def test_incomplete_participant_history():
    """Test that chart handles participants who joined mid-season."""
    # Arrange
    participants = [
        {
            'player_first_name': 'EarlyJoiner',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
                {'event': 3, 'overall_rank': 900000},
                {'event': 4, 'overall_rank': 875000},
                {'event': 5, 'overall_rank': 850000},
            ]
        },
        {
            'player_first_name': 'MidSeasonJoiner',
            'history': [
                # Missing GW 1-4, starts at GW5
                {'event': 5, 'overall_rank': 2000000},
                {'event': 6, 'overall_rank': 1950000},
                {'event': 7, 'overall_rank': 1900000},
            ]
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants)

    # Assert
    assert len(fig.data) == 2, "Figure should have two traces for two participants"

    # Check first participant (full history from GW1)
    trace_0 = fig.data[0]
    assert list(trace_0.x) == [1, 2, 3, 4, 5], "First trace should have full history"
    assert list(trace_0.y) == [1000000, 950000, 900000, 875000, 850000]

    # Check second participant (history starts at GW5)
    trace_1 = fig.data[1]
    assert list(trace_1.x) == [5, 6, 7], "Second trace should start from GW5"
    assert list(trace_1.y) == [2000000, 1950000, 1900000]


def test_x_axis_shows_only_integer_gameweeks():
    """Test that X-axis displays only whole integer gameweek numbers."""
    # Arrange
    participants = [
        {
            'player_first_name': 'Alice',
            'history': [
                {'event': 1, 'overall_rank': 1000000},
                {'event': 2, 'overall_rank': 950000},
                {'event': 3, 'overall_rank': 900000},
                {'event': 4, 'overall_rank': 875000},
                {'event': 5, 'overall_rank': 850000},
                {'event': 6, 'overall_rank': 825000},
                {'event': 7, 'overall_rank': 800000},
            ]
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants)

    # Assert
    # Check that X-axis tick values are integers
    # In Plotly, we can configure tickmode and tickvals to force specific tick values
    xaxis = fig.layout.xaxis

    # Verify tickmode is set to 'linear' or tick values are explicitly defined
    # We expect tick values to be [1, 2, 3, 4, 5, 6, 7]
    expected_ticks = [1, 2, 3, 4, 5, 6, 7]

    # Check if tickvals are explicitly set
    if xaxis.tickvals is not None:
        actual_ticks = list(xaxis.tickvals)
        assert actual_ticks == expected_ticks, \
            f"X-axis tick values should be integers {expected_ticks}, got {actual_ticks}"
    else:
        # If not explicitly set, check that dtick is 1 to ensure integer spacing
        # dtick controls the spacing between ticks
        assert xaxis.dtick == 1, \
            f"X-axis dtick should be 1 to ensure integer ticks, got {xaxis.dtick}"

    # Verify X-axis range covers from 1 to latest gameweek
    # Range should be [0.5, 7.5] or [1, 7] or similar to encompass all data
    if xaxis.range is not None:
        xrange = xaxis.range
        assert xrange[0] <= 1, f"X-axis should start at or before 1, got {xrange[0]}"
        assert xrange[1] >= 7, f"X-axis should end at or after 7, got {xrange[1]}"


def test_default_theme_is_dark():
    """Test that dark theme is used by default when no theme parameter is provided."""
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

    # Act - Call without theme parameter
    fig = generate_rank_progression_chart(participants)

    # Assert - Should use dark theme as default
    bg_color = fig.layout.plot_bgcolor
    assert bg_color is not None, "Background color should be set"

    # For dark theme, we expect dark colors
    dark_colors = ['black', '#000000', '#000', '#1a1a1a', '#2b2b2b', '#333333', '#222222']
    is_dark = bg_color in dark_colors
    assert is_dark, f"Default theme should be dark, got background color: {bg_color}"

    # Check that line colors are light/bright (suitable for dark background)
    for i, trace in enumerate(fig.data):
        line_color = trace.line.color
        assert line_color is not None, f"Trace {i} should have a line color set"
        # Light colors should not be from the standard dark palette (darker colors)
        # Dark theme uses bright colors like #66c2ff, #ffb366, etc.


def test_y_axis_range_set_from_total_players():
    """Test that Y-axis range is set from 1 to total_players."""
    # Arrange
    total_players = 10000000
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
        }
    ]

    # Act
    fig = generate_rank_progression_chart(participants, total_players=total_players)

    # Assert
    # Y-axis should be explicitly set from 1 (top) to total_players (bottom)
    assert fig.layout.yaxis.range is not None, "Y-axis range should be explicitly set"

    # The range is reversed (autorange='reversed'), so it should be [total_players, 1]
    # which displays 1 at the top and total_players at the bottom
    y_range = fig.layout.yaxis.range
    assert len(y_range) == 2, "Y-axis range should have two values [start, end]"
    assert y_range[0] == total_players, f"Y-axis should start at total_players ({total_players})"
    assert y_range[1] == 1, "Y-axis should end at 1"

    # Verify Y-axis is still reversed
    assert fig.layout.yaxis.autorange == "reversed", "Y-axis should still be reversed"
