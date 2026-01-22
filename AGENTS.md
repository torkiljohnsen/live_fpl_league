# AGENTS.md - Live FPL League Dashboard

Generates static HTML dashboards for Fantasy Premier League mini-leagues showing live standings and gameweek history.

## Knowledge collection

When you learn something new about this repo that is of use to users or agents, add it to README.md or AGENTS.md, respectively. You can also place AGENTS.md-files in subfolders if you think there is a need for this.

Add new knowledge sparingly, and do so in a consise way.

## Module Documentation

- **[`fpl/AGENTS.md`](fpl/AGENTS.md)** - Detailed documentation for the `fpl/` module (data collection, processing, context building)
- **[`templates/AGENTS.md`](templates/AGENTS.md)** - Template variables and structure reference
- **[`docs/CHART_THEMES.md`](docs/CHART_THEMES.md)** - Chart theme customization guide (dark, light, Sinkaberg corporate)

## Architecture Flow

**Data Collection → Context Building → Template Rendering → Static HTML Output**

See [`fpl/AGENTS.md`](fpl/AGENTS.md) for detailed module documentation.

### Overview

1. **Data Collection** - [`fpl/fpl_api.py`](fpl/fpl_api.py) fetches from FPL API (or dev mode samples)
2. **Data Processing** - [`fpl/fpl_league.py`](fpl/fpl_league.py) aggregates data; [`fpl/statistics.py`](fpl/statistics.py) calculates stats
3. **Context Building** - [`fpl/league_context.py`](fpl/league_context.py) formats data for templates
4. **Template Rendering** - [`fpl/league_template_renderer.py`](fpl/league_template_renderer.py) generates HTML
5. **Entry Points** - [`generate_html.py`](generate_html.py) and [`generate_index.py`](generate_index.py)

## Directory Structure

- **[`fpl/`](fpl/)** - Core Python package for data fetching and processing. See [`fpl/AGENTS.md`](fpl/AGENTS.md) for detailed module documentation.

- **[`templates/`](templates/)** - Jinja2 HTML templates
  - [`league_standings.html`](templates/league_standings.html) - Current standings table
  - [`league_gameweek_history.html`](templates/league_gameweek_history.html) - Historical performance grid
  - [`base.html`](templates/base.html) - Base template with shared structure
  - [`index.html`](templates/index.html) - Index page template
  - [`AGENTS.md`](templates/AGENTS.md) - Template variables reference

- **[`docs/`](docs/)** - Generated static HTML output (GitHub Pages ready)
  - Generated HTML files for each league/view
  - [`style.css`](docs/style.css) - Shared stylesheet

- **[`tests/`](tests/)** - Test suite
  - [`fpl_tests/`](tests/fpl_tests/) - Tests for `fpl/` modules
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

Tests in [`tests/fpl_tests/`](tests/fpl_tests/) use `DummyAPI` with sample data from [`tests/fpl_tests/data_samples/`](tests/fpl_tests/data_samples/)`

Test organization guidelines in [`fpl/AGENTS.md`](fpl/AGENTS.md)

## Code Quality & Linting

This project uses **ruff** for fast Python linting and code formatting. Configuration is in [`pyproject.toml`](pyproject.toml).

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

### Before Marking Task as DONE and Committing

**ALWAYS follow this workflow before marking a task as DONE**:
```bash
# 1. FIRST: Run ruff on changed Python files to ensure code quality
# If you changed: fpl/statistics.py and tests/fpl_tests/test_statistics.py
python -m ruff check --fix fpl/statistics.py tests/fpl_tests/test_statistics.py

# OR run on all Python files (ruff will ignore non-Python files)
python -m ruff check --fix .

# 2. SECOND: Run ALL tests to ensure nothing broke (not just tests for current feature)
python -m pytest

# 3. If ANY test fails, fix it before proceeding
# Your changes may have introduced regressions in other parts of the codebase
# Repeat steps 1-2 until all tests pass

# 4. Mark the task status as DONE in the TODO file

# 5. Only commit when all tests pass and task is marked DONE
git add -A && git commit -m "Your message"
```

**Critical Workflow Order**: 
1. **Ruff BEFORE tests** - All code must be properly formatted before running tests
2. **All tests MUST pass** - Fix any failures before proceeding
3. **Mark task DONE** - Only after all tests pass
4. **Git commit** - Final step after everything is verified
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
