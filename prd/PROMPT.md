# Agent Starting Prompt

You are an autonomous agent working on the Weekly FPL League Report & Narrative System. Each session, complete ONE atomic task and exit.

**Branch:** `feature/weekly-report`

## Orientation

1. **Verify branch**: Run `git branch --show-current` and confirm you're on `feature/weekly-report`. If not, run `git checkout feature/weekly-report`.
2. **Read the PRD**: `prd/weekly-report.md`
3. **Read the activity log**: `prd/weekly-report-activity.md`
4. **Read project conventions**: `AGENTS.md` (root) — contains code quality rules, TDD workflow, virtual environment setup
5. **Check git status**: See what's changed since last session

## Your Task

1. Find the next task where `"passes": false`
2. Complete ALL acceptance criteria
3. Test your changes
4. Follow completion steps below

## Development

**Activate venv:** `source venv/Scripts/activate`
**Verify venv:** `which python` (should show `venv/Scripts/python`)
**Run tests:** `python -m pytest`
**Run linter:** `python -m ruff check --fix .`
**Run type checker:** `python -m mypy fpl/ --ignore-missing-imports`
**Run report (dev mode):** `python generate_weekly_report.py -l 1639886 --dev`

## Key Files

| File | Purpose |
|------|---------|
| `fpl/fpl_api.py` | API client (live + dev mode), extend with new methods |
| `fpl/fpl_api_protocol.py` | Protocol interface for API (duck typing) |
| `fpl/statistics.py` | Existing pure stat functions — pattern reference for new stats |
| `fpl/participant.py` | Participant dataclass — reference for data model patterns |
| `generate_html.py` | Existing CLI entry point — pattern reference for new CLI |
| `tests/fpl_tests/` | Test directory with DummyAPI pattern and data_samples/ |
| `docs/WEEKLY_REPORT_PLAN.md` | Full data schemas, API endpoints, award definitions |
| `docs/REIDAR_PERSONA.md` | Reidar character definition (voice, personality, rules) |
| `docs/NARRATIVE_GUIDE.md` | Narrative structure, award mappings, continuity rules |
| `docs/REIDAR_EXAMPLES.md` | Few-shot example narratives in Reidar's voice |
| `fpl/reidar_memory.py` | Reidar memory system (persistent knowledge across GWs) |
| `reidar_memory/` | Reidar's persistent files (manager profiles, season arc, GW summaries) |
| `prd/weekly-report-resources/` | Reference material: previous manually-written reports |
| `prd/weekly-report.md` | PRD with task list (update `passes` field) |
| `prd/weekly-report-activity.md` | Activity log (append session entries) |

## Constraints

- **Python 3.13** — target version, use modern Python features
- **Pure functions** for stats — follow `statistics.py` pattern: data in, dicts out, no side effects
- **Protocol-based API** — all API consumers accept `FPLAPIProtocol`, not `FPL_API` directly
- **DummyAPI for tests** — never call live FPL API in tests
- **Dev mode** — sample data auto-management via `fpl/sample_data/`
- **TDD** — write failing test first, then implement (per AGENTS.md)
- **No Co-Authored-By** in commit messages
- **Line length**: 120 characters (ruff configured in pyproject.toml)
- **Ruff + mypy + pytest** must all pass before committing

## Completion Steps

1. **Run quality checks**:
   ```bash
   source venv/Scripts/activate
   python -m ruff check --fix .
   python -m mypy fpl/ --ignore-missing-imports
   python -m pytest
   ```
2. **Update PRD** — Set `"passes": true` for completed task in `prd/weekly-report.md`
3. **Update activity log** — Add session entry to `prd/weekly-report-activity.md`
4. **Commit changes** — Stage all, write proper commit message (50 char subject, body with bullets)
5. **Exit** — Do not run verification commands after commit

## Trust Command Output

- If a command succeeds, move on. Do not re-run to verify.
- Do not run `git status` after successful commits.
- LF/CRLF warnings are normal on Windows.

## Do NOT

- Work on multiple tasks per session
- Modify task descriptions or reorder tasks
- Skip acceptance criteria
- Re-run commands that already succeeded
- Add Co-Authored-By lines to commits
