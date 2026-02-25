# Dynamic Articles — Product Requirements Document

## Overview

Replace the Python-based `NarrativeHTMLRenderer` (which pre-renders Markdown to static HTML) with a client-side JavaScript approach. A single HTML page uses [marked.js](https://marked.js.org/) to fetch and render `.md` narrative files on the fly. This eliminates the server-side rendering step, simplifies the pipeline, and lets us update narratives by just editing Markdown files.

## Target Users

- **League members** — read Reidars Rapport articles via shared links from Teams notifications
- **Pipeline maintainers** — simpler deployment: generate `.md`, commit, done

## Core Requirements

1. Single `docs/reidars_rapport.html` page that dynamically renders any gameweek narrative from Markdown
2. Gameweek selected via query parameter: `?gw=25`
3. Arrow navigation in both the header AND footer for previous/next gameweek (GW 1–38), so users can navigate after reading an article
4. Friendly "not found" state when a gameweek's narrative doesn't exist yet, featuring a Reidar image and a humorous Norwegian message
5. Preserve the existing narrative design exactly — reuse the HTML structure from `templates/narrative.html` and all CSS from `docs/style.css` (hero image, article typography, responsive design). The JS page must produce the same visual result as the current Python-rendered pages.
6. Narrative generator writes `.md` files directly to `docs/narratives/` (single source of truth)
7. Remove `NarrativeHTMLRenderer` class, its tests, and the `narrative.html` Jinja2 template
8. Organize images into `docs/assets/` to declutter the docs root
9. Update Teams notification URL to point to the new dynamic page format

## Tech Stack

- **Markdown rendering**: [marked.js](https://cdn.jsdelivr.net/npm/marked/marked.min.js) via CDN (client-side)
- **Hosting**: GitHub Pages (static files only, no build step)
- **Styling**: Existing `docs/style.css` with narrative-specific classes
- **Pipeline**: Python (existing `generate_weekly_report.py`)

## Architecture

```
User visits: reidars_rapport.html?gw=25
  → JS reads ?gw param
  → fetch("narratives/2025-26/1638989/gw25.md")
  → If 200: extract title from "# ...", render body with marked.js
  → If 404: show friendly "not played yet" page with Reidar image
  → Navigation arrows link to ?gw=24 and ?gw=26
```

**Hardcoded values** (for now):
- League ID: `1638989` (Sinkaberg administrasjon)
- Season: `2025-26`
- Gameweeks: 1–38

**File structure after completion:**
```
docs/
├── assets/                          ← NEW: all images moved here
│   ├── reidars_rapport_1.png        ← Four report images, rotated by GW number
│   ├── reidars_rapport_2.png
│   ├── reidars_rapport_3.png
│   ├── reidars_rapport_4.png
│   ├── reidar_404.png               ← Exists in docs/ root, move here in task 1
│   ├── trophy.png
│   ├── first_place.png
│   ├── second_place.png
│   ├── third_place.png
│   ├── alarm.png
│   └── The Duck liten.png
├── narratives/
│   └── 2025-26/1638989/
│       ├── gw27.md                  ← NEW: .md files served directly
│       ├── gw28.md
│       └── ...
├── reidars_rapport.html             ← NEW: dynamic article page
├── style.css                        ← Updated with 404 state styles
├── index.html
└── *.html                           ← Existing dashboard pages
```

## Success Criteria

- Visiting `reidars_rapport.html?gw=27` renders the GW27 narrative with full styling (hero image, title, article body, navigation)
- Prev/next arrows in both header and footer navigate between gameweeks
- Visiting a non-existent gameweek shows the friendly 404 state
- Links shared on Teams still work (updated URL format)
- The Python pipeline no longer renders HTML — it only generates `.md` files
- `NarrativeHTMLRenderer` class and `narrative.html` template are removed (design preserved in the JS page)
- All images live in `docs/assets/`, all references updated

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
    "title": "Move images to docs/assets/",
    "description": "Create docs/assets/ directory. Move all image files from docs/ root into docs/assets/: reidars_rapport_1.png, reidars_rapport_2.png, reidars_rapport_3.png, reidars_rapport_4.png, reidar_404.png, trophy.png, first_place.png, second_place.png, third_place.png, alarm.png, 'The Duck liten.png'. The four reidars_rapport_N.png images currently exist in weekly_report/ — copy them to docs/assets/. Update all references to these images in: docs/style.css, docs/index.html, docs/*.html (standings, history, progression pages), templates/*.html (Jinja2 templates that reference image paths), generate_weekly_report.py (the image_url for Teams notification). Use grep to find all references before updating. Do NOT move or modify files in docs/narratives/.",
    "acceptance_criteria": [
      "docs/assets/ directory exists with all image files moved from docs/ root",
      "All four reidars_rapport_{1-4}.png images are present in docs/assets/",
      "No image files remain in docs/ root (only .html, .css, narratives/, assets/)",
      "All HTML files in docs/ render correctly with updated image paths",
      "Templates reference updated paths (e.g., assets/trophy.png instead of trophy.png)",
      "grep -r 'reidars_rapport_2.png' shows only docs/assets/ references (no broken paths)",
      "Teams notification image URL updated to include /assets/ in the path"
    ],
    "passes": true
  },
  {
    "id": 2,
    "category": "feature",
    "title": "Create dynamic article page with marked.js",
    "description": "Create docs/reidars_rapport.html — a self-contained HTML page that uses marked.js (via CDN: https://cdn.jsdelivr.net/npm/marked/marked.min.js) to render Markdown narratives client-side. IMPORTANT: The page must replicate the exact HTML structure from templates/narrative.html so the existing CSS renders identically. Read templates/narrative.html and templates/base.html first as your blueprint. The page reads ?gw=N from the query string, fetches narratives/2025-26/1638989/gw{N}.md, extracts the title from the first '# ' heading line, strips the title line and any '![...]()' image lines from the body, renders the remaining Markdown to HTML with marked.parse(), and inserts the result into the page. The page structure must match the existing template: .narrative-page wrapper, .narrative-hero with a dynamically selected hero image, .narrative-header with kicker (league name), title, subtitle ('Runde N'), .narrative-nav with links to Tabell/Rundehistorikk/Poengutvikling, .narrative-article for the rendered body, and .narrative-footer. **Hero image rotation**: The hero image must rotate through four images based on the gameweek number: GW1 → reidars_rapport_1.png, GW2 → reidars_rapport_2.png, GW3 → reidars_rapport_3.png, GW4 → reidars_rapport_4.png, GW5 → reidars_rapport_1.png (cycling with modulo). Formula: image_number = ((gw - 1) % 4) + 1, then use assets/reidars_rapport_{image_number}.png. Link style.css and Google Fonts (Inter, Sora, DM Serif Display, Source Serif 4) in the head. If no ?gw param is provided, default to a landing state or the latest available gameweek. Hardcode league_id=1638989, season=2025-26.",
    "acceptance_criteria": [
      "docs/reidars_rapport.html exists and loads marked.js from CDN",
      "Visiting ?gw=27 fetches narratives/2025-26/1638989/gw27.md and renders the article",
      "Title is extracted from the first '# ' line and displayed in .narrative-header h1",
      "Subtitle shows 'Runde N' matching the gameweek number",
      "Image lines (![...]()) are stripped from the rendered body",
      "Article body renders inside .narrative-article with correct Markdown-to-HTML conversion",
      "Hero image rotates based on gameweek: GW1 uses reidars_rapport_1.png, GW2 uses _2, GW3 uses _3, GW4 uses _4, GW5 uses _1 again",
      "Hero image, navigation links, and footer are all present and use existing CSS classes",
      "Page uses the existing narrative CSS variables (--nr-red, --nr-gold, --nr-text, --nr-muted)"
    ],
    "passes": true
  },
  {
    "id": 3,
    "category": "feature",
    "title": "Add gameweek navigation arrows in header and footer",
    "description": "Add prev/next gameweek navigation to BOTH the header and footer of docs/reidars_rapport.html. In the header: display left arrow (←) and right arrow (→) flanking the subtitle or a dedicated nav row within .narrative-header. In the footer: add a matching navigation row inside .narrative-footer so users can navigate to the next/previous gameweek after finishing an article without scrolling back up. Left arrow links to ?gw={N-1}, right arrow links to ?gw={N+1}. Hide the left arrow when gw=1, hide the right arrow when gw=38. Style the arrows to be clearly clickable, using the existing narrative color scheme (--nr-gold or --nr-text for idle, --nr-red or white for hover). The arrows should be large enough to tap on mobile. Consider using ‹ › or « » or simple SVG arrows for a clean look. The footer nav can also include labels like '← Runde 24' and 'Runde 26 →' for clarity. Add CSS for the navigation arrows in docs/style.css.",
    "acceptance_criteria": [
      "Left and right navigation arrows are visible in the article header",
      "Left and right navigation arrows are visible in the article footer",
      "Footer navigation includes labels (e.g., '← Runde 24' / 'Runde 26 →')",
      "Clicking left arrow navigates to ?gw={N-1}",
      "Clicking right arrow navigates to ?gw={N+1}",
      "Left arrow is hidden when gw=1",
      "Right arrow is hidden when gw=38",
      "Arrows are styled consistently with the narrative design (colors, hover states)",
      "Arrows are large enough for mobile tap targets (min 44px)",
      "Navigation works correctly at boundary gameweeks (1 and 38)"
    ],
    "passes": true
  },
  {
    "id": 4,
    "category": "feature",
    "title": "Add friendly 404 state for missing narratives",
    "description": "When fetching a gameweek's .md file returns a non-OK response (404), display a friendly 'not found' state instead of a blank page. The dedicated 404 image exists at assets/reidar_404.png (moved there by task 1). Show the Reidar image (assets/reidar_404.png with fallback to assets/reidars_rapport_2.png), a humorous Norwegian heading (e.g., 'Denne runden er ikke spilt ennå'), and a short witty body text in Reidar's voice (e.g., 'Reidar ser på deg som om du har brukt triple captain på en keeper. Kom tilbake når runden er ferdig.'). The navigation arrows should still work so users can navigate to other gameweeks. Style the 404 state to be centered and visually appealing using the existing narrative design system. Add a CSS class .narrative-not-found for the 404 state with appropriate styling in docs/style.css. The 404 image should handle the fallback gracefully with an onerror handler.",
    "acceptance_criteria": [
      "Visiting ?gw=99 (non-existent) shows the friendly 404 state instead of a blank page",
      "404 state displays an image (reidar_404.png with fallback to reidars_rapport_2.png)",
      "404 state shows a humorous Norwegian heading",
      "404 state includes witty body text in Reidar's voice",
      "Navigation arrows still function on the 404 page",
      "404 state is styled with .narrative-not-found class in style.css",
      "Image fallback works: if reidar_404.png doesn't exist, reidars_rapport_2.png is shown",
      "The 404 state looks good on both desktop and mobile"
    ],
    "passes": true
  },
  {
    "id": 5,
    "category": "refactor",
    "title": "Update narrative generator to write .md to docs/",
    "description": "Change the narrative output path so .md files are written directly to docs/narratives/{league_id}/{season}/gw{N}.md instead of weekly_report/narratives/{league_id}/{season}/gw{N}.md. This involves updating fpl/narrative_generator.py (the save_narrative method's path construction), and updating the --skip-existing check in generate_weekly_report.py (which currently looks for narrative files under weekly_report/narratives/). The directory structure under docs/narratives/ should use {league_id}/{season}/ order (matching the existing docs/narratives/2025-26/1638989/ structure but NOTE: the current structure is season/league_id — verify and match whichever is already deployed). Also update the previous_narrative path resolution in the pipeline. Existing .md files in weekly_report/narratives/ can remain as historical artifacts — do not delete them.",
    "acceptance_criteria": [
      "save_narrative() writes .md files to docs/narratives/ path",
      "The --skip-existing check looks for narrative .md files in the new docs/narratives/ location",
      "Previous narrative path resolution still works for narrative continuity",
      "Directory structure matches what the JS page expects (narratives/{season}/{league_id}/gw{N}.md)",
      "No existing files are deleted from weekly_report/narratives/",
      "Pipeline runs successfully with the new paths (no import or path errors)"
    ],
    "passes": true
  },
  {
    "id": 6,
    "category": "refactor",
    "title": "Remove NarrativeHTMLRenderer and update pipeline",
    "description": "Remove the NarrativeHTMLRenderer class and all associated code. NOTE: By this point, the dynamic JS page (task 2) already replicates the exact HTML structure and design from the template, so the template is safe to remove. Steps: (1) Delete fpl/narrative_html_renderer.py, (2) Delete tests/fpl_tests/test_narrative_html_renderer.py, (3) Delete templates/narrative.html (the Jinja2 template — its design is preserved in docs/reidars_rapport.html), (4) Remove the 'markdown' dependency from requirements.txt (no longer needed server-side), (5) Remove the HTML rendering block from generate_weekly_report.py (the try/except block that calls renderer.render()), (6) Remove the import of NarrativeHTMLRenderer from generate_weekly_report.py, (7) Update the Teams notification URL construction — instead of using NarrativeHTMLRenderer.get_github_pages_url(), construct the URL directly as 'https://torkiljohnsen.github.io/live_fpl_league/reidars_rapport.html?gw={event_id}', (8) Update the Teams notification image_url to use the new assets/ path with image rotation: image_number = ((event_id - 1) % 4) + 1, then use assets/reidars_rapport_{image_number}.png. Delete the pre-rendered HTML file docs/narratives/2025-26/1638989/reidars_rapport_gw27.html as it's no longer needed. Run ruff, mypy, and pytest to verify nothing is broken.",
    "acceptance_criteria": [
      "fpl/narrative_html_renderer.py is deleted",
      "tests/fpl_tests/test_narrative_html_renderer.py is deleted",
      "templates/narrative.html is deleted",
      "'markdown' is removed from requirements.txt",
      "generate_weekly_report.py no longer imports or uses NarrativeHTMLRenderer",
      "HTML rendering try/except block is removed from the pipeline",
      "Teams notification URL uses new format: reidars_rapport.html?gw={N}",
      "Teams notification image URL uses assets/ path with gameweek-based rotation (reidars_rapport_{1-4}.png)",
      "docs/narratives/2025-26/1638989/reidars_rapport_gw27.html is deleted",
      "ruff, mypy, and pytest all pass cleanly"
    ],
    "passes": true
  },
  {
    "id": 7,
    "category": "setup",
    "title": "Update GitHub Actions workflow",
    "description": "Update .github/workflows/scheduled-build.yml to reflect the simplified pipeline: (1) The hero image copy step should now copy to docs/assets/ instead of docs/ root, (2) Verify that docs/narratives/ .md files are included in the git add step (they should be, since 'docs/' is already added), (3) Remove any references to narrative HTML rendering if present, (4) Ensure the workflow still commits and pushes .md narrative files in docs/narratives/. Review the full workflow file and make only the changes needed for the new file structure.",
    "acceptance_criteria": [
      "Hero image copy step targets docs/assets/ directory",
      "Workflow git add includes docs/ (which covers docs/narratives/*.md and docs/assets/)",
      "No references to narrative HTML rendering remain in the workflow",
      "Workflow file is valid YAML (no syntax errors)"
    ],
    "passes": true
  }
]
```

---

## Agent Instructions

1. Read `prd/dynamic-articles-activity.md` to understand current state
2. Find the next task where `"passes": false`
3. Complete all acceptance criteria for that task
4. Verify the feature works (run tests, check manually, use browser automation)
5. Update the task to `"passes": true`
6. Log completion in `prd/dynamic-articles-activity.md`
7. Commit changes with descriptive message

**Critical:** Only modify the `passes` field. Never remove, edit, or reorder tasks.
