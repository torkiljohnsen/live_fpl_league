# AGENTS.md - Template Folder

Jinja2 templates for FPL league dashboards. Generated to `docs/` folder with `style.css`.

## Template Structure

All templates extend `base.html` (except index.html):
```jinja2
{% extends "base.html" %}
{% block title %}{{ name }} - Page Type{% endblock %}
{% block body %}
    <div class="logo-container"><div>{{ logo_svg | safe }}</div></div>
    <h1>{{ name }} Title {% if league_join_code %}({{ league_join_code }}){% endif %}</h1>
    <!-- content -->
{% endblock %}
```

**base.html** provides: HTML boilerplate, Google Fonts (Inter, Sora), `style.css` link (uses `{{ base_path | default('') }}` prefix for subfolder support), blocks: `title`, `extra_head`, `body`.

## Common Variables

League templates receive:
- `name` - League name
- `league_join_code` - Optional join code
- `logo_svg` - SVG markup (use `| safe`)
- `participants` - List of team dicts with: `manager_name`, `team_name`, `entry_id`, `total_points`, `history`, `last_event`
- `current_event_id` - Current gameweek
- `is_current_finished` - Boolean

`last_event` contains: `event`, `points`, `total_points`, `league_rank`, `league_rank_change`, `event_transfers_cost`, `chip`, `round_rank`

## Templates

**league_standings.html** - Table with class `league_standings`, shows ranks, names, chips, medals (🥇🥈🥉🚨), points. Rank changes: `positive_rank_change` / `negative_rank_change` classes.

**league_gameweek_history.html** - Table with class `gw_history`, grid of GW points. Uses `event_ids`, `hidden_event_ids`. Classes: `golden_gameweek` (every 4th), `gw_is_in_future`, `gw_hidden`, `round_rank_N`.

**ranking_progression.html** - Chart container with `<canvas id="rankingChart">` in `chart-container` div.

**narrative.html** - Reidar's Rapport article page. Receives: `title` (str), `subtitle` (str, e.g. "Runde 27"), `body_html` (str, rendered HTML), `hero_image` (str, image path), `base_path` (str, relative path to docs root, e.g. `../../../`), `league_id` (str), `league_name` (str), `season` (str). Structure: hero image, title/subtitle, navigation bar (Tabell, Rundehistorikk, Poengutvikling — all prefixed with `base_path`), article body, footer. Output to `docs/narratives/{season}/{league_id}/`.

**index.html** - Standalone (doesn't extend base). Uses `league_files` list of `(filename, title)` tuples.

## Key Rules

- **Norwegian labels**: "Spiller", "Lag", "Runde", "Poeng"
- **Always `| safe` for `logo_svg`**
- **No inline styles** (use CSS classes from `style.css`)
- **No `<body>` tags** in child templates
- **Handle optionals**: `{% if league_join_code %}`, `.get('key', default)`

## CSS Classes
`logo-container`, `league_standings`, `gw_history`, `chart-container`, `rank_col`, `player_col`, `entry_col`, `points_col`, `positive_rank_change`, `negative_rank_change`, `golden_gameweek`, `gw_is_in_future`, `gw_hidden`, `round_rank_N`, `narrative-hero`, `narrative-header`, `narrative-title`, `narrative-subtitle`, `narrative-nav`, `narrative-article`, `narrative-footer`
