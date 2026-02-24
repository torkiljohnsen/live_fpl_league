# AGENTS.md - Live FPL League Dashboard

Generates static HTML dashboards for Fantasy Premier League mini-leagues showing live standings and gameweek history.

## Knowledge collection

When you learn something new about this repo that is of use to users or agents, add it to README.md or AGENTS.md, respectively. You can also place AGENTS.md-files in subfolders if you think there is a need for this.

Add new knowledge sparingly, and do so in a consise way.

## Module Documentation

- **[`fpl/AGENTS.md`](fpl/AGENTS.md)** - Detailed documentation for the `fpl/` module (data collection, processing, context building)
- **[`templates/AGENTS.md`](templates/AGENTS.md)** - Template variables and structure reference
- **[`docs/CHART_THEMES.md`](docs/CHART_THEMES.md)** - Chart theme customization guide (dark, light, Sinkaberg corporate)
- **[`weekly_report/`](weekly_report/)** - Reidar persona, narrative guide, and example narratives for weekly report generation

## Architecture Flow

**Data Collection → Context Building → Template Rendering → Static HTML Output**

See [`fpl/AGENTS.md`](fpl/AGENTS.md) for detailed module documentation.

### HTML Dashboard Flow

1. **Data Collection** - [`fpl/fpl_api.py`](fpl/fpl_api.py) fetches from FPL API (or dev mode samples)
2. **Data Processing** - [`fpl/fpl_league.py`](fpl/fpl_league.py) aggregates data; [`fpl/statistics.py`](fpl/statistics.py) calculates stats
3. **Context Building** - [`fpl/league_context.py`](fpl/league_context.py) formats data for templates
4. **Template Rendering** - [`fpl/league_template_renderer.py`](fpl/league_template_renderer.py) generates HTML
5. **Entry Points** - [`generate_html.py`](generate_html.py) and [`generate_index.py`](generate_index.py)

### Weekly Report & Narrative Flow (Reidar's Rapport)

**Data Collection → Report Assembly → Narrative Generation → Memory Update**

1. **Data Collection** - [`fpl/fpl_api.py`](fpl/fpl_api.py) fetches standings, picks, transfers, and live event data
2. **Player Resolution** - [`fpl/player_registry.py`](fpl/player_registry.py) maps element IDs to player/team names
3. **Participant Building** - [`fpl/weekly_report.py`](fpl/weekly_report.py) assembles per-participant gameweek data (points, captain, bench, transfers, rank changes)
4. **Awards Calculation** - [`fpl/weekly_report_stats.py`](fpl/weekly_report_stats.py) computes awards (top scorer, bench disasters, captain picks, etc.)
5. **Report Assembly** - `WeeklyReport.build()` produces a self-contained JSON report with meta, standings, awards, league_summary
6. **Narrative Generation** - [`fpl/narrative_generator.py`](fpl/narrative_generator.py) sends report + Reidar persona + memory context to Claude API, returns Norwegian-language narrative
7. **Memory Update** - [`fpl/reidar_memory.py`](fpl/reidar_memory.py) updates per-manager profiles, season arc, and GW summaries after each narrative
8. **Entry Point** - [`generate_weekly_report.py`](generate_weekly_report.py) (`--dev` for sample data, `--narrative` for Claude API narrative)

**Reidar Memory System**: Persistent context across gameweeks stored in `weekly_report/reidar_memory/{league_id}/{season}/`. Includes per-manager profiles (~200 words), season arc, and rolling GW summaries. Assembled into prompt context via `ReidarMemory.get_prompt_context()` (~4k words at any point in the season).

**GitHub Actions**: `.github/workflows/scheduled-build.yml` runs nightly, generates HTML dashboards and weekly report + narrative (with `--skip-existing` to avoid duplicates), and auto-commits.

## Directory Structure

- **[`fpl/`](fpl/)** - Core Python package for data fetching and processing. See [`fpl/AGENTS.md`](fpl/AGENTS.md) for detailed module documentation.

- **[`templates/`](templates/)** - Jinja2 HTML templates
  - [`league_standings.html`](templates/league_standings.html) - Current standings table
  - [`league_gameweek_history.html`](templates/league_gameweek_history.html) - Historical performance grid
  - [`base.html`](templates/base.html) - Base template with shared structure
  - [`index.html`](templates/index.html) - Index page template
  - [`AGENTS.md`](templates/AGENTS.md) - Template variables reference

- **[`docs/`](docs/)** - GitHub Pages publishing directory (static HTML output only)
  - Generated HTML files for each league/view
  - [`style.css`](docs/style.css) - Shared stylesheet
  - **Do not place non-publishing files here** — this folder is deployed to GitHub Pages

- **[`weekly_report/`](weekly_report/)** - Everything related to weekly narrative generation (Reidar's Rapport)
  - [`REIDAR_PERSONA.md`](weekly_report/REIDAR_PERSONA.md) - Reidar character definition (voice, personality)
  - [`NARRATIVE_GUIDE.md`](weekly_report/NARRATIVE_GUIDE.md) - Narrative structure and content rules
  - [`REIDAR_EXAMPLES.md`](weekly_report/REIDAR_EXAMPLES.md) - Few-shot example narratives for LLM prompting
  - `reports/{league_id}/{season}/gw{N}.json` - Generated JSON weekly reports. Gitignored for local dev; committed by GitHub Actions.
  - `narratives/{league_id}/{season}/gw{N}.md` - Generated Norwegian narratives. Committed by GitHub Actions.
  - `reidar_memory/{league_id}/{season}/` - Reidar's persistent memory files (manager profiles, season arc, GW summaries). Committed by GitHub Actions.

- **[`prd/`](prd/)** - Product requirement documents (Ralph agent loop task definitions)

- **[`assets/`](assets/)** - Source images and SVGs (logos, icons) used by templates

- **[`tests/`](tests/)** - Test suite
  - [`fpl_tests/`](tests/fpl_tests/) - Tests for `fpl/` modules
  - [`fpl_tests/data_samples/`](tests/fpl_tests/data_samples/) - Test fixtures

- **Root files**
  - [`generate_html.py`](generate_html.py) - Main HTML generation script
  - [`generate_index.py`](generate_index.py) - Index page generator
  - [`generate_weekly_report.py`](generate_weekly_report.py) - Weekly report generation (JSON + narrative)
  - [`requirements.txt`](requirements.txt) - Python dependencies

## Key Conventions
- **Dev mode suffix**: Files end with `-dev.html` when using sample data
- **Golden gameweeks**: Every 4th gameweek (4, 8, 12...) marked with `golden_gameweek` CSS class
- **Template variables**: See [`templates/AGENTS.md`](templates/AGENTS.md) for full variable reference
- **CSS**: All styles in [`docs/style.css`](docs/style.css), no inline styles
- **Participant objects vs dicts**: See "Data Model Conventions" below for when to use objects vs dicts

## Data Model Conventions

### Participant Class
The [`Participant`](fpl/participant.py) class is a dataclass representing a league participant with their history and statistics.

**When to use Participant objects:**
- Internal business logic (rank calculation, statistics, chart generation)
- Passing data between `fpl/` modules
- Template rendering (Jinja2 works seamlessly with both objects and dicts)

**When to use dicts:**
- JSON serialization / API responses (`FPLLeague.get_summary_as_dicts()`)
- External integrations expecting plain dict data
- Test fixtures that need dict-serializable format

**Key properties:**
- `player_first_name` - Auto-extracts first name from `manager_name`
- `league_rank` - Assigned by `FPLLeague.get_summary()` (1-indexed position)
- `to_dict()` - Converts to dict for backward compatibility

**Type-aware modules:**
- [`statistics.py`](fpl/statistics.py) - Accepts `Union[Participant, dict]` via `_get_attr()` helper
- [`chart_generator.py`](fpl/chart_generator.py) - Accepts `Union[Participant, dict]` via `_get_attr()` helper
- Templates access attributes via Jinja2 dot notation (works for both)

**Pattern:**
```python
# Internal flow uses objects
participants = league.get_summary()["participants"]  # list[Participant]
highest_value = get_highest_team_value(participants)  # Accepts both types

# External API uses dicts
summary_dict = league.get_summary_as_dicts()  # Converts to plain dicts
```

## Testing

Tests in [`tests/fpl_tests/`](tests/fpl_tests/) use `DummyAPI` with sample data from [`tests/fpl_tests/data_samples/`](tests/fpl_tests/data_samples/)`

Test organization guidelines in [`fpl/AGENTS.md`](fpl/AGENTS.md)

## Code Quality & Linting

This project uses **ruff** for fast Python linting and code formatting, and **mypy** for static type checking. Configuration is in [`pyproject.toml`](pyproject.toml).

### Running Ruff

**Important**: Ruff should ONLY be run on Python (.py) files. Never run it on markdown, JSON, or other file types.

**Before writing code**, check existing code style:
```bash
# Check specific Python file
python -m ruff check fpl/chart_generator.py

# Check all Python files in a directory
python -m ruff check fpl/

# Check all Python files in project (safe - ruff ignores non-Python files)
python -m ruff check .
```

**Auto-fix issues** where possible:
```bash
# Fix specific Python file
python -m ruff check --fix tests/fpl_tests/test_chart_generator.py

# Fix all Python files in project
python -m ruff check --fix .
```

### Running Mypy

Mypy performs static type checking to catch type-related errors before runtime:

```bash
# Check the fpl/ package (main codebase)
python -m mypy fpl/ --ignore-missing-imports

# Check specific file
python -m mypy fpl/chart_generator.py --ignore-missing-imports
```

Mypy analyzes type hints in the code and reports type mismatches, missing return types, and other type-related issues.

### Before Marking Task as DONE and Committing

**ALWAYS follow this workflow before marking a task as DONE**:
```bash
# 1. FIRST: Run ruff on changed Python files to ensure code quality
# If you changed: fpl/statistics.py and tests/fpl_tests/test_statistics.py
python -m ruff check --fix fpl/statistics.py tests/fpl_tests/test_statistics.py

# OR run on all Python files (ruff will ignore non-Python files)
python -m ruff check --fix .

# 2. SECOND: Run mypy type checking on the fpl/ package
python -m mypy fpl/ --ignore-missing-imports

# 3. THIRD: Run ALL tests to ensure nothing broke (not just tests for current feature)
python -m pytest

# 4. If ANY test fails, fix it before proceeding
# Your changes may have introduced regressions in other parts of the codebase
# Repeat steps 1-3 until all tests pass

# 5. Mark the task status as DONE in the TODO file

# 6. Only commit when all checks pass and task is marked DONE
git add -A && git commit -m "Your message"
```

**Critical Workflow Order**: 
1. **Ruff BEFORE tests** - All code must be properly formatted before running tests
2. **Mypy type checking** - Catch type errors before running tests
3. **All tests MUST pass** - Fix any failures before proceeding
4. **Mark task DONE** - Only after all checks pass
5. **Git commit** - Final step after everything is verified
- Even if you only modified one module, run the entire test suite. Changes can have unexpected side effects on other components.
- Ruff automatically ignores non-Python files, but for clarity specify only .py files when listing individual files.

### Common Ruff Rules
- **Import sorting** (I): Imports must be sorted alphabetically and grouped
- **Unused imports** (F401): Remove imports that aren't used
- **Whitespace** (W293): No trailing whitespace on blank lines
- **Dict literals** (C408): Use `{'key': value}` instead of `dict(key=value)`
- **Naming** (N): Follow PEP 8 naming conventions
- **Pyflakes** (F): Detect common Python errors

## Agent Operational Guidelines

### Virtual Environment Activation
**ALWAYS activate the virtual environment at the start of each new session** before running any Python commands:

```bash
source venv/Scripts/activate
```

Verify activation with `which python` (should show `venv/Scripts/python`, not `/c/Python313/python`).

The virtual environment **stays active** within a terminal session but must be re-activated when starting a new terminal or session.

### Running Tests
Once the virtual environment is active, check with `which python` (should show `venv/Scripts/python`).

Run tests:
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

### Test-Driven Development (TDD) Workflow

**CRITICAL**: For bugs and features, write the failing test FIRST, then fix/implement:

#### Bug Fixes
1. Write a failing test that reproduces the bug
2. Run test to confirm it fails: `python -m pytest tests/fpl_tests/test_<module>.py::test_<name> -v`
3. Fix the bug with minimal code changes
4. Run test to confirm it passes
5. Run all tests: `python -m pytest`
6. Commit both test and fix together

**Example**: For "CLI processes both default and specified league" bug:
- First: Write `test_specified_league_overrides_default()` that verifies only specified league is processed (fails)
- Then: Fix argparse handling in `generate_html.py` (test passes)
- Finally: Commit test + fix together

#### New Features
Same workflow: failing test → minimal code → test passes → refactor if needed → commit

**Why TDD?** Ensures test coverage, catches regressions, makes refactoring safe.

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
