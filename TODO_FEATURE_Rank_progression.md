# TODO: Implement Rank Progression Charts

## Objective
Generate a **single league-wide rank progression chart** showing all participants' `overall_rank` progression across gameweeks as multiple lines on one chart. Each line represents one team in the league (X teams = X lines).

The chart must work on old TV display systems that cannot handle JavaScript or complex fonts, so it will be rendered as a static SVG/PNG image.

## Requirements

### 1. Dependencies
Add to [`requirements.txt`](requirements.txt):
```
plotly>=5.0.0
kaleido>=0.2.0
```
- **Plotly**: Chart generation library
- **Kaleido**: Static image export engine (no browser required)

### 2. Data Source
Each participant's history is in `participant['history']` array (from [`FPLLeague.get_summary()`](fpl/fpl_league.py))
- **X-axis**: `event` field (gameweek number)
- **Y-axis**: `overall_rank` field (must be inverted - lower rank = better position)

### 3. Chart Specifications

#### Chart Type
- **Type**: Line chart with multiple lines (`mode='lines+markers'`)
- **Lines**: One line per participant/team in the league
- **Format**: SVG (preferred) or PNG (static image)

#### Axes
- **X-axis**: Gameweek number (`event`)
- **Y-axis**: Overall rank (reversed scale - rank 1 at top, higher ranks at bottom)

#### Visual Configuration
- **Size**: Configurable (default: 1200×600 pixels for TV display)
- **Background color**: Configurable
- **Line colors**: Two theme options:
  - **Light theme**: Dark lines on light background
  - **Dark theme**: Light lines on dark background

#### Legend
- **Display**: Show first name of each player
- **Position**: Right side or top (configurable)

### 4. Template Integration
- Chart should be rendered in [`templates/ranking_progression.html`](templates/ranking_progression.html)
- Chart should be embedded as inline SVG or as `<img>` tag pointing to generated static file

## Implementation Steps

**Agent instructions**: 
- Keep chat/text output (responses to me) at a minimum, to conserve token usage. No need to consider personal feelings, this is strictly business.
- Write consise and succinct code. Respect Zen of Python.
- All new code written should pass RUFF tests.

**Job iteration instructions**
- Start at the first job with `status: todo`. 
- Activate the virtual environment before you begin.
- Complete ONLY that job, then stop. Stay within the job description. The next agent will handle the next job.
- Look at commit history in the current branch if you are unsure of what has been done in previous jobs.
- If making visual changes, verify them by looking at them in a browser.
- As you complete acceptance criterias, check their checkboxes
- After you finish a job:
  - verify that all acceptance criteria have been met, and if so, change the status for the job to done and 
  - if all acceptance criteria haven't been met, continue working, revise your plan if needed
- **Before committing**: ALWAYS run the FULL test suite and fix any failures:
  1. Run ruff linting: `python -m ruff check --fix .`
  2. Run ALL tests: `python -m pytest` (not just tests for current job)
  3. If any test fails, fix the issue before committing
  4. Only commit when all tests pass
- Make a git commit of your work.

**TDD Methodology**: For each job with code changes, follow Test-Driven Development:
1. Write a failing test first
2. Write minimal code to make the test pass
3. Run the FULL test suite (`python -m pytest`) to ensure your changes don't break existing tests
4. Ensure all tests pass before marking job as done, unless the job requires you to make a failing test.

---

### Job 1: Add chart dependencies to requirements
**Status**: done

**Task**: Add plotly and kaleido to requirements.txt

**Acceptance Criteria**:
- [x] `plotly>=5.0.0` added to requirements.txt
- [x] `kaleido>=0.2.0` added to requirements.txt

---

### Job 2: Write test for empty chart generator
**Status**: done

**Task**: Write a test that expects a chart generator function to create an empty Plotly figure with proper axis setup. The test should FAIL initially.

**Acceptance Criteria**:
- [x] Test file created (e.g., `tests/fpl_tests/test_chart_generator.py`)
- [x] Test imports chart generator module (import will fail - that's expected)
- [x] Test calls function with empty participants list
- [x] Test asserts Y-axis is inverted (reversed=True)
- [x] Test asserts X-axis label is "Gameweek"
- [x] Test asserts Y-axis label is "Overall Rank"
- [x] Test asserts function returns a Plotly figure object
- [x] Running test produces FAILURE (function doesn't exist yet)

---

### Job 3: Implement basic chart generator to pass empty chart test
**Status**: done

**Task**: Create `fpl/chart_generator.py` with minimal implementation to make Job 2 test pass.

**Acceptance Criteria**:
- [x] File `fpl/chart_generator.py` exists
- [x] Function accepts empty participants list parameter
- [x] Returns valid Plotly figure object with configured axes
- [x] Y-axis is inverted (reversed=True)
- [x] X-axis labeled "Gameweek"
- [x] Y-axis labeled "Overall Rank"
- [x] Test from Job 2 now PASSES

---

### Job 4: Write test for single participant line
**Status**: done

**Task**: Write a failing test that expects chart to plot one participant's rank progression.

**Acceptance Criteria**:
- [x] Test creates mock participant dict with `history` array containing `event` and `overall_rank` data
- [x] Test calls chart generator with one-participant list
- [x] Test asserts returned figure has exactly one trace (line)
- [x] Test asserts trace contains correct data points
- [x] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 5: Implement single participant line to pass test
**Status**: done

**Task**: Extend chart generator to plot one participant's rank progression, making Job 4 test pass.

**Acceptance Criteria**:
- [x] Function accepts list with one participant dict containing `history` array
- [x] Extracts `event` and `overall_rank` from history
- [x] Adds one line trace to the figure
- [x] Test from Job 4 now PASSES

---

### Job 6: Write test for multiple participant lines
**Status**: done

**Task**: Write failing tests for plotting multiple participants on same chart.

**Acceptance Criteria**:
- [x] Test with 3 participants expects 3 traces in figure
- [x] Test with 10 participants expects 10 traces in figure
- [x] Tests assert each trace has correct participant data
- [x] Running tests produces FAILURES (functionality doesn't exist yet)

---

### Job 7: Implement multiple participant lines to pass test
**Status**: done

**Task**: Extend chart generator to plot multiple participants, making Job 6 tests pass.

**Acceptance Criteria**:
- [x] Function accepts list with multiple participants
- [x] Each participant gets their own line trace on the chart
- [x] Tests from Job 6 now PASS

---

### Job 8: Write test for light theme colors
**Status**: done

**Task**: Write a failing test that expects light theme color configuration.

**Acceptance Criteria**:
- [x] Test calls function with `theme="light"` parameter
- [x] Test asserts background is light colored (white or near-white)
- [x] Test asserts line colors are dark/visible
- [x] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 9: Implement light theme colors to pass test
**Status**: done

**Task**: Add color configuration for light theme, making Job 8 test pass.

**Acceptance Criteria**:
- [x] Function accepts `theme="light"` parameter (can be default)
- [x] Light theme uses light background color
- [x] Light theme uses dark/visible line colors
- [x] Test from Job 8 now PASSES

---

### Job 10: Write test for dark theme colors
**Status**: done

**Task**: Write a failing test that expects dark theme color configuration.

**Acceptance Criteria**:
- [x] Test calls function with `theme="dark"` parameter
- [x] Test asserts background is dark colored
- [x] Test asserts line colors are light/bright for visibility
- [x] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 11: Implement dark theme colors to pass test
**Status**: done

**Task**: Add dark theme color configuration, making Job 10 test pass.

**Acceptance Criteria**:
- [x] Function accepts `theme="dark"` parameter
- [x] Dark theme uses dark background color
- [x] Dark theme uses light/bright line colors for visibility
- [x] Test from Job 10 now PASSES

---

### Job 12: Write test for custom background color override
**Status**: done

**Task**: Write a failing test that expects custom background color to override theme defaults.

**Acceptance Criteria**:
- [x] Test calls function with `bg_color` parameter (e.g., "#ff0000")
- [x] Test asserts background uses the custom color instead of theme default
- [x] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 13: Implement custom background color override to pass test
**Status**: done

**Task**: Allow custom background color parameter, making Job 12 test pass.

**Acceptance Criteria**:
- [x] Function accepts `bg_color` parameter (optional)
- [x] When provided, `bg_color` overrides theme default background
- [x] Test from Job 12 now PASSES

---

### Job 14: Write test for configurable chart dimensions
**Status**: done

**Task**: Write a failing test that expects width and height parameters to control chart size.

**Acceptance Criteria**:
- [x] Test calls function with `width=800, height=400`
- [x] Test asserts generated chart has those dimensions
- [x] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 15: Implement configurable chart dimensions
**Status**: done

**Task**: Add width and height parameters. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test calls function with `width=800, height=400`
- [x] Test asserts generated chart has those dimensions
- [x] Function accepts `width` parameter (default 1200)
- [x] Function accepts `height` parameter (default 600)
- [x] Generated chart uses specified dimensions
- [x] Test passes

---

### Job 16: Implement legend with participant names
**Status**: done

**Task**: Add legend showing participant first names. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates participants with known first names
- [x] Test asserts each trace has correct name label
- [x] Test asserts legend is visible
- [x] Each line in chart has label with participant's first name
- [x] Legend is visible and readable
- [x] Test passes

---

### Job 17: Implement SVG export
**Status**: done

**Task**: Add ability to export chart as SVG string. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test calls function with `output_format="svg"`
- [x] Test asserts returned value is a string starting with `<svg` tag
- [x] Function accepts `output_format="svg"` parameter
- [x] Function returns valid SVG string (not file path)
- [x] SVG can be embedded in HTML
- [x] Test passes

---

### Job 18: Implement PNG export
**Status**: done

**Task**: Add ability to export chart as PNG file. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test calls function with `format="png"` and output path
- [x] Test asserts PNG file is created and is valid image
- [x] Test cleans up created file
- [x] Function accepts `format="png"` parameter and output path
- [x] PNG file is created at specified location
- [x] Test passes

---

### Job 19: Handle incomplete participant history
**Status**: done

**Task**: Support participants who joined mid-season. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates participant with history starting at GW5 (missing GW 1-4)
- [x] Test asserts chart renders without error
- [x] Test asserts line starts from GW5 with no gaps
- [x] Chart renders without error when participant history is incomplete
- [x] Line starts from first available gameweek for that participant
- [x] Test passes

---

### Job 20: Create ranking progression template
**Status**: done

**Task**: Create `templates/ranking_progression.html` that displays the chart.

**Acceptance Criteria**:
- [x] Template file extends `base.html`
- [x] Template has placeholder for chart embedding (SVG or img)
- [x] Template includes page title "Rank Progression"
- [x] Manual test: Template renders without errors when chart variable is provided

---

### Job 21: Integrate chart into league context
**Status**: done

**Task**: Add chart generation to league context. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates LeagueContext with sample data
- [x] Test asserts context dict includes chart data (SVG string or file path)
- [x] Test asserts chart is generated in dev mode
- [x] `LeagueContext.build()` calls chart generator
- [x] Generated chart is added to context dict
- [x] Works with sample data in dev mode
- [x] Test passes

---

### Job 22: Wire up template rendering in generator script
**Status**: done

**Task**: Update generate_html.py to support ranking_progression output. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test simulates CLI call with `-o ranking_progression`
- [x] Test asserts HTML file is generated in docs/ directory
- [x] Test asserts file contains expected chart content
- [x] CLI accepts `--output ranking_progression` option
- [x] Script renders ranking_progression template when requested
- [x] Generated HTML file saved to docs/ directory
- [x] Test passes

---

### Job 23: Support ALL output option for rank progression
**Status**: done

**Task**: Include ranking_progression in `-o ALL`. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test simulates CLI call with `-o ALL`
- [x] Test asserts ranking_progression HTML is created along with other views
- [x] `-o ALL` generates ranking_progression along with other views
- [x] Test passes

---

### Job 24: Add rank progression to index page
**Status**: done

**Task**: Update generate_index.py to link to rank progression pages. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test generates index with ranking_progression pages present
- [x] Test asserts index HTML includes ranking_progression links
- [x] Test asserts links are correctly formatted
- [x] Index page lists ranking_progression HTML files for each league
- [x] Links are correctly formatted and clickable
- [x] Test passes

---

### Job 25: Ensure X-axis shows only whole gameweek numbers
**Status**: todo

**Task**: Configure X-axis to display only integer gameweek numbers from 1 to latest event. Write test first, then implement.

**Acceptance Criteria**:
- [ ] Test creates chart with gameweeks 1-7
- [ ] Test asserts X-axis tick values are integers [1, 2, 3, 4, 5, 6, 7]
- [ ] Test asserts no decimal values appear on X-axis
- [ ] X-axis displays only whole numbers (no decimals like 3.5)
- [ ] X-axis range goes from 1 to latest gameweek number
- [ ] Test passes

---

### Job 26: Set dark theme as default
**Status**: todo

**Task**: Change default theme from light to dark. Write test first, then implement.

**Acceptance Criteria**:
- [ ] Test calls chart generator without theme parameter
- [ ] Test asserts background is dark colored (default dark theme applied)
- [ ] Test asserts line colors are light/bright
- [ ] Default theme parameter is `theme="dark"`
- [ ] Charts generated without explicit theme use dark theme
- [ ] Test passes

---

### Job 27: Set Y-axis range from 1 to total_players
**Status**: todo

**Task**: Configure Y-axis range based on total_players from bootstrap-static. Write test first, then implement.

**Acceptance Criteria**:
- [ ] Test provides total_players value (e.g., 10000000)
- [ ] Test asserts Y-axis range is [1, total_players]
- [ ] Test asserts Y-axis is reversed (1 at top, total_players at bottom)
- [ ] Function accepts `total_players` parameter from bootstrap-static API
- [ ] Y-axis range is explicitly set from 1 (top) to total_players (bottom)
- [ ] Test passes

---

### Job 28: Add asterisk to unfinished gameweek on X-axis
**Status**: todo

**Task**: Mark unfinished gameweeks with asterisk based on bootstrap-static data. Write test first, then implement.

**Acceptance Criteria**:
- [ ] Test provides gameweek data with event 7 having `finished: false`
- [ ] Test asserts X-axis label for event 7 displays "7*"
- [ ] Test asserts finished events (1-6) display without asterisk
- [ ] Function receives event finish status from bootstrap-static
- [ ] Unfinished gameweeks display with asterisk (e.g., "7*")
- [ ] Finished gameweeks display as plain numbers
- [ ] Test passes

---

## Design Decisions to Make

1. **Chart file location**: Save to `docs/charts/` or embed inline in HTML?
2. **Color palette**: Define default color sets for light/dark themes
3. **Line styling**: Solid lines only, or vary line styles (dashed, dotted) for accessibility?
4. **Marker styling**: Show markers at each gameweek, or lines only?
5. **Tooltip/hover**: Not applicable for static images, but consider adding annotations
6. **Missing data**: How to handle participants who joined mid-season?

## Testing Considerations

- Test with sample data in dev mode
- Verify chart renders correctly with varying numbers of participants (2-20 teams)
- Test both light and dark themes
- Verify SVG rendering on target TV display systems
- Test with participants who have incomplete history data

## Future Enhancements

- Interactive version using Plotly.js for web browsers (optional toggle)
- Highlight specific participants on click/hover
- Zoom controls for large datasets
- Export chart data as CSV
- Comparison mode: Show selected participants only
