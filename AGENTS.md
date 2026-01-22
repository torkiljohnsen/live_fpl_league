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

## Code Quality & Linting

This project uses **ruff** for fast Python linting and code formatting. Configuration is in [`pyproject.toml`](pyproject.toml).

### Running Ruff

**Before writing code**, check existing code style:
```bash
# Check specific file
python -m ruff check fpl/chart_generator.py

# Check entire directory
python -m ruff check fpl/

# Check all Python files
python -m ruff check .
```

**Auto-fix issues** where possible:
```bash
# Fix specific file
python -m ruff check --fix tests/fpl_tests/test_chart_generator.py

# Fix all files
python -m ruff check --fix .
```

### Before Committing

**ALWAYS run the FULL test suite before making a git commit**:
```bash
# 1. Run ruff and auto-fix
python -m ruff check --fix .

# 2. Run ALL tests to ensure nothing broke (not just tests for current feature)
python -m pytest

# 3. If ANY test fails, fix it before committing
# Your changes may have introduced regressions in other parts of the codebase

# 4. Only commit when all tests pass
git add -A && git commit -m "Your message"
```

**Critical**: Even if you only modified one module, run the entire test suite. Changes can have unexpected side effects on other components.

### Common Ruff Rules
- **Import sorting** (I): Imports must be sorted alphabetically and grouped
- **Unused imports** (F401): Remove imports that aren't used
- **Whitespace** (W293): No trailing whitespace on blank lines
- **Dict literals** (C408): Use `{'key': value}` instead of `dict(key=value)`
- **Naming** (N): Follow PEP 8 naming conventions
- **Pyflakes** (F): Detect common Python errors

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
- We don't pass the `engine` parameter anywhere in [`fpl/chart_generator.py`](fpl/chart_generator.py)
- Calls are: `fig.to_image(format="svg")` and `fig.write_image(output_path, format="png")`

**Impact**: Informational only - doesn't affect functionality. Will be resolved when plotly removes the parameter after September 2025.

**Action**: Do not suppress this warning. It's harmless and will disappear in a future plotly release.

## Agent Operational Guidelines

### Running Tests
The virtual environment **stays active** once activated in a terminal session. Check if it's active with `which python` (should show `venv/Scripts/python`).

If not active, activate it once:
```bash
source venv/Scripts/activate
```

Then run tests:
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/fpl_tests/test_chart_generator.py

# Run specific test
python -m pytest tests/fpl_tests/test_chart_generator.py::test_empty_chart_has_proper_axes -v
```

**Why `python -m pytest` instead of `pytest`?** The Windows bash terminal doesn't have execute permissions on the pytest script directly.

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

### Refactoring Best Practices

**Test Coverage First**: Before refactoring any code, ensure comprehensive test coverage exists to validate that functionality remains unchanged after refactoring.

**Pre-Refactor Steps**:
1. Check current test coverage: `python -m pytest --cov=fpl --cov-report=term-missing`
2. Write tests for uncovered code paths (aim for >90% coverage on modules being refactored)
3. Verify all tests pass: `python -m pytest`
4. Commit the improved test coverage before starting refactor

**During Refactoring**:
- Make small, incremental changes
- Run tests after each logical change
- Commit working states frequently
- If tests fail, fix immediately before proceeding

**Post-Refactor Validation**:
- All existing tests still pass
- Test coverage has not decreased
- Linting passes: `python -m ruff check --fix .`
- Code is more maintainable/readable than before
