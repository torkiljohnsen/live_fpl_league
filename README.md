# live_fpl_league
A static HTML dashboard generator for Fantasy Premier League mini-leagues, showing live standings, gameweek history, and rank progression.

See [Live standings](https://torkiljohnsen.github.io/live_fpl_league/)

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

# Dev mode with sample data
python generate_weekly_report.py --dev
```

### Output

All weekly report artifacts are stored under `weekly_report/`:

- `weekly_report/reports/{league_id}/{season}/gw{N}.json` — Structured gameweek data
- `weekly_report/narratives/{league_id}/{season}/gw{N}.md` — Generated narratives
- `weekly_report/reidar_memory/{league_id}/{season}/` — Persistent memory (manager profiles, season arc, GW summaries)

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