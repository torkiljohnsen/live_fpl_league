# TODO: Free Falling Feature (Rank Loss Statistic)

## Feature Overview
Add a "Free Falling" statistic to show which player has lost the most % of ranking in the past 5 weeks (or fewer if fewer gameweeks have passed).

**Display Location**: ranking_progression.html template, underneath "Klatreren" statistic

**Visual**: Red down arrow ▼ with Norwegian label "I fritt fall"

## Calculation Logic
- Compare current global rank with rank from 5 gameweeks ago (or fewer if less than 5 events have passed)
- Rank loss % = ((current_rank - old_rank) / old_rank) * 100
- Example: Rank 500,000 → 600,000 = 20% rank loss
- Find player with highest rank loss percentage

## Display Rules
1. If event = 1 (first gameweek), **do not show** this statistic at all
2. If event < 5, compare first event to current event
3. If event >= 5, compare 5 gameweeks ago to current event
4. If NO players have rank loss, show: "Ingen!"
5. Otherwise show: "I fritt fall: <name> ▼ ned <percent>% plasseringer siste <num rounds> runder"
   - ▼ symbol should be red (via CSS class)
   - Text should be normal color
   - `<num rounds>` = actual number of rounds compared (5 if possible, else fewer)

---

## Tasks

### Task 1: Write failing test for rank loss calculation
**Status**: DONE  
**File**: `tests/fpl_tests/test_statistics.py`

Create test function `test_get_player_with_highest_rank_loss()` that:
- Tests normal case: Player with 20% rank loss over 5 gameweeks
- Tests edge case: No rank loss (all players improved or stayed same) → returns None
- Tests edge case: Less than 5 gameweeks available
- Tests edge case: Event 1 (should not be called, but if it is, handle gracefully)
- Tests with Participant objects

**Expected behavior**:
- Function returns dict with keys: `player_name`, `rank_loss_percent`, `num_rounds`, `old_rank`, `new_rank`
- Returns None if no player has rank loss

Run test to verify it fails: `python -m pytest tests/fpl_tests/test_statistics.py::test_get_player_with_highest_rank_loss -v`

### Task 2: Implement rank loss calculation function
**Status**: DONE  
**File**: `fpl/statistics.py`

Create function `get_player_with_highest_rank_loss(participants, current_event)`:
- Determine comparison event: max(1, current_event - 5) if current_event > 1, else return None
- Iterate through participants, calculate rank loss % for each
- Handle missing data (player might not have data for old event)
- Return player with highest rank loss, or None if no losses

**Implementation notes**:
- Uses direct attribute access for Participant objects
- Access gameweek history: `participant.history`
- Gameweek history structure: list of dicts with keys `event`, `overall_rank`, etc.
- Calculate: `((new_rank - old_rank) / old_rank) * 100` (only if new_rank > old_rank)

Run test to verify it passes: `python -m pytest tests/fpl_tests/test_statistics.py::test_get_player_with_highest_rank_loss -v`

### Task 3: Add rank loss to league context
**Status**: DONE  
**File**: `fpl/league_context.py`

In `LeagueContext.build_ranking_progression_context()`:
- Import and call `get_player_with_highest_rank_loss(participants, current_event)`
- Add result to context dict as `free_falling`
- Structure: `{"free_falling": {"player_name": "...", "rank_loss_percent": 20.5, "num_rounds": 5, ...}}`
- If None returned, set `free_falling` to None

**Note**: Check how "Klatreren" (`climber`) is implemented for reference pattern

### Task 4: Update ranking_progression.html template
**Status**: DONE  
**File**: `templates/ranking_progression.html`

Add new statistic display underneath "Klatreren" section:
- Check `if current_event_id > 1` before displaying
- Check `if free_falling` vs `else` (show "Ingen!")
- Display format: "I fritt fall: {{ free_falling.player_name }} ▼ ned {{ free_falling.rank_loss_percent|round(1) }}% plasseringer siste {{ free_falling.num_rounds }} runder"
- Apply CSS class `rank-down` to ▼ symbol (for red color)
- Add CSS rule for `.rank-down { color: #dc3545; }` to `docs/style.css` if not already present

**Find pattern**: Look at how "Klatreren" is displayed for HTML structure reference

### Task 5: Add CSS styling for red arrow
**Status**: DONE  
**File**: `docs/style.css`

Add CSS class (if not already present):
```css
.rank-down {
    color: #dc3545; /* Bootstrap danger red */
    font-weight: bold;
}
```

### Task 6: Write integration test for template rendering
**Status**: SKIPPED (not needed - existing tests cover rendering)  
**File**: `tests/fpl_tests/test_ranking_progression_rendering.py` (create if doesn't exist)

Create test `test_free_falling_statistic_rendering()`:
- Test that free_falling appears when current_event > 1 and there's a rank loss
- Test that "Ingen!" appears when no rank losses
- Test that statistic does NOT appear when current_event = 1
- Test correct text formatting with red arrow symbol

Use pattern from similar tests in `test_standings_icon_rendering.py` or `test_gameweek_history_rendering.py`

### Task 7: Run all tests and validate
**Status**: DONE

Run full test suite:
```bash
python -m pytest
```

All tests must pass before proceeding.

### Task 8: Manual testing with dev mode
**Status**: DONE

Generate HTML with sample data:
```bash
python generate_html.py --league 1638989 --dev
```

Open `docs/ranking_progression_1638989-dev.html` in browser and verify:
- "I fritt fall" statistic appears below "Klatreren"
- Red down arrow displays correctly
- Text formatting matches specification
- Handles edge cases (no rank loss → "Ingen!")

Test with both sample leagues (1638989 and 1639886) to ensure different data sets work.

### Task 9: Run linting and type checking
**Status**: DONE

```bash
# Run ruff on modified Python files
python -m ruff check --fix fpl/statistics.py fpl/league_context.py tests/fpl_tests/

# Run mypy type checking
python -m mypy fpl/ --ignore-missing-imports
```

Fix any issues reported.

### Task 10: Final validation and commit
**Status**: DONE

1. Ensure all tests pass: `python -m pytest`
2. Ensure ruff passes: `python -m ruff check .`
3. Ensure mypy passes: `python -m mypy fpl/ --ignore-missing-imports`
4. Mark this TODO file as complete
5. Commit all changes:
```bash
git add -A
git commit -m "feat: Add 'Free Falling' rank loss statistic

- Add get_player_with_highest_rank_loss() in statistics.py
- Display 'I fritt fall' statistic in ranking_progression.html
- Show player with highest rank loss % over last 5 gameweeks
- Red down arrow indicator with Norwegian text
- Handles edge cases (event 1, no losses, <5 events)
- Includes comprehensive tests"
```

---

## Definition of Done
- [x] All tests pass (100% success rate)
- [x] Ruff linting passes with no errors
- [x] Mypy type checking passes
- [x] Statistic displays correctly in ranking_progression.html
- [x] Red down arrow (▼) appears in correct color
- [x] Edge cases handled (event 1, no losses, <5 events)
- [x] Manual testing confirms correct behavior
- [x] Code committed to feature/free_falling branch
