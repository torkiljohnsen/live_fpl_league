# fpl/ Module - Agent Documentation

## Code Organization Principles

**Separation of Concerns**: Keep calculation logic separate from presentation formatting.

- **[`statistics.py`](statistics.py)** - Pure calculations returning raw data structures (dicts with counts, values, lists). No string formatting or language-specific text.
- **[`league_context.py`](league_context.py)** - Presentation layer that formats statistics for templates (Norwegian text, currency symbols, arrow symbols). Bridge between raw data and template-ready strings.

This separation makes code more testable and easier to internationalize.

## Module Overview

### Data Collection
**[`fpl_api.py`](fpl_api.py)** - API client with dev mode support
- **Live mode**: Fetches from `fantasy.premierleague.com/api`
- **Dev mode**: Automatic sample data management via `_read_sample_or_generate()`
  - If sample file exists: reads from [`sample_data/`](sample_data/)
  - If sample file missing: fetches from live API and saves to [`sample_data/`](sample_data/)
  - Sample files: `{endpoint}_sample.json` (e.g., `bootstrap-static_sample.json`, `entry_123_history_sample.json`)
  - Console output: `[dev_mode] Sample read:` or `[dev_mode] API called and sample generated:`
- Key methods: `get_bootstrap_static()`, `get_league_standings()`, `get_team_history()`, `get_team_picks()`

### Data Processing
**[`fpl_league.py`](fpl_league.py)** - Aggregates API data into league summary
- Fetches bootstrap data (events, chips), league standings, team histories
- `FPLLeague.get_summary()` returns dict with participants, events, current gameweek

**[`participant.py`](participant.py)** - Processes individual team data (win counts, lowest rank counts)

**[`rank_calculator.py`](rank_calculator.py)** - Calculates round ranks for gameweek history

**[`statistics.py`](statistics.py)** - Statistical calculations
- `get_highest_team_value()` - Returns team with highest value
- `get_in_form_players()` - Returns players with most consecutive rank improvements
- `should_show_in_form_stat()` - Business logic for stat visibility

### Context Building
**[`league_context.py`](league_context.py)** - Wraps league data for templates
- `LeagueContext.build()` creates context from league_id
- `as_dict()` provides template variables: `participants`, `event_ids`, `golden_event_ids`, `hidden_event_ids`, `logo_svg`
- Formats statistics with Norwegian text and symbols

### Rendering
**[`league_template_renderer.py`](league_template_renderer.py)** - Jinja2 rendering engine
- `write_html_output()` generates HTML to `docs/` folder

**[`chart_generator.py`](chart_generator.py)** - Plotly chart generation for static SVG/PNG images

**[`chip_annotator.py`](chip_annotator.py)** - Chip usage annotations

### Sample Data
**[`sample_data/`](sample_data/)** - Sample API JSON responses for dev mode
- `bootstrap_static_sample.json` - Global FPL data (events, chips, teams)
- `leagues-classic_{league_id}_standings_sample.json` - League standings
- `entry_{team_id}_history_sample.json` - Team gameweek history and chip usage

## Testing Guidelines

### Test File Naming
Each module should have a corresponding test file in `tests/fpl_tests/` following the pattern `test_<module_name>.py`.

Examples:
- [`fpl_api.py`](fpl_api.py) → `tests/fpl_tests/test_fpl_api.py`
- [`chart_generator.py`](chart_generator.py) → `tests/fpl_tests/test_chart_generator.py`
- [`statistics.py`](statistics.py) → `tests/fpl_tests/test_statistics.py`
- [`league_context.py`](league_context.py) → `tests/fpl_tests/test_league_context.py`

**Critical**: Tests must be placed in the file corresponding to the module they test. Do NOT place tests for `statistics.py` in `test_chart_generator.py`, even if the chart generator uses statistics functions. Each module's tests should be isolated in its own test file.

**When writing new tests**:
1. Create a new test file if one doesn't exist for the module
2. Place tests in the corresponding test file based on which module's code is being tested
3. Integration tests that test multiple modules together should be clearly named (e.g., `test_integration_<feature>.py`)

### Type Hints
- Add type hints to all function signatures in production code
- Plotly types can be complex - use `# type: ignore` when necessary for dynamic attributes
- Test files: type hints recommended but optional

## Known Issues

### Plotly Deprecation Warning (Informational Only)

When running tests that use chart generation (SVG/PNG export), you may see this deprecation warning:

```
DeprecationWarning: Support for the 'engine' argument is deprecated and will be removed after September 2025.
```

**Root Cause**: This warning originates from plotly's internal code (v6.5.2+), not our code.
- `plotly.io.write_image()` has `engine="auto"` as a default parameter
- When it calls `to_image()`, it triggers the deprecation warning
- This is a bug in plotly - they deprecated the parameter but still use a non-None default

**Our Code Status**: ✅ Already compliant with plotly's migration guide
- We don't pass the `engine` parameter anywhere in [`chart_generator.py`](chart_generator.py)
- Calls are: `fig.to_image(format="svg")` and `fig.write_image(output_path, format="png")`

**Impact**: Informational only - doesn't affect functionality. Will be resolved when plotly removes the parameter after September 2025.

**Action**: Do not suppress this warning. It's harmless and will disappear in a future plotly release.

