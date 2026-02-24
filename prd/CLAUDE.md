# PRD Agent Guide

You are an autonomous agent. Each session, complete **ONE atomic task** from the active PRD, then stop.

## Orientation

1. **Verify branch**: Run `git branch --show-current` and confirm you're on `feature/<prd-name>`. If not, run `git checkout feature/<prd-name>`.
2. **Read the PRD**: `prd/<prd-name>.md`
3. **Read the activity log**: `prd/<prd-name>-activity.md`
4. **Read project conventions**: `AGENTS.md` (root) — contains architecture, code quality rules, TDD workflow, and virtual environment setup
5. **Check git status**: See what's changed since last session. If partial work exists, verify what already works before writing new code.

## Your Task

1. Find the next task where `"passes": false`
2. If partial work exists from a prior session, continue from where it left off — do not rewrite working code
3. Complete **ALL** acceptance criteria for that one task
4. Test your changes
5. Follow completion steps below, then **STOP — do not continue to the next task**

## Quality Check (Before Completion)

Before marking your task complete, pause and verify:

1. **Verify behavior**: Does the change actually work? Test it, don't assume.
2. **Demand elegance**: For non-trivial changes, ask "is there a more elegant way?"
   If the fix feels hacky, step back and implement the clean solution.
   Skip this for simple, obvious fixes — don't over-engineer.
3. **Staff engineer test**: Would a senior developer approve this code?
   Check for root causes vs. band-aids, proper error handling, clean abstractions.
4. **Minimal impact**: Did you touch only what's necessary? No unrelated changes?

## Completion Steps

1. **Run quality checks** (see AGENTS.md for full details):
   ```bash
   source venv/Scripts/activate
   python -m ruff check --fix .
   python -m mypy fpl/ --ignore-missing-imports
   python -m pytest
   ```
2. **Update PRD** — set `"passes": true` for your ONE completed task only. Do not mark other tasks. Only modify the `passes` field — never remove, edit, or reorder tasks.
3. **Log progress** — append a session entry to the activity log (`prd/<prd-name>-activity.md`):
   ```markdown
   ### Session N — YYYY-MM-DD
   **Task:** Task N — <title>
   **Status:** completed
   **Notes:** <brief description of what was done>
   ```
4. **Commit** — stage all, write a proper commit message:
   - Subject: imperative mood, no period
   - Body: bullet points of what was done
   - No Co-Authored-By lines
5. **Exit** — do not run verification commands after commit

## Exit Signals

**You MUST emit exactly one signal at the very end of your output.** `ralph.py` parses these to track progress — without a signal, the iteration counts as a stall.

| Signal | When |
|--------|------|
| `<promise>COMPLETE</promise>` | You finished your task (ralph.py will check if more tasks remain) |
| `<promise>DONE</promise>` | All tasks were already complete before you started — nothing to do |
| `<promise>STUCK: reason</promise>` | You cannot complete the task after reasonable effort |

## Permission Errors

If a tool call is **denied due to permissions** (e.g., a Bash command is not in the allowlist), **stop immediately**. Do not retry, work around, or continue with the task. Instead:

1. List every command you need that was denied or that you expect will be denied
2. Emit `<promise>STUCK: Permission denied — need allowlist entries: <comma-separated list of commands></promise>`

## When Things Go Sideways

If your approach isn't working after a reasonable attempt:
- **STOP pushing** — don't brute-force through errors
- Note the blocker in the activity log
- Exit the session so the next iteration can take a fresh approach
- Do NOT mark the task as passing if acceptance criteria aren't met

## Trust Command Output

- If a command succeeds, move on. Do not re-run to verify.
- Do not run `git status` after successful commits.
- LF/CRLF warnings are normal on Windows.

## Do NOT

- Work on more than one task per session
- Mark a task `"passes": true` without testing it
- Modify task descriptions, acceptance criteria, or ordering
- Re-run commands that already succeeded
- Run `git status` or `git log` after a successful commit
- Introduce new dependencies without explicit need
- Add new features beyond what the task specifies
- Add Co-Authored-By lines to commits

## PRD File Naming

PRDs follow a strict naming convention so `ralph.py` can discover and aggregate them:

| File | Pattern | Example |
|------|---------|---------|
| Main PRD | `<name>.md` | `weekly-report.md` |
| Phase files | `<name>-phase-<label>.md` | `weekly-report-phase-api.md` |
| Activity log | `<name>-activity.md` | `weekly-report-activity.md` |
| Resources | `<name>-resources/` | `weekly-report-resources/` |

Phase files **must** contain `-phase-` in the name — otherwise they won't be found by `ralph.py --list` or counted toward the main PRD's progress.

## Project Context

For project architecture, module documentation, coding conventions, and testing patterns, see the root [AGENTS.md](../AGENTS.md).
