# Season Rollover Recipe

How to move this project from one FPL season to the next. Written after the
2025-26 → 2026-27 rollover; every step below is one that actually bit.

Budget about an hour. Do it *after* the new season's leagues exist in FPL but
*before* the Gameweek 1 deadline.

---

## 0. Before you start

Find the new league IDs. Open each league in FPL and read the URL:
`https://fantasy.premierleague.com/leagues/<LEAGUE_ID>/standings/c`. Then check
they resolve, and note the exact names:

```bash
python - <<'EOF'
import json, urllib.request
for lid in (848662, 538233):          # ← this season's IDs
    u = f'https://fantasy.premierleague.com/api/leagues-classic/{lid}/standings/'
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    d = json.load(urllib.request.urlopen(r, timeout=30))
    print(lid, repr(d['league']['name']), 'entries', len(d['standings']['results']))
EOF
```

Decide which league is the **report league** — the one Reidar writes about.
Everything narrative-related takes a single league ID.

---

## 1. Reset the gameweek state

**This is the one that silently kills everything.** `.gw_state.json` holds
counters from last season (e.g. `380` fixtures, `38` events). The FPL API
restarts both at zero each season, and the hourly check only fires when the
live count *exceeds* the stored one — so a stale file means the workflow never
does anything, all season, with no error.

```bash
cat > .gw_state.json <<'JSON'
{
  "finished_fixtures": 0,
  "finished_events": 0
}
JSON
```

---

## 2. Add the season to `leagues.json`

Newest season first. This drives the season grouping on `docs/index.html`, so
last season's dashboards stay published as an archive instead of vanishing or
sitting confusingly alongside the new ones.

```json
{
  "seasons": [
    {
      "season": "2026-27",
      "current": true,
      "report_league": "848662",
      "leagues": [
        { "id": "848662", "name": "Sinkaberg The Office" },
        { "id": "538233", "name": "Sinkaberg Superliga" }
      ]
    },
    { "season": "2025-26", "...": "leave previous seasons in place" }
  ]
}
```

Season strings are *derived from the FPL API*, not configured — see
`get_season_from_bootstrap()`. The string here must match the format it
produces (`2026-27`), or the index won't match dashboards to seasons.

---

## 3. Update the workflow

In `.github/workflows/scheduled-build.yml`:

- Re-enable the `schedule:` block if it was commented out for the off-season.
- Dashboards take **both** leagues: `generate_html.py -l 848662,538233`
- Report, narrative and notification take **only the report league**:
  `generate_weekly_report.py -l 848662`, likewise `generate_narrative.py` and
  `notify_teams.py`
- Update `LEAGUE_ID:` in the "Wait for GitHub Pages deployment" step.

Sanity check that no old IDs survive:

```bash
grep -n "1638989\|1639886" .github/workflows/*.yml   # last season's IDs — expect no output
```

---

## 4. Update the article page

`docs/reidars_rapport.html` is hand-maintained (it is the one non-generated
file in `docs/`). Near the top of its script block:

```js
var SEASONS = {
    '2026-27': { league: '848662', name: 'Sinkaberg The Office' },
    '2025-26': { league: '1638989', name: 'Sinkaberg administrasjon' }
};
var CURRENT_SEASON = '2026-27';
```

Add the new season, keep the old entries. `?season=2025-26&gw=30` then still
serves archived narratives; the current season needs no parameter.

---

## 5. Update the CLI defaults

`FPL_LEAGUE_ID` at the top of `generate_html.py`, `generate_weekly_report.py`,
`generate_narrative.py` and `notify_teams.py` — set to the report league. Only
affects local runs; CI passes IDs explicitly.

---

## 6. Seed Reidar's memory (optional, recommended)

Without this Reidar starts the season with amnesia: no running jokes, no
grudges, no idea who won last year. Memory lives at
`weekly_report/reidar_memory/{league_id}/{season}/`.

```bash
mkdir -p weekly_report/reidar_memory/848662/2026-27/{managers,gameweeks}
```

Then, for each manager who is *still in the league*, write
`managers/{FirstName}.md` carrying last season's character forward: team name,
final position and points, notable moments, running jokes — with current form
reset to "Ny sesong — ingen runder spilt ennå." Drop anyone who left. New
managers need nothing; the memory updater creates their profiles on the first
run, because the prompt lists every manager in the report.

Write a `season_arc.md` covering last season's final table, records that still
stand, and the storylines to watch. Do **not** copy `gameweeks/` or
`season_stats.md` — they are last season's, and a stale `season_stats.md` will
have Reidar quoting the wrong league name.

Check it loads:

```bash
python -c "
from fpl.reidar_memory import ReidarMemory
print(len(ReidarMemory('.', '848662', '2026-27').get_prompt_context(1).split()), 'words')"
```

Expect roughly 1000–1500 words. Zero means the path is wrong.

---

## 7. Generate and check

```bash
python generate_html.py -l 848662,538233 --cache-dir .fpl_cache
python generate_index.py
```

**Expect breakage on pre-season data.** Before the first gameweek is scored the
API returns `null` for `overall_rank`, `rank`, `percentile_rank` and friends.
In 2026-27 this crashed all six pages via `format_rank_compact(None)`. Anything
reading those fields must tolerate `None` — if a new crash appears here, that's
almost certainly the cause.

Open `docs/index.html` and confirm the new season is on top with the previous
one archived below.

---

## 8. Commit, push, verify

```bash
python -m pytest tests/ -q && python -m mypy fpl/ --ignore-missing-imports
git add -A && git commit && git push origin dev
gh workflow run scheduled-build.yml --ref dev
gh run watch <run-id> --exit-status
```

A manual dispatch before the first gameweek should refresh dashboards, **skip**
the report steps (`has_finished_gameweek=false`), push, and request a Pages
build. Then confirm the site:

```bash
gh api repos/:owner/:repo/pages/builds/latest --jq .status   # → "built"
```

---

## Gotchas worth remembering

**Gameweek lock time (new in 2026/27).** FPL locks gameweek points at **09:00
UK on the day after the gameweek's final match** — previously one hour after
the final whistle. The extension lets Opta's six-hour post-match review feed
into BPS and Defensive Contribution points. Consequences:

- A played fixture keeps `finished: false` for *days*; only
  `finished_provisional` flips at full time. `count_finished_fixtures()`
  counts both, or dashboards would refresh once per gameweek instead of after
  each match.
- The report and narrative wait for `event.finished`, which flips at the lock.
  So Reidar's report now lands the *morning after* the last match, not late the
  same night. Teams notification timing shifts with it.

**Reports for past seasons cannot be rebuilt.** The FPL API only serves the
season currently running — historical picks, transfers and live data are gone.
The committed `weekly_report/reports/{league}/{season}/gw*.json` files are the
only copy. Treat them as archives.

**Regenerating an archived narrative** needs `--season`, since the season is
otherwise taken from the live API, and `--output-dir`, or it overwrites the
published narrative *and* rewrites that season's memory in place:

```bash
python generate_narrative.py -l 1638989 -e 38 --season 2025-26 --output-dir /tmp/preview
```

Easier: run the **Preview Narrative** workflow, which sandboxes all of that and
uploads the result as an artifact:

```bash
gh workflow run preview-narrative.yml -f league_id=848662 -f event=3
```

**Model and token limits** live in `fpl/claude_api.py`. Two calls per gameweek
(narrative ≈33k in / 2k out, memory update ≈25k in / 6k out) — roughly $0.30
per gameweek on `claude-sonnet-5`, $10–12 for a full season. `MAX_TOKENS` must
stay generous: the memory update writes every manager profile plus a gameweek
summary and the season arc in one response, and at 4096 it truncated silently,
which froze the 2025-26 season arc at GW27 for eleven gameweeks.

**No PAT needed.** The workflow pushes with the built-in `GITHUB_TOKEN` and
asks for the Pages rebuild explicitly, because pushes made with that token do
not trigger `pages-build-deployment`. Only `ANTHROPIC_API_KEY` and
`TEAMS_WEBHOOK_URL` need to exist as repository secrets.

---

## Off-season

When the season ends, comment out the two `schedule:` lines in
`scheduled-build.yml`. Leave everything else — next season starts at step 0.
