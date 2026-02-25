# Dynamic Articles — Activity Log

## Current Status
**Last Updated:** 2026-02-25
**Tasks Completed:** 7 / 7
**Current Task:** All tasks completed

---

## Session Log

### Session 1 — 2026-02-25
**Task:** Task 1 — Move images to docs/assets/
**Status:** completed
**Notes:** Created docs/assets/ directory. Moved all 8 images from docs/ root to docs/assets/ via git mv. Copied all 4 reidars_rapport_{1-4}.png hero images from weekly_report/ to docs/assets/. Updated all image references in: templates (league_standings.html, league_gameweek_history.html), CSS (style.css), Python (narrative_html_renderer.py, generate_weekly_report.py), GitHub Actions workflow (scheduled-build.yml), all generated HTML files in docs/, narrative HTML file, and test assertions. All 275 tests pass, mypy clean.

### Session 2 — 2026-02-25
**Task:** Task 2 — Create dynamic article page with marked.js
**Status:** completed
**Notes:** Created docs/reidars_rapport.html — a self-contained HTML page that uses marked.js via CDN to render Markdown narratives client-side. Replicates the exact HTML structure from templates/narrative.html and templates/base.html: .narrative-page wrapper, .narrative-hero with dynamic hero image, .narrative-header with kicker/title/subtitle/byline, .narrative-article for rendered body, .narrative-nav with dashboard links, and .narrative-footer. Reads ?gw=N from query string, fetches narratives/2025-26/1638989/gw{N}.md, extracts title from first # heading, strips image lines, renders body with marked.parse(). Hero image rotates via ((gw-1)%4)+1 formula. Includes landing state for missing ?gw param and basic 404 handling. All 275 tests pass.

### Session 3 — 2026-02-25
**Task:** Task 3 — Add gameweek navigation arrows in header and footer
**Status:** completed
**Notes:** Added prev/next gameweek navigation to both header and footer of docs/reidars_rapport.html. Header uses « » guillemets flanking the subtitle in a flex container (.narrative-gw-nav). Footer uses labeled links ("« Runde 24" / "Runde 26 »") in a dedicated nav row above the existing dashboard links. JS setupNavigation() sets hrefs to ?gw={N±1} and hides arrows at boundaries (gw=1 hides prev, gw=38 hides next). Landing page hides all navigation. Added CSS for .gw-nav-arrow (header) and .gw-nav-link (footer) with 44px min tap targets, hover states using --nr-accent/--nr-highlight, and responsive adjustments. All 275 tests pass.

### Session 4 — 2026-02-25
**Task:** Task 4 — Add friendly 404 state for missing narratives
**Status:** completed
**Notes:** Enhanced the showNotFound() function in docs/reidars_rapport.html to render a full 404 state with .narrative-not-found container: displays reidar_404.png image (with onerror fallback to reidars_rapport_2.png), humorous Norwegian heading ("Denne runden er ikke spilt ennå"), and witty body text in Reidar's voice. Navigation arrows remain functional since setupNavigation() runs before the fetch. Added .narrative-not-found CSS class to docs/style.css with centered layout, image styling, typography, and responsive mobile adjustments. All 275 tests pass.

### Session 5 — 2026-02-25
**Task:** Task 5 — Update narrative generator to write .md to docs/
**Status:** completed
**Notes:** Changed narrative output path from `{output_dir}/weekly_report/narratives/{league_id}/{season}/gw{N}.md` to `{output_dir}/docs/narratives/{season}/{league_id}/gw{N}.md`, matching the fetch URL used by the client-side reidars_rapport.html page. Updated save_narrative() in fpl/narrative_generator.py, --skip-existing check in generate_weekly_report.py, and previous_narrative path in fpl/weekly_report.py. Also flipped path order from `{league_id}/{season}` to `{season}/{league_id}` to match deployed structure. Updated all corresponding test assertions. Existing files in weekly_report/narratives/ left untouched. All 275 tests pass.

### Session 6 — 2026-02-25
**Task:** Task 6 — Remove NarrativeHTMLRenderer and update pipeline
**Status:** completed
**Notes:** Deleted fpl/narrative_html_renderer.py, tests/fpl_tests/test_narrative_html_renderer.py, templates/narrative.html, and pre-rendered docs/narratives/2025-26/1638989/reidars_rapport_gw27.html. Removed 'markdown' dependency from requirements.txt. Removed NarrativeHTMLRenderer import and HTML rendering try/except block from generate_weekly_report.py. Updated Teams notification URL to use new dynamic page format (reidars_rapport.html?gw={N}) and image URL to use gameweek-based rotation (assets/reidars_rapport_{1-4}.png). Removed NarrativeHTMLRenderer from fpl/__init__.py exports. Updated AGENTS.md, fpl/AGENTS.md, and .claude/commands/rewrite-narrative.md to reflect removal. All 257 tests pass (18 fewer due to deleted renderer tests), mypy clean.

### Session 7 — 2026-02-25
**Task:** Task 7 — Update GitHub Actions workflow
**Status:** completed
**Notes:** Reviewed .github/workflows/scheduled-build.yml against the new file structure. Hero image copy step already targets docs/assets/ (from Task 1). git add docs/ already covers docs/narratives/*.md and docs/assets/. No narrative HTML rendering references present. Removed stale weekly_report/narratives from the git add loop since narratives are now written to docs/narratives/ (Task 5). YAML validated, all 257 tests pass, mypy clean.
