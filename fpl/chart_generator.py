"""Chart generation module for FPL rank progression visualization."""

import plotly.graph_objects as go

# Color palettes for different themes
LIGHT_THEME_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]

DARK_THEME_COLORS = [
    '#66c2ff', '#ffb366', '#66ff8c', '#ff6b6b', '#d896ff',
    '#c2a17a', '#ff99d8', '#b3b3b3', '#f2f266', '#66fff2'
]


def generate_rank_progression_chart(
    participants,
    theme="dark",
    bg_color=None,
    width=1200,
    height=600,
    output_format="figure",
    output_path=None
):
    """Generate a rank progression chart for FPL participants.

    Args:
        participants: List of participant dictionaries, each containing 'history' array
                     with 'event' and 'overall_rank' fields.
        theme: Color theme for the chart. Options: "light", "dark" (default).
        bg_color: Optional custom background color (hex string). Overrides theme default.
        width: Width of the chart in pixels (default: 1200).
        height: Height of the chart in pixels (default: 600).
        output_format: Output format. Options: "figure" (default), "svg", "png".
        output_path: File path for PNG output (required when output_format="png").

    Returns:
        If output_format="figure": A Plotly figure object.
        If output_format="svg": An SVG string representation of the chart.
        If output_format="png": None (writes PNG file to output_path).
    """
    # Create empty figure
    fig = go.Figure()

    # Set color palette based on theme
    if theme == "light":
        colors = LIGHT_THEME_COLORS
        default_bg_color = "white"
    elif theme == "dark":
        colors = DARK_THEME_COLORS
        default_bg_color = "#222222"
    else:
        colors = DARK_THEME_COLORS  # Default to dark colors
        default_bg_color = "#222222"

    # Use custom bg_color if provided, otherwise use theme default
    final_bg_color = bg_color if bg_color is not None else default_bg_color

    # Add a line trace for each participant
    all_events = []
    for i, participant in enumerate(participants):
        history = participant.get('history', [])

        # Extract event numbers and overall ranks
        events = [entry['event'] for entry in history]
        ranks = [entry['overall_rank'] for entry in history]

        # Track all event numbers to determine X-axis range
        all_events.extend(events)

        # Select color from palette (cycle through if more participants than colors)
        color = colors[i % len(colors)]

        # Add line trace for this participant
        fig.add_trace(go.Scatter(
            x=events,
            y=ranks,
            mode='lines+markers',
            name=participant.get('player_first_name', 'Unknown'),
            line={'color': color}
        ))

    # Configure X-axis to show only integer gameweek numbers
    # Set dtick=1 to ensure tick marks appear at every whole number
    xaxis_config = {'title_text': "Gameweek", 'dtick': 1}

    # If we have data, set the range from 1 to the latest gameweek
    if all_events:
        min_event = min(all_events)
        max_event = max(all_events)
        # Add small padding to make sure all data points are visible
        xaxis_config['range'] = [min_event - 0.5, max_event + 0.5]

    fig.update_xaxes(**xaxis_config)

    # Configure Y-axis (inverted so lower rank appears at top)
    fig.update_yaxes(
        title_text="Overall Rank",
        autorange="reversed"
    )

    # Set background color
    fig.update_layout(
        plot_bgcolor=final_bg_color,
        width=width,
        height=height,
        showlegend=True
    )

    # Return based on requested format
    if output_format == "svg":
        return fig.to_image(format="svg").decode('utf-8')
    elif output_format == "png":
        if output_path is None:
            raise ValueError("output_path is required when output_format='png'")
        fig.write_image(output_path, format="png")
        return None
    else:
        return fig
