# fpl/ Module - Agent Documentation

## Code Organization Principles

**Separation of Concerns**: Keep calculation logic separate from presentation formatting.

- **[`statistics.py`](statistics.py)** - Pure calculations returning raw data structures (dicts with counts, values, lists). No string formatting or language-specific text.
- **[`league_context.py`](league_context.py)** - Presentation layer that formats statistics for templates (Norwegian text, currency symbols, arrow symbols). Bridge between raw data and template-ready strings.

This separation makes code more testable and easier to internationalize.

## Data Model Conventions

### Participant Objects vs Dicts

The [`Participant`](participant.py) dataclass represents a league participant with their history and statistics.

**When to use Participant objects:**
- Internal business logic (rank calculation, statistics, chart generation)
- Passing data between `fpl/` modules
- Template rendering (Jinja2 works seamlessly with both objects and dicts)

**When to use dicts:**
- JSON serialization / API responses (use `FPLLeague.get_summary_as_dicts()`)
- Test fixtures that need dict-serializable format
- External integrations expecting plain dict data

**Key properties:**
- `player_first_name` - Auto-extracted property from `manager_name` (returns first word)
- `league_rank` - Assigned by `FPLLeague.get_summary()` (1-indexed position in sorted standings)
- `to_dict()` - Converts to dict for backward compatibility

**Type-aware modules:**
- [`statistics.py`](statistics.py) - Accepts `Union[Participant, dict]` via `_get_attr()` helper
- [`chart_generator.py`](chart_generator.py) - Accepts `Union[Participant, dict]` via `_get_attr()` helper
- Templates access attributes via Jinja2 dot notation (works for both)

**Pattern:**
```python
# Internal flow uses objects
participants = league.get_summary()["participants"]  # list[Participant]
highest_value = get_highest_team_value(participants)  # Accepts both types

# External API uses dicts (for JSON serialization)
summary_dict = league.get_summary_as_dicts()  # Converts to plain dicts
```

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
- `FPLLeague.get_summary()` returns dict with `list[Participant]` objects (for internal use)
- `FPLLeague.get_summary_as_dicts()` returns dict with `list[dict]` (for JSON serialization)

**[`participant.py`](participant.py)** - Dataclass representing a participant
- Properties: `player_first_name` (extracted from `manager_name`), `league_rank`
- Fields: `entry_id`, `team_name`, `manager_name`, `total_score`, `history`, `last_event`, `lowest_rank_count`, `win_count`, `golden_win_count`

**[`rank_calculator.py`](rank_calculator.py)** - Calculates round ranks and win/loss statistics
- `apply_history_ranks()` - Calculates `round_rank`, `league_rank`, and `league_rank_change`
- `calculate_lowest_rank_counts()` - Counts gameweeks with minimum points
- `calculate_win_counts()` - Counts gameweek wins and golden gameweek wins

**[`statistics.py`](statistics.py)** - Statistical calculations
- Type-aware: accepts `Union[Participant, dict]` via `_get_attr()` helper
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
- Type-aware: accepts `Union[Participant, dict]` via `_get_attr()` helper
- `generate_rank_progression_chart()` - Creates rank progression visualization

**[`chip_annotator.py`](chip_annotator.py)** - Chip usage annotations

### Weekly Report Pipeline
**[`player_registry.py`](player_registry.py)** - Maps FPL element IDs to human-readable names
- `PlayerRegistry(bootstrap_data)` builds lookup dicts from bootstrap `elements[]`, `teams[]`, `element_types[]`
- `get_player_name(element_id)` returns "FirstName LastName" (or "Unknown Player")
- `get_player_info(element_id)` returns dict with name, team, position
- `get_team_name(team_code)` returns team name (or "Unknown Team")
- Pure data transformation — no API calls

**[`weekly_report.py`](weekly_report.py)** - Assembles gameweek data into a structured report
- `WeeklyReport(api, league_id, event_id)` — constructor takes API client, league ID, and gameweek number
- `build()` fetches all data, assembles participant dicts, calculates awards, returns complete report dict with `meta`, `standings`, `awards`, `league_summary`
- `save_report(output_dir)` writes JSON to `reports/{league_id}/{season}/gw{N}.json`
- Uses PlayerRegistry for name resolution, weekly_report_stats for awards

**[`weekly_report_stats.py`](weekly_report_stats.py)** - Pure award calculation functions
- All functions: `list[dict]` in, `dict`/`list`/`None` out — no side effects
- Functions: `get_highest_gameweek_scorer`, `get_lowest_gameweek_scorer`, `get_biggest_rank_rise`, `get_biggest_rank_fall`, `get_bench_disasters`, `get_transfer_impact`, `get_captain_summary`, `get_chip_usage`, `get_hit_takers`
- Follows same pure-function pattern as [`statistics.py`](statistics.py)

**[`narrative_generator.py`](narrative_generator.py)** - Claude API narrative generation
- `NarrativeGenerator(client=None)` — accepts optional anthropic client; creates from `ANTHROPIC_API_KEY` env var if not provided
- `generate(report_json, persona, narrative_guide, examples, memory_context, previous_narrative=None)` — builds system prompt from reference docs + memory, sends report as user message, returns Norwegian narrative markdown
- `save_narrative(content, output_dir, league_id, season, event_id)` writes to `narratives/{league_id}/{season}/gw{N}.md`
- Uses `claude-sonnet-4-6` model

**[`reidar_memory.py`](reidar_memory.py)** - Persistent memory system for Reidar persona
- `ReidarMemory(output_dir, league_id, season)` — manages files under `reidar_memory/{league_id}/{season}/`
- `scaffold_directories()` creates `managers/` and `gameweeks/` subdirs
- `load_manager_profiles()` returns `dict[str, str]` keyed by manager name
- `load_season_arc()` returns season arc markdown (empty string if missing)
- `load_recent_gameweeks(current_event, window=5)` returns last N GW summaries
- `get_prompt_context(current_event)` assembles all memory into formatted prompt string (~4k words)
- `update_memory(report_json, narrative, client)` makes a Claude API call to update all memory files after each narrative

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

