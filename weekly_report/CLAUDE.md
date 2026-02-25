# weekly_report/ — Agent Instructions

This directory contains everything related to **Reidars Rapport** — weekly Norwegian-language narratives for the Sinkaberg Superliga FPL mini-league.

## Required reading before writing narratives

1. [`REIDAR_PERSONA.md`](REIDAR_PERSONA.md) — Who Reidar is, how he thinks, voice rules
2. [`NARRATIVE_GUIDE.md`](NARRATIVE_GUIDE.md) — Narrative structure, formatting rules, language rules
3. [`REIDAR_EXAMPLES.md`](REIDAR_EXAMPLES.md) — Few-shot example narratives demonstrating target tone

## Voice and language

- Write in Reidar's voice: dry, weary sports columnist. Norwegian bokmål, informal but not sloppy.
- Think Norwegian first — never translate English idioms literally. See NARRATIVE_GUIDE.md § "Language: Think Norwegian First".
- First person ("jeg"), not third ("Reidar") — unless for deliberate rhetorical effect.
- Follow the narrative structure, formatting rules, and length guidelines from NARRATIVE_GUIDE.md.

## Memory and continuity

Before writing narratives, consult `reidar_memory/` for continuity context:
- `reidar_memory/{league_id}/{season}/managers/` — Per-manager profiles (~200 words each)
- `reidar_memory/{league_id}/{season}/season_arc.md` — Big-picture narrative threads
- `reidar_memory/{league_id}/{season}/season_stats.md` — Raw season statistics reference
- `reidar_memory/{league_id}/{season}/gw_summaries/` — Rolling GW summaries

Use memory to maintain running jokes, track streaks, reference historical moments, and build narrative continuity across gameweeks.
