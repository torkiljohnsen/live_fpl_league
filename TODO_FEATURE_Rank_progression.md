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
  1. FIRST: Run ruff linting on changed Python files: `python -m ruff check --fix <changed_files>` (or `python -m ruff check --fix .` for all files)
  2. SECOND: Run ALL tests: `python -m pytest` (not just tests for current job)
  3. If any test fails, fix the issue before proceeding. Repeat steps 1-2 until all tests pass
  4. Mark the job status as done in the TODO file
  5. Only commit when all tests pass and job is marked done
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
**Status**: done

**Task**: Configure X-axis to display only integer gameweek numbers from 1 to latest event. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates chart with gameweeks 1-7
- [x] Test asserts X-axis tick values are integers [1, 2, 3, 4, 5, 6, 7]
- [x] Test asserts no decimal values appear on X-axis
- [x] X-axis displays only whole numbers (no decimals like 3.5)
- [x] X-axis range goes from 1 to latest gameweek number
- [x] Test passes

---

### Job 26: Set dark theme as default
**Status**: done

**Task**: Change default theme from light to dark. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test calls chart generator without theme parameter
- [x] Test asserts background is dark colored (default dark theme applied)
- [x] Test asserts line colors are light/bright
- [x] Default theme parameter is `theme="dark"`
- [x] Charts generated without explicit theme use dark theme
- [x] Test passes

---

### Job 27: Set Y-axis range from 1 to total_players
**Status**: done

**Task**: Configure Y-axis range based on total_players from bootstrap-static. Might need to fetch updated numbers here from the live API. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test provides total_players value (e.g., 10000000)
- [x] Test asserts Y-axis range is [1, total_players]
- [x] Test asserts Y-axis is reversed (1 at top, total_players at bottom)
- [x] Function accepts `total_players` parameter from bootstrap-static API
- [x] Y-axis range is explicitly set from 1 (top) to total_players (bottom)
- [x] Test passes

---

### Job 28: Add asterisk to unfinished gameweek on X-axis
**Status**: done

**Task**: Mark unfinished gameweeks with asterisk based on bootstrap-static data. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test provides gameweek data with event 7 having `finished: false`
- [x] Test asserts X-axis label for event 7 displays "7*"
- [x] Test asserts finished events (1-6) display without asterisk
- [x] Function receives event finish status from bootstrap-static
- [x] Unfinished gameweeks display with asterisk (e.g., "7*")
- [x] Finished gameweeks display as plain numbers
- [x] Test passes

---

### Job 29: Make graph background color configurable with RGBA
**Status**: done

**Task**: Change background color configuration to support RGBA format with opacity. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test calls function with `bg_color="rgba(0, 0, 0, 0.1)"`
- [x] Test asserts background uses the specified RGBA color
- [x] Test verifies opacity is correctly applied
- [x] Function accepts `bg_color` parameter in RGBA format (e.g., "rgba(0, 0, 0, 0.1)")
- [x] Default background color is `rgba(0, 0, 0, 0.1)` (black with 10% opacity)
- [x] Background opacity is properly rendered in output
- [x] Test passes

---

### Job 30: Center graph horizontally in template
**Status**: done

**Task**: Update ranking_progression template to center the chart horizontally, matching layout in league_gameweek_history and league_standings templates. Write test first if applicable, then implement.

**Acceptance Criteria**:
- [x] Review CSS/layout in league_gameweek_history.html and league_standings.html
- [x] Apply similar centering approach to ranking_progression.html
- [x] Chart image is centered horizontally in the page
- [x] Layout is consistent with other templates
- [x] Manual test: Verify chart is centered when viewed in browser

---

### Job 31: Add horizontal helper lines for major Y-axis points
**Status**: done

**Task**: Add horizontal gridlines at major Y-axis tick marks (0, 2M, 4M, 6M, etc.). Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates chart with Y-axis major ticks at 0, 2000000, 4000000, 6000000
- [x] Test asserts horizontal gridlines are enabled
- [x] Test asserts gridlines appear at major tick positions
- [x] Chart displays horizontal gridlines at each major Y-axis tick
- [x] Gridlines improve readability without cluttering the chart
- [x] Test passes

---

### Job 32: Enhance legend format with rank and player details
**Status**: done

**Task**: Change legend format to show: Line | League rank | Player name | Overall rank (rounded to thousands). Example: "--- 1. Torkil (345k)". Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates participants with league_rank, first_name, and latest overall_rank
- [x] Test asserts legend displays format: "1. Torkil (345k)"
- [x] Test verifies overall_rank is rounded to thousands (e.g., 345123 → 345k)
- [x] Legend format shows: `<league_rank>. <first_name> (<overall_rank_rounded>)`
- [x] Overall rank is rounded to nearest thousand with "k" suffix
- [x] Legend entries are numbered by league rank
- [x] Test passes

---

### Job 33: Add statistics section - Highest team value
**Status**: done

**Task**: Below the graph, add a statistics section with "Highest team value" statistic. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates participants with history containing bank and value fields
- [x] Test calculates team_value = value / 10
- [x] Test asserts highest team value is correctly identified
- [x] Test asserts format is "Team name (Player name) - £XXX.XM"
- [x] Template displays "Stats:" headline
- [x] First statistic shows: "Highest team value: <team_name> (<player_name>) - £<value>M"
- [x] Team value is calculated from latest event: value / 10
- [x] Value is displayed in millions with one decimal (e.g., £100.5M)
- [x] Test passes

---

### Job 34: Add statistics section - In form (consecutive green arrows)
**Status**: done

**Task**: Add "In form" statistic showing team(s) with most consecutive overall_rank improvements (green arrows). Write test first, then implement.

**Acceptance Criteria**:
- [x] Test creates participant history with consecutive rank decreases
- [x] Test asserts function correctly counts consecutive green arrows
- [x] Test verifies teams are identified and formatted correctly
- [x] Test asserts "None" is shown when no team has green arrows
- [x] Test asserts multiple teams are listed if tied
- [x] Test verifies statistic is hidden before event 3
- [x] Calculate consecutive green arrows: overall_rank decreases from previous event
- [x] Identify team(s) with most consecutive green arrows
- [x] Display format: "<FirstName>, <FirstName> ▲ grønn pil <count> runder på rad"
- [x] Show "None" if no teams have green arrows
- [x] List all teams if multiple teams are tied for most green arrows
- [x] Only display this statistic from event 3 onwards
- [x] Test passes

---

### Job 35: Fix chart background color
**Status**: done

**Task**: Looking at /live_fpl_league/docs/ranking_progression_1639886-dev.html - Bug: Background shows as white. Should be RGBA(0,0,0,0.1) by default. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test verifies default background color is "rgba(0, 0, 0, 0.1)"
- [x] Test asserts background is not white/opaque by default
- [x] Identify and fix issue causing white background in rendered chart
- [x] Verify fix with generated HTML in browser
- [x] Background displays as intended RGBA(0,0,0,0.1) - black with 10% opacity
- [x] Test passes

---

### Job 36: Increase text size for TV display readability
**Status**: done

**Task**: Chart will be shown on a big screen from a distance. Increase font sizes for legend, axis labels, and axis titles. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test asserts legend font size is increased (e.g., 16-20px)
- [x] Test asserts axis label font size is increased (e.g., 14-18px)
- [x] Test asserts axis title font size is increased (e.g., 18-24px)
- [x] Legend text is larger and readable from distance
- [x] Axis tick labels (numbers) are larger and readable from distance
- [x] Axis titles ("Gameweek", "Overall Rank") are larger and readable from distance
- [x] Manual test: Verify readability from 3+ meters on big screen
- [x] Test passes

---

### Job 37: Reduce top padding above chart
**Status**: done

**Task**: Reduce top padding above the chart - currently has too much whitespace. Make padding consistent for all chart edges. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test asserts top margin/padding is reduced from current value
- [x] Test asserts all margins (top, bottom, left, right) are equal or balanced
- [x] Top padding is reduced to match other edges
- [x] Chart has consistent padding on all sides
- [x] Manual test: Verify improved layout in browser
- [x] Test passes

---

### Job 38: Adjust gridline brightness for dark theme
**Status**: done

**Task**: Visual refactor of gridlines for better dark theme appearance. Vertical gridlines (on X-axis gameweeks) are too bright. The horizontal zero line (Y-axis 0 mark) is too bright. The horizontal gridlines (2M, 4M, 6M, etc.) are too dark and barely visible. Write test first, then implement.

**Acceptance Criteria**:
- [x] Test verifies X-axis vertical gridlines have reduced brightness for dark theme
- [x] Test verifies Y-axis zero line has reduced brightness for dark theme
- [x] Test verifies Y-axis horizontal gridlines (major ticks) have increased brightness for dark theme
- [x] X-axis vertical gridlines are more subtle/less prominent
- [x] Y-axis zero line is more subtle/less prominent
- [x] Y-axis horizontal gridlines at 2M, 4M, 6M, etc. are brighter and more visible
- [x] Manual test: Verify improved visual balance in browser
- [x] Test passes

---

### Job 39: Fix overlapping semi-transparent backgrounds and increase default opacity
**Status**: todo

**Task**: The chart area and legend box inherit the same semi-transparent background as the main plot background, causing a darker appearance where they overlap. Make the plot area and legend box backgrounds fully transparent. Also change default background color from rgba(0,0,0,0.1) to rgba(0,0,0,0.3). Write test first, then implement.

**Acceptance Criteria**:
- [ ] Test verifies default background color is "rgba(0, 0, 0, 0.3)"
- [ ] Test verifies plot area background is fully transparent
- [ ] Test verifies legend background is fully transparent
- [ ] Default background color changed to rgba(0,0,0,0.3)
- [ ] Plot area (graph area) has transparent background
- [ ] Legend box has transparent background
- [ ] No overlapping semi-transparent backgrounds
- [ ] Manual test: Verify improved appearance in browser
- [ ] Test passes

---

### Job 40: Reduce chart top padding further
**Status**: todo

**Task**: The top padding above the chart is still too large. Reduce it further for better visual balance. Write test first, then implement.

**Acceptance Criteria**:
- [ ] Test asserts top margin is further reduced from current value
- [ ] Top padding is reduced to improve visual balance
- [ ] Chart appears better balanced with less whitespace above
- [ ] Manual test: Verify improved layout in browser
- [ ] Test passes

---

### Job 41: Center stats section in container matching league_standings width
**Status**: todo

**Task**: The stats section at the bottom of ranking_progression template aligns to the left edge of the screen. It should be in a centered container with the same width as league_standings content for consistency. Write test first if applicable, then implement.

**Acceptance Criteria**:
- [ ] Review CSS for league_standings content container width
- [ ] Apply similar container/centering approach to stats section
- [ ] Stats section uses centered container (not full screen width)
- [ ] Container width matches league_standings for consistency
- [ ] Manual test: Verify stats section is properly centered in browser
- [ ] Test passes (if applicable)

---

### Job 42: Improve stats section layout with consistent label alignment
**Status**: todo

**Task**: Use a definition list or ensure all labels have the same width so stat values align on the left edge. Improve readability and visual consistency. Write test first if applicable, then implement.

**Acceptance Criteria**:
- [ ] Consider using HTML `<dl>` definition list for stats
- [ ] Ensure all stat labels have consistent width
- [ ] Stat values align on the same left edge
- [ ] Layout is visually cleaner and more readable
- [ ] Manual test: Verify improved alignment in browser
- [ ] Test passes (if applicable)

---

### Job 43: Apply green style to arrow in "I toppform" stat
**Status**: todo

**Task**: The triangle/arrow (▲) in the "I toppform" stat text should have green styling applied. Find existing green CSS class and apply it. Write test first if applicable, then implement.

**Acceptance Criteria**:
- [ ] Locate existing green arrow CSS class in style.css
- [ ] Apply green styling to arrow in "I toppform" stat
- [ ] Arrow displays in green color
- [ ] Manual test: Verify green arrow in browser
- [ ] Test passes (if applicable)

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
