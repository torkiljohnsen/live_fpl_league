# AGENTS.md - Live FPL League Dashboard

Generates static HTML dashboards for Fantasy Premier League mini-leagues showing live standings and gameweek history.

## Knowledge collection

When you learn something new about this repo that is of use to users or agents, add it to README.md or AGENTS.md, respectively. You can also place AGENTS.md-files in subfolders if you think there is a need for this.

Add new knowledge sparingly, and do so in a consise way.

## Architecture Flow

**Data Collection → Context Building → Template Rendering → Static HTML Output**

### 1. Data Collection
[`fpl/fpl_api.py`](fpl/fpl_api.py) - API client with dev mode support
- **Live mode**: Fetches from `fantasy.premierleague.com/api`
- **Dev mode**: Uses/generates sample JSON files in [`fpl/sample_data/`](fpl/sample_data/)
- Key methods: [`get_bootstrap_static()`](fpl/fpl_api.py), [`get_league_standings()`](fpl/fpl_api.py), [`get_team_history()`](fpl/fpl_api.py), [`get_team_picks()`](fpl/fpl_api.py)

### 2. Data Processing
[`fpl/fpl_league.py`](fpl/fpl_league.py) - Aggregates API data into league summary
- Fetches bootstrap data (events, chips), league standings, team histories
- [`FPLLeague.get_summary()`](fpl/fpl_league.py) returns dict with participants, events, current gameweek

[`fpl/participant.py`](fpl/participant.py) - Processes individual team data (win counts, lowest rank counts)

[`fpl/rank_calculator.py`](fpl/rank_calculator.py) - Calculates round ranks for gameweek history

### 3. Context Building
[`fpl/league_context.py`](fpl/league_context.py) - Wraps league data for templates
- [`LeagueContext.build()`](fpl/league_context.py) creates context from league_id
- [`as_dict()`](fpl/league_context.py) provides template variables: `participants`, `event_ids`, `golden_event_ids`, `hidden_event_ids`, `logo_svg`

### 4. Template Rendering
[`fpl/league_template_renderer.py`](fpl/league_template_renderer.py) - Jinja2 rendering engine
- Templates in [`templates/`](templates/): [`league_standings.html`](templates/league_standings.html), [`league_gameweek_history.html`](templates/league_gameweek_history.html)
- [`write_html_output()`](fpl/league_template_renderer.py) generates HTML to [`docs/`](docs/) folder

### 5. Entry Points
[`generate_html.py`](generate_html.py) - Main generator script
```bash
python generate_html.py -l LEAGUE_ID [--dev] [-o standings|gw_history|ALL]
```
- Creates one [`FPL_API`](fpl/fpl_api.py) instance (shared across leagues)
- For each league: builds [`LeagueContext`](fpl/league_context.py), renders requested templates

[`generate_index.py`](generate_index.py) - Creates [`docs/index.html`](docs/index.html) listing all generated pages

## Directory Structure

- **[`fpl/`](fpl/)** - Core Python package for data fetching and processing
  - [`fpl_api.py`](fpl/fpl_api.py) - FPL API client
  - [`fpl_league.py`](fpl/fpl_league.py) - League data aggregation
  - [`league_context.py`](fpl/league_context.py) - Template context builder
  - [`league_template_renderer.py`](fpl/league_template_renderer.py) - Jinja2 renderer
  - [`chart_generator.py`](fpl/chart_generator.py) - Plotly chart generation for static PNG images
  - [`participant.py`](fpl/participant.py) - Team data processor
  - [`rank_calculator.py`](fpl/rank_calculator.py) - Gameweek rank calculations
  - [`chip_annotator.py`](fpl/chip_annotator.py) - Chip usage annotations
  - [`sample_data/`](fpl/sample_data/) - Sample API JSON responses for dev mode
    - `bootstrap_static_sample.json` - Global FPL data (events, chips, teams)
    - `leagues-classic_{league_id}_standings_sample.json` - League standings
    - `entry_{team_id}_history_sample.json` - Team gameweek history and chip usage

- **[`templates/`](templates/)** - Jinja2 HTML templates
  - [`league_standings.html`](templates/league_standings.html) - Current standings table
  - [`league_gameweek_history.html`](templates/league_gameweek_history.html) - Historical performance grid
  - [`base.html`](templates/base.html) - Base template with shared structure
  - [`index.html`](templates/index.html) - Index page template

- **[`docs/`](docs/)** - Generated static HTML output (GitHub Pages ready)
  - Generated HTML files for each league/view
  - [`style.css`](docs/style.css) - Shared stylesheet

- **[`tests/`](tests/)** - Test suite
  - [`fpl_tests/`](tests/fpl_tests/) - Main test modules
  - [`fpl_tests/data_samples/`](tests/fpl_tests/data_samples/) - Test fixtures

- **Root files**
  - [`generate_html.py`](generate_html.py) - Main HTML generation script
  - [`generate_index.py`](generate_index.py) - Index page generator
  - [`requirements.txt`](requirements.txt) - Python dependencies

## Key Conventions
- **Dev mode suffix**: Files end with `-dev.html` when using sample data
- **Golden gameweeks**: Every 4th gameweek (4, 8, 12...) marked with `golden_gameweek` CSS class
- **Template variables**: See [`templates/AGENTS.md`](templates/AGENTS.md) for full variable reference
- **CSS**: All styles in [`docs/style.css`](docs/style.css), no inline styles

## Testing
Tests in [`tests/fpl_tests/`](tests/fpl_tests/) use `DummyAPI` with sample data from [`tests/fpl_tests/data_samples/`](tests/fpl_tests/data_samples/)

## Agent Operational Guidelines

### Running Tests
The terminal needs the virtual environment activated to run tests easily. **Always activate the venv first**:

```bash
source venv/Scripts/activate && python -m pytest [test_path]
```

Examples:
```bash
# Run all tests
source venv/Scripts/activate && python -m pytest

# Run specific test file
source venv/Scripts/activate && python -m pytest tests/fpl_tests/test_chart_generator.py

# Run specific test
source venv/Scripts/activate && python -m pytest tests/fpl_tests/test_chart_generator.py::test_empty_chart_has_proper_axes -v
```

**Why not just `pytest`?** The Windows bash terminal doesn't have execute permissions on the pytest script directly, so use `python -m pytest` instead.

### Git Commits
Git commands work normally in the bash terminal. **Don't use `cd` with Windows-style paths** (backslashes).

```bash
# ❌ WRONG - bash doesn't understand backslashes
cd c:\Dev\live_fpl_league && git add -A

# ✅ CORRECT - git commands work from current directory
git add -A && git commit -m "Your message"

# ✅ CORRECT - use forward slashes if you need cd
cd /c/Dev/live_fpl_league && git add -A
```
