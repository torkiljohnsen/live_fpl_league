# Chart Themes

The chart generator supports multiple visual themes for FPL rank progression charts, allowing you to customize the appearance for different contexts and brand requirements.

## Available Themes

### Dark Theme (Default)
- **Background**: Dark gray (`rgba(0, 0, 0, 0.3)`)
- **Line colors**: Bright, vibrant colors for visibility
- **Text**: Light gray for readability on dark background
- **Best for**: Dashboards, TV displays, dark mode websites

### Light Theme
- **Background**: White
- **Line colors**: Standard Plotly colors
- **Text**: Dark colors for readability on light background
- **Best for**: Print, light mode websites, presentations

### Sinkaberg Corporate Theme
- **Background**: White (`#FFFFFF`)
- **Line colors**: Sinkaberg corporate color palette
- **Text**: Deep blue (`#00143C`)
- **Best for**: Corporate reports, branded materials

#### Sinkaberg Color Palette

1. **Lys blå (Light blue)** - `#3E7DEE` - Primary brand color
2. **Lakserød (Salmon red)** - `#F06848` - Accent/contrast color
3. **Mellomblå (Medium blue)** - `#023493`
4. **Mørk blå (Dark blue)** - `#1f295C`
5. **Dus lakserosa (Muted salmon pink)** - `#FAD2C8`
6. **Dyp blå (Deep blue)** - `#00143C`
7. **Dus blå (Muted blue)** - `#E2ECFC`

## Using Themes

### In Code

```python
from fpl.chart_generator import generate_rank_progression_chart

# Dark theme (default)
fig = generate_rank_progression_chart(
    participants=participants_data,
    theme="dark"  # or omit - dark is default
)

# Light theme
fig = generate_rank_progression_chart(
    participants=participants_data,
    theme="light"
)

# Sinkaberg corporate theme
fig = generate_rank_progression_chart(
    participants=participants_data,
    theme="sinkaberg"
)
```

### In HTML Generation

To change the theme for all generated HTML outputs, modify [`fpl/league_context.py`](../fpl/league_context.py) line 110:

```python
chart_svg = generate_rank_progression_chart(
    participants=participants_for_chart,
    output_format="svg",
    theme="sinkaberg"  # Change this to "dark", "light", or "sinkaberg"
)
```

Then regenerate the HTML files:

```bash
# Generate ranking progression with current theme
python generate_html.py -l 1638989 -o ranking_progression

# Generate all views for a league
python generate_html.py -l 1638989
```

## Custom Background Override

You can override the theme's default background color:

```python
fig = generate_rank_progression_chart(
    participants=participants_data,
    theme="dark",
    bg_color="#1a1a2e"  # Custom background color
)
```

## Adding a New Theme

To add a new theme, update `THEME_CONFIGS` in [`fpl/chart_generator.py`](../fpl/chart_generator.py):

```python
THEME_CONFIGS = {
    # ...existing themes...
    'my_theme': {
        'colors': ['#color1', '#color2', '#color3', ...],  # Line colors (cycled for many participants)
        'bg_color': '#ffffff',                              # Background color
        'text_color': 'rgba(0, 0, 0, 1)',                  # Title and legend text
        'tick_color': 'rgba(0, 0, 0, 1)',                  # Axis tick numbers
        'grid_color': 'rgba(128, 128, 128, 0.3)',          # Y-axis horizontal gridlines
        'xaxis_grid_color': 'rgba(128, 128, 128, 0.3)',    # X-axis vertical gridlines
        'zeroline_color': 'rgba(128, 128, 128, 0.5)',      # Zero line color
    }
}
```

### Color Selection Guidelines

- **Line colors**: Provide at least 7-10 distinct colors. The chart cycles through them for multiple participants.
- **Contrast**: Ensure good contrast between text/gridlines and background.
- **Accessibility**: Consider colorblind-friendly palettes (avoid red-green combinations).
- **Transparency**: Use `rgba()` with alpha < 1.0 for subtle gridlines and backgrounds.

## Testing

Test coverage is in [`tests/fpl_tests/test_chart_generator.py`](../tests/fpl_tests/test_chart_generator.py):

```bash
# Run all theme tests
python -m pytest tests/fpl_tests/test_chart_generator.py -k theme -v

# Run specific theme test
python -m pytest tests/fpl_tests/test_chart_generator.py::test_sinkaberg_theme_colors -v

# Run all chart generator tests
python -m pytest tests/fpl_tests/test_chart_generator.py -v
```

## Theme Comparison Table

| Theme | Background | Text Color | Line Colors | Use Case |
|-------|-----------|------------|-------------|----------|
| **dark** | Dark gray | Light gray | Bright/vibrant | Dashboards, TV displays |
| **light** | White | Dark | Standard | Print, presentations |
| **sinkaberg** | White | Deep blue | Corporate palette | Branded materials |

## Implementation Details

The theme system is implemented using a configuration dictionary (`THEME_CONFIGS`) that maps theme names to their visual settings. This architecture makes it easy to:

- Add new themes without modifying core chart generation logic
- Switch themes with a single parameter
- Override specific theme settings (e.g., `bg_color`)
- Maintain consistent styling across all charts

See [`fpl/chart_generator.py`](../fpl/chart_generator.py) for the complete implementation.

