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
    output_path=None,
    total_players=None,
    events=None
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
        total_players: Total number of FPL players (from bootstrap-static). If provided,
                      sets Y-axis range from 1 to total_players.
        events: List of event dictionaries from bootstrap-static, each containing 'id' and
               'finished' fields. Used to mark unfinished gameweeks with asterisk.

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
        text_color = "rgba(42, 63, 95, 1)"  # Dark text for light theme
        tick_color = "rgba(42, 63, 95, 1)"  # Dark text for axis numbers
        grid_color = "rgba(128, 128, 128, 0.3)"
    elif theme == "dark":
        colors = DARK_THEME_COLORS
        default_bg_color = "rgba(0, 0, 0, 0.1)"
        text_color = "rgba(200, 200, 200, 1)"  # Light text for dark theme
        tick_color = "rgba(180, 180, 180, 1)"  # Slightly dimmer for axis numbers
        grid_color = "rgba(100, 100, 100, 0.3)"  # Lighter gridlines
    else:
        colors = DARK_THEME_COLORS  # Default to dark colors
        default_bg_color = "rgba(0, 0, 0, 0.1)"
        text_color = "rgba(200, 200, 200, 1)"
        tick_color = "rgba(180, 180, 180, 1)"
        grid_color = "rgba(100, 100, 100, 0.3)"

    # Use custom bg_color if provided, otherwise use theme default
    final_bg_color = bg_color if bg_color is not None else default_bg_color

    # Add a line trace for each participant
    all_events = []
    for i, participant in enumerate(participants):
        history = participant.get('history', [])

        # Extract event numbers and overall ranks
        event_numbers = [entry['event'] for entry in history]
        ranks = [entry['overall_rank'] for entry in history]

        # Track all event numbers to determine X-axis range
        all_events.extend(event_numbers)

        # Select color from palette (cycle through if more participants than colors)
        color = colors[i % len(colors)]

        # Create legend label with enhanced format: "<league_rank>. <first_name> (<overall_rank_rounded>)"
        first_name = participant.get('player_first_name', 'Unknown')
        league_rank = participant.get('league_rank')

        # Get the latest overall_rank from history and format appropriately
        if history:
            latest_overall_rank = history[-1].get('overall_rank', 0)
            # Format based on magnitude: use "M" for millions, "k" for thousands
            if latest_overall_rank >= 1000000:
                # Display as millions with 2 decimal places
                overall_rank_value = latest_overall_rank / 1000000
                overall_rank_str = f"{overall_rank_value:.2f}M"
            else:
                # Display as thousands, rounded to nearest thousand
                # Use int(x + 0.5) for consistent rounding (always up at .5)
                overall_rank_rounded = int(latest_overall_rank / 1000 + 0.5)
                overall_rank_str = f"{overall_rank_rounded}k"
        else:
            overall_rank_str = "0k"

        # Format legend label
        if league_rank is not None:
            legend_label = f"{league_rank}. {first_name} ({overall_rank_str})"
        else:
            # Fallback if league_rank is not provided
            legend_label = first_name

        # Add line trace for this participant
        fig.add_trace(go.Scatter(
            x=event_numbers,
            y=ranks,
            mode='lines+markers',
            name=legend_label,
            line={'color': color}
        ))

    # Configure X-axis to show only integer gameweek numbers
    # Set dtick=1 to ensure tick marks appear at every whole number
    xaxis_config = {
        'title_text': "Gameweek",
        'dtick': 1,
        'title_font': {'color': text_color},
        'tickfont': {'color': tick_color}
    }

    # If we have data, set the range from 1 to the latest gameweek
    if all_events:
        min_event = min(all_events)
        max_event = max(all_events)
        # Add small padding to make sure all data points are visible
        xaxis_config['range'] = [min_event - 0.5, max_event + 0.5]

    # If events data is provided, mark unfinished gameweeks with asterisk
    if events is not None and all_events:
        # Create a mapping of event_id -> finished status
        event_status = {event['id']: event['finished'] for event in events}

        # Generate tick values and text for all events in range
        min_event = min(all_events)
        max_event = max(all_events)
        tick_vals = list(range(min_event, max_event + 1))
        tick_text = []

        for event_id in tick_vals:
            # Add asterisk to unfinished events
            if event_id in event_status and not event_status[event_id]:
                tick_text.append(f"{event_id}*")
            else:
                tick_text.append(str(event_id))

        xaxis_config['tickvals'] = tick_vals
        xaxis_config['ticktext'] = tick_text

    fig.update_xaxes(**xaxis_config)

    # Configure Y-axis (inverted so lower rank appears at top)
    yaxis_config = {
        'title_text': "Overall Rank",
        'autorange': "reversed",
        'showgrid': True,
        'gridcolor': grid_color,
        'title_font': {'color': text_color},
        'tickfont': {'color': tick_color}
    }

    # If total_players is provided, set explicit range from 1 to total_players
    if total_players is not None:
        yaxis_config['range'] = [total_players, 1]

    fig.update_yaxes(**yaxis_config)

    # Set background color (both plot and paper for consistent appearance)
    fig.update_layout(
        plot_bgcolor=final_bg_color,
        paper_bgcolor=final_bg_color,
        width=width,
        height=height,
        showlegend=True,
        legend={'font': {'color': text_color}}
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
