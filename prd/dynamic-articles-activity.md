# Dynamic Articles — Activity Log

## Current Status
**Last Updated:** 2026-02-25
**Tasks Completed:** 2 / 7
**Current Task:** Task 2 completed

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
