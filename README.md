# live_fpl_league
A static HTML dashboard generator for Fantasy Premier League mini-leagues, showing live standings, gameweek history, and rank progression.

See [Live standings](https://torkiljohnsen.github.io/live_fpl_league/)

## Table of Contents

- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Command-Line Options](#command-line-options)
  - [Output Files](#output-files)
- [Weekly Report (Reidar's Rapport)](#weekly-report-reidars-rapport)
  - [Setup](#setup)
  - [Usage](#usage-1)
  - [Output](#output)
- [GitHub Actions (Hourly Workflow)](#github-actions-hourly-workflow)
  - [How it works](#how-it-works)
  - [Required secrets](#required-secrets)
  - [Failure recovery](#failure-recovery)
- [Development Setup](#development-setup)
  - [Environment Setup](#environment-setup)
  - [Running Tests](#running-tests)
  - [Development Mode and Sample Data](#development-mode-and-sample-data)

## Usage

### Quick Start

Generate all dashboard views for the default league:
```bash
python generate_html.py
```

Generate for a specific league:
```bash
python generate_html.py -l 1638989
```

### Command-Line Options

View all available options:
```bash
python generate_html.py --help
```

**Basic options:**
- `-l, --league_id` - FPL league ID(s). Can be comma-separated or repeated. Default: 1639886
- `-o, --output` - Which view to generate: `standings`, `gw_history`, `ranking_progression`, or `ALL` (default)
- `-j, --join_code` - Optional league join code to display
- `--dev` - Use sample data instead of live FPL API (outputs have `-dev.html` suffix)

**Examples:**
```bash
# Generate all views for default league
python generate_html.py

# Generate all views for specific league
python generate_html.py -l 1638989

# Generate only ranking progression chart
python generate_html.py -o ranking_progression

# Multiple leagues (comma-separated)
python generate_html.py -l 1638989,1639886

# Multiple leagues (repeated flag)
python generate_html.py -l 1638989 -l 1639886

# Use sample data (dev mode)
python generate_html.py --dev
```

### Output Files

Generated HTML files are saved to the `docs/` directory:
- `league_standings_{league_id}.html` - Current league standings table
- `league_gameweek_history_{league_id}.html` - Historical performance grid
- `ranking_progression_{league_id}.html` - Rank progression chart over time

When using `--dev` mode, files are suffixed with `-dev.html` (e.g., `league_standings_1638989-dev.html`)

## Weekly Report (Reidar's Rapport)

The weekly report system generates entertaining Norwegian-language narratives for each FPL gameweek, written in the voice of "Reidar" — a fictional commentator with strong opinions.

### Setup

The narrative generator requires an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

On Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

### Usage

```bash
# Generate report + narrative for a specific gameweek
python generate_weekly_report.py -l 1639886 -e 10 --narrative

# Generate report only (no narrative, no API key needed)
python generate_weekly_report.py -l 1639886 -e 10

# Skip if report already exists (used in CI to avoid duplicates)
python generate_weekly_report.py -l 1639886 --narrative --skip-existing

# Generate narrative with Teams notification
python generate_weekly_report.py -l 1639886 -e 10 --narrative --notify-teams

# Dev mode with sample data
python generate_weekly_report.py --dev
```

The `--narrative` flag writes a Markdown narrative to `docs/narratives/{season}/{league_id}/gw{N}.md`, viewable at `reidars_rapport.html?gw={N}` on GitHub Pages.

The `--notify-teams` flag posts a Teams Adaptive Card with a teaser and link to the article. Requires the `TEAMS_WEBHOOK_URL` environment variable.

### Output

All weekly report artifacts are stored under `weekly_report/`:

- `weekly_report/reports/{league_id}/{season}/gw{N}.json` — Structured gameweek data
- `weekly_report/narratives/{league_id}/{season}/gw{N}.md` — Generated narratives
- `weekly_report/reidar_memory/{league_id}/{season}/` — Persistent memory (manager profiles, season arc, GW summaries)

Narrative Markdown files are written to `docs/narratives/{season}/{league_id}/gw{N}.md`, rendered client-side at `reidars_rapport.html?gw={N}`.

## GitHub Actions (Hourly Workflow)

An hourly GitHub Actions workflow (`.github/workflows/scheduled-build.yml`) checks for FPL changes and runs the appropriate steps. It can also be triggered manually via `workflow_dispatch`.

### How it works

Each hour, `check_gw_status.py` queries the FPL API and compares against a persisted state file (`.gw_state.json`) to detect what has changed since the last successful run. It produces two signals:

**Tier 1 — New fixtures finished** (e.g. a match ended): Refreshes dashboards.
1. **HTML dashboards** — Regenerates standings, gameweek history, and ranking progression for all configured leagues (`1639886`, `1638989`).
2. **Index page** — Regenerates `docs/index.html`.

**Tier 2 — Whole gameweek finished** (FPL marks the event as finished): Generates reports.
1. **Weekly report** — Builds the JSON report for the finished gameweek (`--skip-existing` prevents duplicates).
2. **Narrative** — Generates a Norwegian-language narrative via Claude API.
3. **Teams notification** — Posts an Adaptive Card to the configured Teams webhook.

If nothing has changed, the workflow skips all generation steps to minimize CI usage.

After successful generation, the state file is updated and committed alongside the generated files so the next run can diff against it.

Manual dispatch (`workflow_dispatch`) skips the check and runs everything unconditionally.

### Required secrets

- `GH_PAT` — GitHub personal access token (for pushing to the repo)
- `ANTHROPIC_API_KEY` — Claude API key (for narrative generation)
- `TEAMS_WEBHOOK_URL` — Power Automate Workflows webhook URL (for Teams notifications)

### Failure recovery

The state file (`.gw_state.json`) is only saved after all generation steps succeed. If any step fails mid-pipeline, the state is not updated, and the next hourly run will detect the same changes and retry automatically.

For a full manual re-run, use the **Run workflow** button on GitHub (workflow_dispatch) — this bypasses the check entirely and runs all steps.

## Development Setup

### Environment Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
   - **Windows (Git Bash)**: `source venv/Scripts/activate`
   - **Windows (Command Prompt)**: `venv\Scripts\activate`
   - **Unix/macOS**: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=fpl
```

Run a specific test file:
```bash
pytest tests/fpl_tests/test_chart_generator.py
```

Run a specific test:
```bash
pytest tests/fpl_tests/test_chart_generator.py::test_empty_chart_has_proper_axes
```

### Development Mode and Sample Data

The project supports a development mode that uses cached sample data instead of making live API calls. This is useful for:
- Testing without hitting FPL API rate limits
- Working offline or with consistent test data
- Faster development iteration

#### How It Works

When `--dev` flag is used with `generate_html.py`, the FPL_API class operates in dev mode:

1. **First run**: If sample data doesn't exist, it automatically fetches from the live API and saves it to `fpl/sample_data/`
2. **Subsequent runs**: Uses the cached sample data without making API calls

Sample files follow the naming pattern: `{endpoint}_sample.json`
- `bootstrap-static_sample.json` - Global FPL data (events, chips, teams)
- `leagues-classic_{league_id}_standings_sample.json` - League standings
- `entry_{team_id}_history_sample.json` - Team gameweek history

#### Generating Sample Data

```bash
# First run generates sample data for league 1638989
python generate_html.py -l 1638989 --dev
# Output: [dev_mode] API called and sample generated: fpl/sample_data/leagues-classic_1638989_standings_sample.json

# Subsequent runs use cached data
python generate_html.py -l 1638989 --dev
# Output: [dev_mode] Sample read: fpl/sample_data/leagues-classic_1638989_standings_sample.json
```

#### Refreshing Sample Data

To update sample data with fresh API data, delete the sample files and rerun with `--dev`:

```bash
rm fpl/sample_data/*_sample.json
python generate_html.py -l 1638989 --dev
```