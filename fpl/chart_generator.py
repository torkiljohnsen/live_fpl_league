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


def generate_rank_progression_chart(participants, theme="light", bg_color=None, width=1200, height=600):
    """Generate a rank progression chart for FPL participants.

    Args:
        participants: List of participant dictionaries, each containing 'history' array
                     with 'event' and 'overall_rank' fields.
        theme: Color theme for the chart. Options: "light" (default).
        bg_color: Optional custom background color (hex string). Overrides theme default.
        width: Width of the chart in pixels (default: 1200).
        height: Height of the chart in pixels (default: 600).

    Returns:
        A Plotly figure object with rank progression chart.
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
        colors = LIGHT_THEME_COLORS  # Default to light colors
        default_bg_color = "white"

    # Use custom bg_color if provided, otherwise use theme default
    final_bg_color = bg_color if bg_color is not None else default_bg_color

    # Add a line trace for each participant
    for i, participant in enumerate(participants):
        history = participant.get('history', [])

        # Extract event numbers and overall ranks
        events = [entry['event'] for entry in history]
        ranks = [entry['overall_rank'] for entry in history]

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

    # Configure X-axis
    fig.update_xaxes(title_text="Gameweek")

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

    return fig
