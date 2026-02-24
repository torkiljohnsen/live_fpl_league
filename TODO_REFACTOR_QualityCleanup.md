# TODO: Quality Cleanup and Agent Instructions Improvements

## Objective
Clean up stale artifacts, fix CI/CD inconsistencies, and improve agent instructions for faster/better agentic work.

This TODO covers three areas:
1. **Housekeeping** - Remove dead files and stale artifacts
2. **CI/CD fixes** - Align versions and fix missing outputs
3. **Agent instruction improvements** - Make AGENTS.md more effective for autonomous agents

## Implementation Steps

**Agent instructions**:
- Keep chat/text output (responses to me) at a minimum, to conserve token usage. No need to consider personal feelings, this is strictly business.
- Write concise and succinct code. Respect Zen of Python.

**Job iteration instructions**
- Start at the first job with `status: todo`.
- Activate the virtual environment before you begin.
- Complete ONLY that job, then stop. Stay within the job description. The next agent will handle the next job.
- Look at commit history in the current branch if you are unsure of what has been done in previous jobs.
- As you complete acceptance criteria, check their checkboxes
- After you finish a job:
  - Verify that all acceptance criteria have been met, and if so, change the status for the job to done
  - If all acceptance criteria haven't been met, continue working, revise your plan if needed
- **Before committing**: Run `python -m pytest` to make sure nothing is broken.
- Make a git commit of your work with a descriptive message.

---

### Job 1: Remove dead files from repository root
**Status**: todo

**Task**: Delete empty stub files and stale artifacts that confuse agents and clutter the repo.

**Files to remove**:
- `test.py` (0 bytes, empty stub)
- `template.html` (0 bytes, empty stub)
- `sample_data.json` (old artifact, superseded by `fpl/sample_data/` directory)

**Also**:
- Remove tracked `.coverage` file: `git rm --cached .coverage` (it's already in `.gitignore` but was committed before the rule existed)

**Acceptance Criteria**:
- [ ] `test.py` deleted from repo
- [ ] `template.html` deleted from repo
- [ ] `sample_data.json` deleted from repo
- [ ] `.coverage` removed from git tracking (via `git rm --cached`)
- [ ] All tests still pass: `python -m pytest`

---

### Job 2: Archive completed TODO files
**Status**: todo

**Task**: Move fully completed TODO files to an `archive/` directory to reduce root clutter and save agent tokens (agents currently read these files only to discover they're 100% done).

All three files are 100% complete:
- `TODO_FEATURE_Rank_loss.md` — All 10 tasks DONE, merged via PR #19
- `TODO_FEATURE_Rank_progression.md` — All 44 jobs done (Job 44 was implemented as `fpl/formatters.py` but not marked done until this review)

**Acceptance Criteria**:
- [ ] Create `archive/` directory
- [ ] Move `TODO_FEATURE_Rank_loss.md` to `archive/`
- [ ] Move `TODO_FEATURE_Rank_progression.md` to `archive/`
- [ ] Add `archive/` to root AGENTS.md directory structure section with a one-line description: "Completed TODO files"
- [ ] Verify no broken links in other files referencing these TODOs (search for their filenames)

---

### Job 3: Fix CI Python version mismatch
**Status**: todo

**Task**: [`pr-tests.yml`](.github/workflows/pr-tests.yml) uses Python 3.12 but [`pyproject.toml`](pyproject.toml) targets Python 3.13. Align them to prevent version-specific issues slipping through CI.

**Acceptance Criteria**:
- [ ] `.github/workflows/pr-tests.yml` updated to use `python-version: '3.13'`
- [ ] `.github/workflows/scheduled-build.yml` updated to use `python-version: '3.13'` (instead of `'3.x'`)
- [ ] Both workflows are valid YAML (no syntax errors)

---

### Job 4: Fix nightly build to generate all output types
**Status**: todo

**Task**: [`scheduled-build.yml`](.github/workflows/scheduled-build.yml) runs `generate_html.py -l 1639886,1638989` without `-o ALL`, so ranking_progression pages are not generated nightly.

**Acceptance Criteria**:
- [ ] `scheduled-build.yml` generate step updated to include `-o ALL`
- [ ] Workflow YAML is valid

---

### Job 5: Replace `git add -A` with safer staging in AGENTS.md
**Status**: todo

**Task**: [`AGENTS.md`](AGENTS.md) line 171 recommends `git add -A && git commit` which can accidentally stage sensitive files, `.coverage`, or sample data. Replace with safer guidance.

**Changes to make in [`AGENTS.md`](AGENTS.md)**:
- Replace the `git add -A && git commit -m "Your message"` example with guidance to stage specific files
- Example: `git add fpl/ tests/ templates/ docs/ generate_html.py generate_index.py`
- Add a note: "Avoid `git add -A` or `git add .` — these can stage sensitive files, sample data, or build artifacts"

**Also update the Git Commits section** (around line 222-232) with the same safer pattern.

**Acceptance Criteria**:
- [ ] All instances of `git add -A` in AGENTS.md replaced with specific file staging
- [ ] Warning about `git add -A` / `git add .` added
- [ ] No other markdown files reference `git add -A` (search the repo)

---

### Job 6: Add error recovery section to AGENTS.md
**Status**: todo

**Task**: Agents currently have no guidance for common failure scenarios. Add a "Troubleshooting" section to [`AGENTS.md`](AGENTS.md) after the "Refactoring Best Practices" section.

**Content to add**:

```markdown
### Troubleshooting

**Tests fail after unrelated changes**:
1. Run `python -m pytest -x` to stop at first failure
2. Read the traceback carefully — check if the failure is in your changed code or elsewhere
3. If the failure is pre-existing (not caused by your changes), note it and continue
4. If unsure, check `git diff` to see exactly what you changed

**Virtual environment issues**:
1. Verify activation: `which python` should show `venv/Scripts/python`
2. If packages are missing: `pip install -r requirements.txt`
3. If venv is corrupted: `python -m venv venv --clear` then reinstall

**FPL API is down or unreachable**:
- Use `--dev` flag to work with cached sample data
- If sample data doesn't exist yet, you cannot generate it without API access — work on non-API tasks instead

**Generated HTML looks wrong**:
- Check the template variables with a test: compare `LeagueContext.as_dict()` output
- Verify CSS classes exist in `docs/style.css`
- Check the template for typos in variable names
```

**Acceptance Criteria**:
- [ ] Troubleshooting section added to AGENTS.md
- [ ] Covers: test failures, venv issues, API downtime, HTML rendering issues
- [ ] Placed after "Refactoring Best Practices" section

---

### Job 7: De-duplicate data model docs between AGENTS.md files
**Status**: todo

**Task**: The "Data Model Conventions" and "Participant Class" documentation is duplicated near-identically in root [`AGENTS.md`](AGENTS.md) and [`fpl/AGENTS.md`](fpl/AGENTS.md). Keep the detailed version in `fpl/AGENTS.md` only, and replace the root copy with a link.

**Changes**:
- In root AGENTS.md: Replace the "Data Model Conventions" section (lines ~62-95) with a short summary and a link:
  ```markdown
  ## Data Model Conventions

  See [`fpl/AGENTS.md`](fpl/AGENTS.md) for detailed Participant class documentation, when to use objects vs dicts, and the type-aware module pattern.
  ```
- Keep `fpl/AGENTS.md` unchanged (it has the canonical version)

**Acceptance Criteria**:
- [ ] Root AGENTS.md data model section replaced with link to `fpl/AGENTS.md`
- [ ] `fpl/AGENTS.md` data model section unchanged
- [ ] No information lost (all details preserved in `fpl/AGENTS.md`)

---

### Job 8: Add documentation for generated files in docs/
**Status**: todo

**Task**: There is no documentation telling agents that `docs/` contains auto-generated output. Agents might try to manually edit or clean up HTML files there. Add guidance to root [`AGENTS.md`](AGENTS.md).

**Changes to make in the Directory Structure section for `docs/`**:
```markdown
- **[`docs/`](docs/)** - Generated static HTML output (GitHub Pages ready)
  - **Do not manually edit** - these files are auto-generated by `generate_html.py` and `generate_index.py`
  - Auto-committed nightly by GitHub Actions ([`scheduled-build.yml`](.github/workflows/scheduled-build.yml))
  - [`style.css`](docs/style.css) is the only hand-maintained file in this directory
```

**Acceptance Criteria**:
- [ ] `docs/` directory description in AGENTS.md updated with "do not manually edit" guidance
- [ ] Notes that `style.css` is the exception (hand-maintained)
- [ ] References the nightly build workflow

---

### Job 9: Simplify CLAUDE.md redirect pattern
**Status**: todo

**Task**: Every `CLAUDE.md` file (root, `fpl/`, `templates/`) just says "Read and follow the instructions in AGENTS.md". This adds an extra file read per agent session. Inline the AGENTS.md reference directly.

**Option A** (preferred): Change each CLAUDE.md to contain the actual content from its corresponding AGENTS.md, then delete the AGENTS.md files.

**Option B** (simpler): Keep as-is but acknowledge the tradeoff. Claude Code reads CLAUDE.md automatically but not AGENTS.md, so the redirect is necessary.

**Decision**: Go with **Option B** — keep the current pattern. The redirect is only one line and AGENTS.md is a well-known convention that other tools also read. No changes needed. Mark as done.

**Acceptance Criteria**:
- [ ] Reviewed and decided to keep current pattern (no changes needed)

---

## Future Improvements (not scoped as jobs — for reference only)

These are lower-priority items identified during the review. They could be scoped into their own TODO files when ready.

### Custom Exception Types
- `fpl/fpl_api.py` lets raw `requests` exceptions bubble up
- Create `FPLAPIError`, `FPLRateLimitError`, etc. for better error handling
- Callers can then handle specific failure modes

### Timezone Handling
- `fpl/fpl_league.py` has hardcoded CET+2 for next event calculation
- Should use `zoneinfo.ZoneInfo("Europe/Oslo")` to handle DST transitions correctly
- Affects `get_next_event()` method

### TypedDict for API Responses
- Multiple modules use `dict[str, Any]` for known API response shapes
- Introduce `TypedDict` definitions for: bootstrap-static response, league standings, team history
- Improves IDE support and catches key typos at type-check time

### Template Rendering Tests
- Limited test coverage for template rendering edge cases
- Add tests for: empty league, single participant, missing optional fields
- Existing tests focus on data processing more than rendering
