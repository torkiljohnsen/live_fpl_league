# Reidar's Rapport — Teams Integration & Narrative Website

## Overview

Reidar's weekly narratives are currently only saved as `.md` files in git. This feature adds two things: (1) a narrative article page on GitHub Pages for each gameweek report, and (2) a Teams notification via Adaptive Card posted to the group chat with a teaser and "read more" link.

## Target Users

- **League members** — receive Teams notifications when a new narrative drops, read the full article on a styled page
- **Reidar pipeline** — automated HTML rendering and notification as part of the nightly CI/CD run

## Core Requirements

1. Each narrative rendered as a styled HTML article page in `docs/`, published via GitHub Pages
2. Microsoft Teams Adaptive Card notification with teaser and link to the article page
3. **Feature flag**: Teams notifications require an explicit `--notify-teams` CLI flag on `generate_weekly_report.py`. The flag is OFF by default — the GitHub Actions workflow does NOT send any Teams notifications until this flag is manually enabled after verification.
4. Both steps are non-fatal — failures log warnings but don't break the pipeline
5. No duplicate Teams posts (existing `--skip-existing` flag prevents duplicate runs)
6. No real webhook calls during development — all tests use mocked HTTP

## Tech Stack

- **Language**: Python 3.13 (existing)
- **Templating**: Jinja2 (existing)
- **Markdown rendering**: `markdown` library (new dependency)
- **HTTP**: `requests` (existing)
- **Testing**: pytest with unittest.mock (existing)
- **Linting**: ruff, mypy (existing)

## Architecture

### Narrative Article Pages

Each narrative markdown file gets converted to a styled HTML page:

```
narrative markdown (gw27.md)
  → markdown library → HTML body
  → Jinja2 template (narrative.html extends base.html)
  → styled article page (docs/reidars_rapport_{league_id}_gw{N}.html)
```

Published at: `https://torkiljohnsen.github.io/live_fpl_league/reidars_rapport_{league_id}_gw{N}.html`

**Template structure:**
- Hero image (`reidars_rapport_2.png`, copied to `docs/`)
- Title (extracted from narrative `# ` heading)
- Subtitle ("Runde {N}")
- Navigation bar → standings, GW history, ranking progression pages
- Article body (narrative HTML in centered readable column, ~720px)
- Footer with league info

**Navigation links** (hardcoded per league for now):
- Standings: `league_standings_{league_id}.html`
- Gameweek History: `league_gameweek_history_{league_id}.html`
- Ranking Progression: `ranking_progression_{league_id}.html`

**Visual style**: Dark theme matching existing `style.css` (`#00143C` background, Inter/Sora fonts).

### Teams Adaptive Card

Power Automate Workflows webhook (not classic O365 connector):
- URL stored as `TEAMS_WEBHOOK_URL` environment variable / GitHub Actions secret
- Adaptive Cards only (not MessageCard), version 1.4
- Payload limit: 256 KB
- Supported actions: `Action.OpenUrl`

**Teaser extraction** (deterministic, no API call):
1. Split narrative on `\n\n` to get paragraphs
2. Skip title (`# `) and image (`![`) lines
3. Take first remaining paragraph
4. Strip `**` bold markers
5. Truncate at ~300 chars on word boundary, append `...` if needed

**Card layout:**
- Hero image (GitHub Pages URL)
- Title: "Reidars Rapport — Runde {N}" (bold, large)
- Teaser paragraph (~300 chars)
- Action button: "Les hele Reidars Rapport" → opens article page URL

**Adaptive Card payload format:**
```json
{
  "type": "message",
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "contentUrl": null,
    "content": {
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.4",
      "body": [
        { "type": "Image", "url": "<github-pages-image-url>", "size": "stretch" },
        { "type": "TextBlock", "text": "Reidars Rapport — Runde {N}", "weight": "bolder", "size": "large", "wrap": true },
        { "type": "TextBlock", "text": "<teaser>", "wrap": true, "size": "medium" }
      ],
      "actions": [
        { "type": "Action.OpenUrl", "title": "Les hele Reidars Rapport", "url": "<narrative-page-url>" }
      ]
    }
  }]
}
```

### Pipeline Integration

After narrative is saved in `generate_weekly_report.py`, add two new steps in separate try/except blocks:
1. **Render HTML** → `NarrativeHTMLRenderer.render()` → writes to `docs/`
2. **Post to Teams** → `post_to_teams()` → only if BOTH `--notify-teams` CLI flag is passed AND `TEAMS_WEBHOOK_URL` env var is set

The `--notify-teams` flag is a feature flag that defaults to OFF. The GitHub Actions workflow does NOT pass this flag initially — it must be manually enabled after the HTML rendering has been verified in production. This prevents accidental Teams posts during rollout.

Both steps are non-fatal — failures log warnings but don't break the pipeline.

### GitHub Actions Changes

1. Add `TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}` to the report step's env
2. Add idempotent image copy step: `cp -n weekly_report/reidars_rapport_2.png docs/`
3. `git add docs/` already covers new HTML files

## Files Summary

### Create
- `fpl/narrative_html_renderer.py` — `NarrativeHTMLRenderer` class
- `fpl/teams_notification.py` — `extract_teaser()`, `build_adaptive_card()`, `post_to_teams()`
- `templates/narrative.html` — Jinja2 template extending `base.html`
- `tests/fpl_tests/test_narrative_html_renderer.py`
- `tests/fpl_tests/test_teams_notification.py`

### Modify
- `requirements.txt` — add `markdown`
- `fpl/__init__.py` — export `NarrativeHTMLRenderer`
- `generate_weekly_report.py` — add HTML rendering + Teams posting after narrative save
- `.github/workflows/scheduled-build.yml` — add `TEAMS_WEBHOOK_URL` secret, image copy step
- `docs/style.css` — add narrative article styles

### Copy
- `weekly_report/reidars_rapport_2.png` → `docs/reidars_rapport_2.png`

## Critical Constraints

- **Feature flag OFF by default.** The `--notify-teams` flag must be explicitly passed to enable Teams posting. The GitHub Actions workflow is shipped WITHOUT this flag — it gets enabled manually after verification.
- **No live webhook posts during development.** All Teams notification code must be developed and tested with mocked HTTP calls only.
- **Non-fatal integration.** Both HTML rendering and Teams posting must be wrapped in try/except — failures log warnings but don't affect the pipeline exit code.
- **Existing skip-existing behavior prevents duplicates.** If the narrative already exists, the entire post-narrative block is skipped.

## Success Criteria

- `python -m ruff check .` — no lint issues
- `python -m mypy fpl/ --ignore-missing-imports` — types OK
- `python -m pytest` — all tests pass
- Narrative HTML renders correctly with dark theme, hero image, navigation, article body
- Teams adaptive card has correct structure with teaser and action URL
- Pipeline integration is non-fatal (failures don't break the build)

---

## Tasks

The task list below drives autonomous agent execution. Each task must be:
- **Atomic**: Completable in one agent session without context overflow
- **Verifiable**: Has clear acceptance criteria an agent can test
- **Ordered**: Respects dependencies (earlier tasks don't depend on later ones)

```json
[
  {
    "id": 1,
    "category": "setup",
    "title": "Add markdown dependency and copy hero image to docs",
    "description": "Add `markdown` to requirements.txt (after the existing `rich` entry). Copy `weekly_report/reidars_rapport_2.png` to `docs/reidars_rapport_2.png` (the hero image for narrative pages, must be in docs/ for GitHub Pages). Verify the image file exists in docs/ after copy. Install the updated requirements in the venv.",
    "acceptance_criteria": [
      "requirements.txt contains `markdown` as a dependency",
      "docs/reidars_rapport_2.png exists and is a valid PNG file (same size as weekly_report/reidars_rapport_2.png)",
      "pip install -r requirements.txt succeeds with markdown installed",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": true
  },
  {
    "id": 2,
    "category": "ui",
    "title": "Create narrative article template and styles",
    "description": "Create `templates/narrative.html` extending `base.html`. The template receives these context variables: `title` (str, the narrative heading), `subtitle` (str, e.g. 'Runde 27'), `body_html` (str, rendered HTML from markdown), `hero_image` (str, image filename), `league_id` (str), `league_name` (str), `season` (str). Template structure: (1) Hero image section with `reidars_rapport_2.png`. (2) Title block with `title` in Sora font and `subtitle` below it. (3) Navigation bar with 3 links: Tabell (league_standings_{league_id}.html), Rundehistorikk (league_gameweek_history_{league_id}.html), Poengutvikling (ranking_progression_{league_id}.html). (4) Article body in a centered column (~720px max-width) with the `body_html` content rendered as rich typography. (5) Footer with league name and season. Add narrative-specific CSS to `docs/style.css`: article container (max-width 720px, centered, readable line-height ~1.7), hero image (full-width, max-height ~400px, object-fit cover), navigation bar (horizontal links, styled as pills/buttons), article typography (h2 subheadings styled, blockquotes as pull quotes, paragraph spacing). Use the existing dark theme colors (#00143C background, #fff text, #3E7DEE accent, Inter/Sora fonts). Add responsive styles for mobile (max-width: 768px).",
    "acceptance_criteria": [
      "templates/narrative.html exists and extends base.html",
      "Template uses {% block title %}, {% block body %} from base.html",
      "Hero image section renders with the hero_image variable",
      "Title and subtitle are displayed prominently with Sora font",
      "Navigation bar has 3 links: Tabell, Rundehistorikk, Poengutvikling with correct href patterns",
      "Article body renders body_html in a centered ~720px column",
      "Footer shows league name and season",
      "docs/style.css has new narrative-specific styles (prefixed with .narrative- or scoped to article element)",
      "Narrative styles include hero image, nav bar, article typography, and responsive rules",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": true
  },
  {
    "id": 3,
    "category": "feature",
    "title": "Create NarrativeHTMLRenderer class",
    "description": "Create `fpl/narrative_html_renderer.py` with a `NarrativeHTMLRenderer` class. Constructor takes `template_dir` (str, default 'templates') and `output_dir` (str, default 'docs'). Sets up a Jinja2 Environment with FileSystemLoader (same pattern as LeagueTemplateRenderer). Methods: (1) `render(self, narrative_md: str, league_id: str, league_name: str, season: str, event_id: int) -> Path` — Extracts title from the first `# ` line in the markdown (fallback: 'Reidars Rapport'). Removes the title line and any `![...]()` image lines from the markdown before rendering. Converts remaining markdown to HTML using the `markdown` library (with 'extra' extension for things like fenced code blocks). Renders the `narrative.html` template with context: title, subtitle='Runde {event_id}', body_html, hero_image='reidars_rapport_2.png', league_id, league_name, season. Writes output to `{output_dir}/reidars_rapport_{league_id}_gw{event_id}.html`. Returns the output Path. (2) `get_github_pages_url(league_id: str, event_id: int) -> str` (static method) — Returns `https://torkiljohnsen.github.io/live_fpl_league/reidars_rapport_{league_id}_gw{event_id}.html`. Add `NarrativeHTMLRenderer` to `fpl/__init__.py` imports and `__all__`.",
    "acceptance_criteria": [
      "fpl/narrative_html_renderer.py exists with NarrativeHTMLRenderer class",
      "Constructor creates Jinja2 Environment with FileSystemLoader",
      "render() extracts title from first # heading in markdown",
      "render() strips title line and image lines before markdown conversion",
      "render() converts markdown to HTML using the markdown library with 'extra' extension",
      "render() writes HTML to docs/reidars_rapport_{league_id}_gw{event_id}.html",
      "render() returns the output Path",
      "get_github_pages_url() returns correct GitHub Pages URL",
      "NarrativeHTMLRenderer exported in fpl/__init__.py and __all__",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": true
  },
  {
    "id": 4,
    "category": "test",
    "title": "Tests for NarrativeHTMLRenderer",
    "description": "Create `tests/fpl_tests/test_narrative_html_renderer.py`. Test the NarrativeHTMLRenderer class using tmp_path for output. Tests should cover: (1) render() creates the correct output file at the expected path. (2) render() extracts title from `# Heading` line correctly. (3) render() uses fallback title when no # heading exists. (4) render() strips image lines (`![...]()`) from the markdown body. (5) render() converts markdown to HTML (verify bold, subheadings, paragraphs are rendered). (6) Output HTML contains the title, subtitle, navigation links, and article body. (7) Output HTML includes hero image reference. (8) get_github_pages_url() returns correct URL format. (9) render() creates parent directories if they don't exist. Use a sample narrative markdown string based on the real GW27 format (# heading, ![image], paragraphs with ## subheadings and **bold**). The template_dir should point to the real templates/ directory so the actual template is tested.",
    "acceptance_criteria": [
      "tests/fpl_tests/test_narrative_html_renderer.py exists",
      "Test for correct output file path creation",
      "Test for title extraction from # heading",
      "Test for fallback title when no heading exists",
      "Test for image line stripping",
      "Test for markdown-to-HTML conversion (bold, subheadings, paragraphs)",
      "Test that output HTML contains title, subtitle, nav links, article body",
      "Test for get_github_pages_url() format",
      "Test for directory creation",
      "All tests pass: python -m pytest tests/fpl_tests/test_narrative_html_renderer.py"
    ],
    "passes": true
  },
  {
    "id": 5,
    "category": "feature",
    "title": "Create Teams notification module",
    "description": "Create `fpl/teams_notification.py` with three functions. (1) `extract_teaser(narrative: str, max_length: int = 300) -> str` — Split on `\\n\\n`, skip lines starting with `# ` or `![`, take first remaining paragraph, strip `**` bold markers, truncate at max_length on word boundary and append `...` if truncated. Returns the teaser string. (2) `build_adaptive_card(gameweek: int, teaser: str, narrative_url: str, image_url: str) -> dict` — Build the full Adaptive Card payload dict matching the schema in the PRD: type='message', attachments array with contentType='application/vnd.microsoft.card.adaptive', content with $schema, type=AdaptiveCard, version=1.4, body with Image (url=image_url, size=stretch), two TextBlocks (title 'Reidars Rapport — Runde {gameweek}' with weight=bolder/size=large/wrap=true, and teaser with wrap=true/size=medium), actions with Action.OpenUrl (title='Les hele Reidars Rapport', url=narrative_url). (3) `post_to_teams(webhook_url: str, gameweek: int, narrative: str, narrative_url: str, image_url: str) -> bool` — Calls extract_teaser() and build_adaptive_card(), then POSTs the card JSON to webhook_url using requests.post() with Content-Type application/json. Returns True on success (HTTP 200-299), False on any failure. Catches ALL exceptions, logs warnings via print() to stderr, never raises. Import only requests and __future__ annotations.",
    "acceptance_criteria": [
      "fpl/teams_notification.py exists with extract_teaser, build_adaptive_card, post_to_teams",
      "extract_teaser() skips title and image lines",
      "extract_teaser() strips ** bold markers",
      "extract_teaser() truncates on word boundary at max_length and appends ...",
      "extract_teaser() returns full paragraph if under max_length (no ...)",
      "build_adaptive_card() returns correct Adaptive Card structure matching PRD schema exactly",
      "build_adaptive_card() card version is 1.4",
      "post_to_teams() returns True on successful HTTP response",
      "post_to_teams() returns False and logs warning on HTTP error",
      "post_to_teams() returns False and logs warning on any exception (never raises)",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": true
  },
  {
    "id": 6,
    "category": "test",
    "title": "Tests for Teams notification module",
    "description": "Create `tests/fpl_tests/test_teams_notification.py`. Test all three functions. For extract_teaser(): (1) Basic extraction from a multi-paragraph narrative. (2) Skips # title line. (3) Skips ![image]() line. (4) Strips ** bold markers. (5) Truncates long paragraph at word boundary with '...'. (6) Returns full text without '...' when under max_length. (7) Handles narrative with only title and image (returns empty or first real paragraph). For build_adaptive_card(): (8) Returns dict with correct top-level structure (type=message, attachments array). (9) Card content has correct $schema, type, version=1.4. (10) Body has Image, two TextBlocks with correct properties. (11) Actions has Action.OpenUrl with correct title and URL. For post_to_teams(): (12) Returns True on HTTP 200 (mock requests.post). (13) Returns False on HTTP 400 (mock requests.post). (14) Returns False on requests.RequestException (mock requests.post to raise). (15) Never raises — all exceptions caught. ALL tests must mock requests.post — NO real HTTP calls.",
    "acceptance_criteria": [
      "tests/fpl_tests/test_teams_notification.py exists",
      "extract_teaser() basic extraction tested",
      "extract_teaser() title and image line skipping tested",
      "extract_teaser() bold marker stripping tested",
      "extract_teaser() truncation with word boundary tested",
      "extract_teaser() no truncation when under max_length tested",
      "build_adaptive_card() structure validated (type, attachments, card schema, version)",
      "build_adaptive_card() body elements validated (Image, TextBlocks, Actions)",
      "post_to_teams() success case tested with mocked HTTP 200",
      "post_to_teams() failure cases tested (HTTP error, exception) — returns False, never raises",
      "No real HTTP calls — all requests.post calls are mocked",
      "All tests pass: python -m pytest tests/fpl_tests/test_teams_notification.py"
    ],
    "passes": true
  },
  {
    "id": 7,
    "category": "feature",
    "title": "Pipeline integration and GitHub Actions update",
    "description": "Modify `generate_weekly_report.py`: (A) Add a new CLI flag `--notify-teams` (action='store_true', default False) with help text: 'Post Teams notification after narrative generation. Requires TEAMS_WEBHOOK_URL env var.' This is a feature flag — OFF by default. (B) After the narrative is saved (the `print(f'Narrative saved: {narrative_path}')` line inside the `if args.narrative and not narrative_exists:` block), add two new steps in SEPARATE try/except blocks. (1) HTML rendering: Import NarrativeHTMLRenderer from fpl. Create renderer instance. Read the narrative file content. Call renderer.render() with narrative content, league_id (args.league_id), league_name, season (result['meta']['season']), event_id. Print the output path. (2) Teams notification: Import post_to_teams and NarrativeHTMLRenderer (for URL). Only execute if `args.notify_teams` is True. Read TEAMS_WEBHOOK_URL from os.environ. If the env var is set, call post_to_teams() with webhook_url, event_id, narrative content, narrative URL (from get_github_pages_url), and image URL (GitHub Pages base + 'reidars_rapport_2.png'). Print success/failure. If TEAMS_WEBHOOK_URL is not set, print a warning that the env var is missing. Both blocks must catch Exception, print warning to stderr, and continue — never break the pipeline. (C) Update `.github/workflows/scheduled-build.yml`: (1) Add `TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}` to the 'Generate weekly report and narrative' step's env block (alongside ANTHROPIC_API_KEY). (2) Add a new step before 'Commit and push changes' that copies the hero image: `cp -n weekly_report/reidars_rapport_2.png docs/ 2>/dev/null || true` (idempotent, no-clobber). (3) IMPORTANT: Do NOT add --notify-teams to the workflow command. The flag stays OFF until manually enabled after verification.",
    "acceptance_criteria": [
      "generate_weekly_report.py has --notify-teams CLI flag (store_true, default False)",
      "generate_weekly_report.py imports NarrativeHTMLRenderer and post_to_teams",
      "HTML rendering step added after narrative save, in its own try/except",
      "HTML rendering step creates NarrativeHTMLRenderer and calls render()",
      "Teams notification step added after HTML rendering, in its own try/except",
      "Teams notification only fires when BOTH args.notify_teams is True AND TEAMS_WEBHOOK_URL env var is set",
      "Both steps are non-fatal (catch Exception, print warning, continue)",
      "scheduled-build.yml has TEAMS_WEBHOOK_URL in report step's env block",
      "scheduled-build.yml has hero image copy step (cp -n, idempotent)",
      "scheduled-build.yml does NOT pass --notify-teams flag (feature flag is OFF)",
      "Ruff clean, mypy clean, all tests pass"
    ],
    "passes": false
  }
]
```

---

## Agent Instructions

1. Read `prd/reidar-improvements-activity.md` to understand current state
2. Find the next task where `"passes": false`
3. Complete all acceptance criteria for that task
4. Verify the feature works (run tests, check manually)
5. Update the task to `"passes": true`
6. Log completion in `prd/reidar-improvements-activity.md`
7. Commit changes with descriptive message

**Critical:** Only modify the `passes` field. Never remove, edit, or reorder tasks.

**Before committing any task**, follow the workflow from AGENTS.md:
```bash
source venv/Scripts/activate
python -m ruff check --fix .
python -m mypy fpl/ --ignore-missing-imports
python -m pytest
```

**Reference docs:**
- `AGENTS.md` — Project conventions, testing patterns, code quality rules
- `fpl/AGENTS.md` — Module documentation
- `templates/AGENTS.md` — Template variables reference
- `docs/style.css` — Existing dark theme styles
- `templates/base.html` — Base template structure
- `fpl/league_template_renderer.py` — Reference for Jinja2 Environment setup pattern
- `weekly_report/narratives/1638989/2025-26/gw27.md` — Example narrative markdown format

**GitHub Pages base URL:** `https://torkiljohnsen.github.io/live_fpl_league/`
