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
- Make a git commit of your work.

**TDD Methodology**: For each job with code changes, follow Test-Driven Development:
1. Write a failing test first
2. Write minimal code to make the test pass
3. Ensure test passes before marking job as done, unless the job requires you to make a failing test.

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
**Status**: todo

**Task**: Add dark theme color configuration, making Job 10 test pass.

**Acceptance Criteria**:
- [ ] Function accepts `theme="dark"` parameter
- [ ] Dark theme uses dark background color
- [ ] Dark theme uses light/bright line colors for visibility
- [ ] Test from Job 10 now PASSES

---

### Job 12: Write test for custom background color override
**Status**: todo

**Task**: Write a failing test that expects custom background color to override theme defaults.

**Acceptance Criteria**:
- [ ] Test calls function with `bg_color` parameter (e.g., "#ff0000")
- [ ] Test asserts background uses the custom color instead of theme default
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 13: Implement custom background color override to pass test
**Status**: todo

**Task**: Allow custom background color parameter, making Job 12 test pass.

**Acceptance Criteria**:
- [ ] Function accepts `bg_color` parameter (optional)
- [ ] When provided, `bg_color` overrides theme default background
- [ ] Test from Job 12 now PASSES

---

### Job 14: Write test for configurable chart dimensions
**Status**: todo

**Task**: Write a failing test that expects width and height parameters to control chart size.

**Acceptance Criteria**:
- [ ] Test calls function with `width=800, height=400`
- [ ] Test asserts generated chart has those dimensions
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 15: Implement configurable chart dimensions to pass test
**Status**: todo

**Task**: Add width and height parameters, making Job 14 test pass.

**Acceptance Criteria**:
- [ ] Function accepts `width` parameter (default 1200)
- [ ] Function accepts `height` parameter (default 600)
- [ ] Generated chart uses specified dimensions
- [ ] Test from Job 14 now PASSES

---

### Job 16: Write test for legend with participant names
**Status**: todo

**Task**: Write a failing test that expects legend to show participant first names.

**Acceptance Criteria**:
- [ ] Test creates participants with known first names
- [ ] Test asserts each trace has correct name label
- [ ] Test asserts legend is visible
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 17: Implement legend with participant names to pass test
**Status**: todo

**Task**: Add legend showing first name for each participant line, making Job 16 test pass.

**Acceptance Criteria**:
- [ ] Each line in chart has label with participant's first name
- [ ] Legend is visible and readable
- [ ] Test from Job 16 now PASSES

---

### Job 18: Write test for SVG export
**Status**: todo

**Task**: Write a failing test that expects chart to export as SVG string.

**Acceptance Criteria**:
- [ ] Test calls function with `format="svg"`
- [ ] Test asserts returned value is a string
- [ ] Test asserts string starts with `<svg` tag
- [ ] Test asserts SVG contains valid XML structure
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 19: Implement SVG export to pass test
**Status**: todo

**Task**: Add ability to export chart as SVG string, making Job 18 test pass.

**Acceptance Criteria**:
- [ ] Function accepts `format="svg"` parameter
- [ ] Function returns SVG string (not file path)
- [ ] SVG is valid and can be embedded in HTML
- [ ] Test from Job 18 now PASSES

---

### Job 20: Write test for PNG export
**Status**: todo

**Task**: Write a failing test that expects chart to export as PNG file.

**Acceptance Criteria**:
- [ ] Test calls function with `format="png"` and output path
- [ ] Test asserts PNG file is created at expected location
- [ ] Test asserts file is valid image (can check file header)
- [ ] Test cleans up created file after assertion
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 21: Implement PNG export to pass test
**Status**: todo

**Task**: Add ability to export chart as PNG file, making Job 20 test pass.

**Acceptance Criteria**:
- [ ] Function accepts `format="png"` parameter
- [ ] Function accepts output path parameter
- [ ] PNG file is created at specified location
- [ ] Test from Job 20 now PASSES

---

### Job 22: Write test for incomplete participant history
**Status**: todo

**Task**: Write a failing test for participants who joined mid-season.

**Acceptance Criteria**:
- [ ] Test creates participant with history starting at GW5 (missing GW 1-4)
- [ ] Test asserts chart renders without error
- [ ] Test asserts line starts from GW5 (not GW1)
- [ ] Test asserts no gaps or breaks in line
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 23: Implement handling for incomplete history to pass test
**Status**: todo

**Task**: Handle participants with incomplete history, making Job 22 test pass.

**Acceptance Criteria**:
- [ ] Chart renders without error when participant history is incomplete
- [ ] Line starts from first available gameweek for that participant
- [ ] No gaps or breaks in line rendering
- [ ] Test from Job 22 now PASSES

---

### Job 24: Create ranking progression template
**Status**: todo

**Task**: Create `templates/ranking_progression.html` that displays the chart.

**Acceptance Criteria**:
- [ ] Template file extends `base.html`
- [ ] Template has placeholder for chart embedding (SVG or img)
- [ ] Template includes page title "Rank Progression"
- [ ] Manual test: Template renders without errors when chart variable is provided

---

### Job 25: Write test for chart integration in league context
**Status**: todo

**Task**: Write a failing test that expects LeagueContext to include chart data.

**Acceptance Criteria**:
- [ ] Test creates LeagueContext with sample data
- [ ] Test asserts context dict includes chart data (SVG string or file path)
- [ ] Test asserts chart is generated in dev mode
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 26: Integrate chart into league context to pass test
**Status**: todo

**Task**: Add chart generation to `fpl/league_context.py`, making Job 25 test pass.

**Acceptance Criteria**:
- [ ] `LeagueContext.build()` calls chart generator
- [ ] Generated chart is added to context dict
- [ ] Works with sample data in dev mode
- [ ] Test from Job 25 now PASSES

---

### Job 27: Write test for generator script supporting ranking_progression
**Status**: todo

**Task**: Write a failing test that expects generate_html.py to support ranking_progression output.

**Acceptance Criteria**:
- [ ] Test simulates CLI call with `-o ranking_progression`
- [ ] Test asserts HTML file is generated in docs/ directory
- [ ] Test asserts file contains expected chart content
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 28: Wire up template rendering in generator script to pass test
**Status**: todo

**Task**: Update `generate_html.py` to support ranking_progression output, making Job 27 test pass.

**Acceptance Criteria**:
- [ ] CLI accepts `--output ranking_progression` option
- [ ] Script renders ranking_progression template when requested
- [ ] Generated HTML file saved to docs/ directory
- [ ] Test from Job 27 now PASSES

---

### Job 29: Write test for ALL output including rank progression
**Status**: todo

**Task**: Write a failing test that expects `-o ALL` to include ranking_progression.

**Acceptance Criteria**:
- [ ] Test simulates CLI call with `-o ALL`
- [ ] Test asserts ranking_progression HTML is created along with other views
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 30: Support ALL output option for rank progression to pass test
**Status**: todo

**Task**: Include ranking_progression when `--output ALL` is specified, making Job 29 test pass.

**Acceptance Criteria**:
- [ ] `-o ALL` generates ranking_progression along with other views
- [ ] Test from Job 29 now PASSES

---

### Job 31: Write test for index page with rank progression links
**Status**: todo

**Task**: Write a failing test that expects index page to link to rank progression pages.

**Acceptance Criteria**:
- [ ] Test generates index with ranking_progression pages present
- [ ] Test asserts index HTML includes ranking_progression links
- [ ] Test asserts links are correctly formatted
- [ ] Running test produces FAILURE (functionality doesn't exist yet)

---

### Job 32: Add rank progression to index page to pass test
**Status**: todo

**Task**: Update `generate_index.py` to link to rank progression pages, making Job 31 test pass.

**Acceptance Criteria**:
- [ ] Index page lists ranking_progression HTML files for each league
- [ ] Links are correctly formatted and clickable
- [ ] Test from Job 31 now PASSES

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
