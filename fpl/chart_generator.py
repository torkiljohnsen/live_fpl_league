"""Chart generation module for FPL rank progression visualization."""

import plotly.graph_objects as go

# Color palettes for different themes
LIGHT_THEME_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]


def generate_rank_progression_chart(participants, theme="light"):
    """Generate a rank progression chart for FPL participants.

    Args:
        participants: List of participant dictionaries, each containing 'history' array
                     with 'event' and 'overall_rank' fields.
        theme: Color theme for the chart. Options: "light" (default).

    Returns:
        A Plotly figure object with rank progression chart.
    """
    # Create empty figure
    fig = go.Figure()

    # Set color palette based on theme
    if theme == "light":
        colors = LIGHT_THEME_COLORS
        bg_color = "white"
    else:
        colors = LIGHT_THEME_COLORS  # Default to light colors for now
        bg_color = "white"

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
    fig.update_layout(plot_bgcolor=bg_color)

    return fig
