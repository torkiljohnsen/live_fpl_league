# Dynamic Articles — Activity Log

## Current Status
**Last Updated:** 2026-02-25
**Tasks Completed:** 5 / 7
**Current Task:** Task 5 completed

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
