# weekly_report/ — Agent Instructions

This directory contains everything related to **Reidars Rapport** — weekly Norwegian-language narratives for the league's FPL mini-league.

## Required reading before writing narratives

1. [`REIDAR_PERSONA.md`](REIDAR_PERSONA.md) — Who Reidar is, how he thinks, voice rules
2. [`NARRATIVE_GUIDE.md`](NARRATIVE_GUIDE.md) — Shape menu, hard constraints, language and format rules
3. [`REIDAR_EXAMPLES.md`](REIDAR_EXAMPLES.md) — Five worked columns in five shapes
4. [`DEVICE_PALETTE.md`](DEVICE_PALETTE.md) — Exact markup for every visual device

These four are the system prompt. [`reference/`](reference/) holds on-demand material (FPL rules, chips, deadlines, league rules and history) that `fpl/reference_loader.py` adds to the *user* message only when a gameweek triggers it — see [`reference/README.md`](reference/README.md).

## Voice and language

- Write in Reidar's voice: dry, weary sports columnist. Norwegian bokmål, informal but not sloppy.
- Think Norwegian first — never translate English idioms literally. See NARRATIVE_GUIDE.md § "Norwegian first".
- First person ("jeg"), not third ("Reidar").
- The hard constraints in NARRATIVE_GUIDE.md are enforced after generation by `fpl/style_lint.py`. Check a draft with `python -m fpl.style_lint <file>`.

## Memory and continuity

Before writing narratives, consult `reidar_memory/` for continuity context:
- `reidar_memory/{league_id}/{season}/managers/` — Per-manager profiles (~200 words each)
- `reidar_memory/{league_id}/{season}/season_arc.md` — Big-picture narrative threads
- `reidar_memory/{league_id}/{season}/gameweeks/` — Rolling GW summaries (`gw{N}.md`)

Use memory to maintain running jokes, track streaks, reference historical moments, and build narrative continuity across gameweeks. All-time records and past seasons live in [`reference/league_history.md`](reference/league_history.md), which survives the season rollover.
