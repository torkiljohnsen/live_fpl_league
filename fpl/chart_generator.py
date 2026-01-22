"""Chart generation module for FPL rank progression visualization."""

import plotly.graph_objects as go


def generate_rank_progression_chart(participants):
    """
    Generate a rank progression chart for FPL participants.
    
    Args:
        participants: List of participant dictionaries, each containing 'history' array
                     with 'event' and 'overall_rank' fields.
    
    Returns:
        A Plotly figure object with rank progression chart.
    """
    # Create empty figure
    fig = go.Figure()
    
    # Configure X-axis
    fig.update_xaxes(title_text="Gameweek")
    
    # Configure Y-axis (inverted so lower rank appears at top)
    fig.update_yaxes(
        title_text="Overall Rank",
        autorange="reversed"
    )
    
    return fig
