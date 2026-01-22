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