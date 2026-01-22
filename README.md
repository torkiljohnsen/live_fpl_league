# live_fpl_league
A streamlit dashboard to show the live standings of your FPL mini league

See [Live standings](https://torkiljohnsen.github.io/live_fpl_league/)

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