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
- [GitHub Actions (Nightly Workflow)](#github-actions-nightly-workflow)
  - [What happens each night](#what-happens-each-night)
  - [Required secrets](#required-secrets)
  - [How it ties together after a gameweek finishes](#how-it-ties-together-after-a-gameweek-finishes)
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

## GitHub Actions (Nightly Workflow)

A nightly GitHub Actions workflow (`.github/workflows/scheduled-build.yml`) runs at 05:00 UTC and ties everything together automatically. It can also be triggered manually via `workflow_dispatch`.

### What happens each night

1. **HTML dashboards** — Generates standings, gameweek history, and ranking progression charts for all configured leagues (currently `1639886` and `1638989`). API responses are cached with `--cache-dir` to avoid redundant calls.
2. **Index page** — Regenerates `docs/index.html` with links to all dashboard pages.
3. **Weekly report & narrative** — Runs `generate_weekly_report.py` with `--narrative --skip-existing` for league `1638989`. This:
   - Builds the JSON report (if it doesn't already exist for this gameweek)
   - Generates a Norwegian narrative via Claude API
   - `--skip-existing` ensures no duplicate work — once a gameweek's report and narrative exist, it's skipped
4. **Hero images** — Copies `reidars_rapport_{1-4}.png` to `docs/assets/` if not already present
5. **Auto-commit** — Commits all changes to `docs/`, `weekly_report/reports/`, and `weekly_report/reidar_memory/` to the `dev` branch

### Required secrets

- `GH_PAT` — GitHub personal access token (for pushing to the repo)
- `ANTHROPIC_API_KEY` — Claude API key (for narrative generation)
- `TEAMS_WEBHOOK_URL` — Power Automate Workflows webhook URL (configured but not active until `--notify-teams` is added to the workflow)

### How it ties together after a gameweek finishes

When the FPL API marks a gameweek as finished, the next nightly run will:
1. Detect the newly finished gameweek automatically
2. Generate fresh dashboard HTML reflecting the latest results
3. Create a new narrative report (Reidar's take on the gameweek)
4. Commit the narrative Markdown file (viewable via the dynamic article page on GitHub Pages)
5. Commit everything — the site updates automatically

Dashboard pages are always regenerated (reflecting live data), while reports and narratives are only generated once per gameweek (`--skip-existing`).

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