# TODO: Refactor Project Structure and Build System

## Objective
Modernize the project build system and improve code quality infrastructure:
1. Migrate from `requirements.txt` to `pyproject.toml` for dependency management
2. Ensure comprehensive ruff linting across entire codebase
3. Add GitHub Actions workflow for automated linting on dev/main branches
4. Review and document project code structure with refactor proposals

## Requirements

### 1. Dependencies
Current state:
- [`requirements.txt`](requirements.txt) - Current dependency specification
- [`pyproject.toml`](pyproject.toml) - Partially configured with ruff settings only

Target state:
- Fully configured [`pyproject.toml`](pyproject.toml) with:
  - Project metadata (name, version, description, authors)
  - All dependencies from requirements.txt
  - Build system configuration
  - Tool configurations (pytest, ruff)

### 2. Ruff Linting
Current state:
- Ruff configured in [`pyproject.toml`](pyproject.toml)
- Used manually before commits (documented in [`AGENTS.md`](AGENTS.md))

Target state:
- All Python files pass ruff checks
- Consistent code style across codebase
- No linting errors or warnings

### 3. CI/CD Integration
Current state:
- No automated checks

Target state:
- GitHub Actions workflow that:
  - Runs on pull requests to `dev` and `main` branches
  - Executes ruff linting on all Python files
  - Runs pytest test suite
  - Prevents merge if checks fail

### 4. Code Structure Analysis
Target deliverable:
- Document analyzing current code organization
- Identify code smells, duplication, and improvement opportunities
- Propose concrete refactoring plans with pros/cons
- Prioritize refactorings by impact and effort

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
- Make a git commit of your work with a descriptive message

**TDD Methodology**: For jobs with building new features, follow Test-Driven Development where applicable:
1. Write a failing test first (when testing is relevant)
2. Write minimal code to make the test pass
3. Ensure test passes before marking job as done

---

### Job 1: Migrate dependencies to pyproject.toml
**Status**: todo

**Task**: Move all dependencies from requirements.txt to pyproject.toml and add project metadata.

**Acceptance Criteria**:
- [ ] All dependencies from [`requirements.txt`](requirements.txt) added to `[project.dependencies]` section in [`pyproject.toml`](pyproject.toml)
- [ ] Project metadata added: name, version, description, authors, requires-python
- [ ] `[build-system]` section configured (use setuptools or hatchling)
- [ ] Optional dependencies group added for dev tools (pytest, etc.) as `[project.optional-dependencies]`
- [ ] Virtual environment can be recreated using: `pip install -e .`
- [ ] All existing tests pass after reinstallation
- [ ] Document in commit message: "Do NOT delete requirements.txt yet - will be removed in final job"

---

### Job 2: Verify project installs and runs with pyproject.toml
**Status**: todo

**Task**: Test that the project works correctly with new pyproject.toml configuration.

**Acceptance Criteria**:
- [ ] Create fresh virtual environment in temporary location
- [ ] Install project: `pip install -e .` (editable mode)
- [ ] Install dev dependencies: `pip install -e ".[dev]"`
- [ ] Run full test suite: `python -m pytest` - all tests pass
- [ ] Run HTML generation in dev mode: `python generate_html.py -l 1638989 --dev -o ALL`
- [ ] Verify generated HTML files exist in [`docs/`](docs/) folder
- [ ] Commit any fixes needed to pyproject.toml

---

### Job 3: Run ruff check on entire codebase and document findings
**Status**: todo

**Task**: Execute ruff on all Python files and create a detailed report of all issues found.

**Acceptance Criteria**:
- [ ] Run: `python -m ruff check .` from project root
- [ ] Create file `RUFF_AUDIT.md` documenting:
  - Total number of issues found
  - Breakdown by rule category (imports, whitespace, naming, etc.)
  - List of files with most issues
  - Sample of most common violations
- [ ] Do NOT fix issues yet - just document them
- [ ] Commit the audit report

---

### Job 4: Fix ruff issues in fpl/ package (part 1 - imports and formatting)
**Status**: todo

**Task**: Fix import sorting, unused imports, and basic formatting issues in the `fpl/` directory.

**Acceptance Criteria**:
- [ ] Run: `python -m ruff check --fix fpl/` 
- [ ] Manually review and fix any issues that couldn't be auto-fixed
- [ ] Focus only on these rule categories:
  - Import sorting (I)
  - Unused imports (F401)
  - Trailing whitespace (W293)
- [ ] Run tests after fixes: `python -m pytest` - all tests pass
- [ ] Run: `python -m ruff check fpl/` - no errors in these categories
- [ ] Commit changes with message describing categories fixed

---

### Job 5: Fix ruff issues in fpl/ package (part 2 - code quality)
**Status**: todo

**Task**: Fix remaining code quality issues in `fpl/` directory (naming, dict literals, etc.).

**Acceptance Criteria**:
- [ ] Run: `python -m ruff check --fix fpl/`
- [ ] Fix issues in these categories:
  - Dict literals (C408)
  - Naming conventions (N)
  - Pyflakes errors (F)
- [ ] Run tests after fixes: `python -m pytest` - all tests pass
- [ ] Run: `python -m ruff check fpl/` - no errors remain
- [ ] Commit changes with message describing categories fixed

---

### Job 6: Fix ruff issues in tests/ directory
**Status**: todo

**Task**: Apply ruff fixes to all test files.

**Acceptance Criteria**:
- [ ] Run: `python -m ruff check --fix tests/`
- [ ] Manually fix any issues that couldn't be auto-fixed
- [ ] Test files may have more relaxed standards - use `# noqa` comments where appropriate for test-specific patterns
- [ ] Run tests: `python -m pytest` - all tests pass
- [ ] Run: `python -m ruff check tests/` - no errors remain (or only acceptable noqa-tagged lines)
- [ ] Commit changes

---

### Job 7: Fix ruff issues in root Python files
**Status**: todo

**Task**: Apply ruff fixes to [`generate_html.py`](generate_html.py), [`generate_index.py`](generate_index.py), and any other root-level Python files.

**Acceptance Criteria**:
- [ ] Run: `python -m ruff check --fix *.py`
- [ ] Manually fix any remaining issues
- [ ] Test both scripts work:
  - `python generate_html.py -l 1638989 --dev -o ALL`
  - `python generate_index.py`
- [ ] Run: `python -m ruff check *.py` - no errors remain
- [ ] Commit changes

---

### Job 8: Verify entire codebase passes ruff checks
**Status**: todo

**Task**: Final verification that all ruff issues are resolved across the entire project.

**Acceptance Criteria**:
- [ ] Run: `python -m ruff check .` - zero errors reported
- [ ] Run: `python -m pytest` - all tests pass
- [ ] Test HTML generation: `python generate_html.py -l 1638989 --dev -o ALL`
- [ ] Verify generated files look correct in browser
- [ ] Update `RUFF_AUDIT.md` with "RESOLVED" status
- [ ] Commit any final fixes

---

### Job 9: Create GitHub Actions workflow for linting
**Status**: todo

**Task**: Add GitHub Actions workflow file to run ruff and pytest on pull requests.

**Acceptance Criteria**:
- [ ] Create `.github/workflows/lint-and-test.yml` file
- [ ] Workflow triggers on:
  - Pull requests to `dev` branch
  - Pull requests to `main` branch
- [ ] Workflow steps include:
  - Checkout code
  - Set up Python (version specified in pyproject.toml)
  - Install dependencies: `pip install -e ".[dev]"`
  - Run ruff: `python -m ruff check .`
  - Run tests: `python -m pytest`
- [ ] Add status badge to [`README.md`](README.md) (optional but recommended)
- [ ] Commit workflow file
- [ ] Document in commit message: "Workflow will be tested when PR is created"

---

### Job 10: Analyze project code structure
**Status**: todo

**Task**: Review the codebase architecture and identify refactoring opportunities.

**Acceptance Criteria**:
- [ ] Create `CODE_STRUCTURE_ANALYSIS.md` with:
  - **Current Architecture**: Diagram/description of module relationships and data flow
  - **Module Responsibilities**: What each module does and its dependencies
  - **Identified Issues**: Code smells, circular dependencies, tight coupling, etc.
- [ ] Review each module in [`fpl/`](fpl/) directory:
  - [`fpl_api.py`](fpl/fpl_api.py) - API client responsibilities
  - [`fpl_league.py`](fpl/fpl_league.py) - League data aggregation
  - [`league_context.py`](fpl/league_context.py) - Template context builder
  - [`participant.py`](fpl/participant.py) - Participant data processing
  - [`chart_generator.py`](fpl/chart_generator.py) - Chart generation
  - [`rank_calculator.py`](fpl/rank_calculator.py) - Rank calculations
  - [`chip_annotator.py`](fpl/chip_annotator.py) - Chip annotations
  - [`league_template_renderer.py`](fpl/league_template_renderer.py) - Template rendering
- [ ] Analyze coupling between modules (count direct imports)
- [ ] Identify code duplication (similar patterns across files)
- [ ] Commit analysis document

---

### Job 11: Create refactoring proposal document
**Status**: todo

**Task**: Based on Job 10 analysis, create concrete refactoring proposals with priorities.

**Acceptance Criteria**:
- [ ] Create `REFACTOR_PROPOSALS.md` with multiple refactoring options
- [ ] Each proposal includes:
  - **Title**: Short descriptive name
  - **Problem**: What issue it addresses
  - **Solution**: Concrete changes to make
  - **Benefits**: What improves (maintainability, testability, performance)
  - **Risks**: Potential issues or breaking changes
  - **Effort**: Estimated complexity (Small/Medium/Large)
  - **Priority**: High/Medium/Low
- [ ] Proposals should cover:
  - Dependency injection opportunities (e.g., API client injection)
  - Service layer abstractions
  - Data model improvements (typed dataclasses vs dicts)
  - Module responsibility clarification
  - Test coverage improvements
- [ ] Include prioritization matrix (Impact vs Effort)
- [ ] Recommend top 3 refactorings to tackle first
- [ ] Commit proposal document

---

### Job 12: Update documentation with new build system
**Status**: todo

**Task**: Update project documentation to reflect pyproject.toml migration and CI/CD setup.

**Acceptance Criteria**:
- [ ] Update [`README.md`](README.md):
  - Installation instructions use: `pip install -e ".[dev]"`
  - Remove references to `pip install -r requirements.txt`
  - Add section about GitHub Actions CI/CD
  - Add development setup section with ruff commands
- [ ] Update [`AGENTS.md`](AGENTS.md):
  - Update "Dependencies" section to reference pyproject.toml
  - Update installation commands
  - Keep ruff guidelines (they're still relevant)
- [ ] Create/update `CONTRIBUTING.md` (if doesn't exist):
  - Development environment setup
  - Running tests and linting
  - Git workflow with CI/CD checks
- [ ] Commit documentation updates

---

### Job 13: Remove requirements.txt and final cleanup
**Status**: todo

**Task**: Remove old requirements.txt file now that pyproject.toml is fully working.

**Acceptance Criteria**:
- [ ] Verify one final time:
  - Fresh venv can be created
  - `pip install -e ".[dev]"` installs everything needed
  - All tests pass
  - HTML generation works
  - Ruff linting passes
- [ ] Delete [`requirements.txt`](requirements.txt)
- [ ] Search codebase for any references to requirements.txt:
  - `grep -r "requirements.txt" .`
  - Update or remove found references
- [ ] Update `.gitignore` if it references requirements.txt
- [ ] Final commit: "Complete migration to pyproject.toml, remove requirements.txt"

---

## Post-Implementation Verification

After completing all jobs:
1. Create a test branch
2. Clone repo fresh in new location
3. Create venv: `python -m venv venv`
4. Activate: `source venv/Scripts/activate` (Windows Git Bash)
5. Install: `pip install -e ".[dev]"`
6. Run tests: `python -m pytest`
7. Run linting: `python -m ruff check .`
8. Generate HTML: `python generate_html.py -l 1638989 --dev -o ALL`
9. Verify all works correctly
10. Create pull request to test GitHub Actions workflow

## Notes

- This refactor should NOT change any functionality - only build system and code quality
- All existing tests must continue to pass throughout
- The project should remain deployable to GitHub Pages without changes
- Keep generated HTML files format unchanged (existing links should keep working)
