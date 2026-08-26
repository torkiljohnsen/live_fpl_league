# Reidar's reference shelf

Condensed reference material Reidar can be handed **on demand**. None of this is in the system prompt by default; the pipeline includes a file only when the gameweek calls for it, so the standing context stays small. Raw sources are not kept here — only the distilled versions, each with its source URL and retrieval date at the top.

| File | Words | Load when |
|---|---|---|
| `fpl_rules_2026-27.md` | ~700 | GW1 (season preview); a rule decided something — autosub, vice-captain, clean sheet, tie-break |
| `fpl_deadlines_2026-27.md` | ~250 | a look-ahead needs the next deadline(s); midweek or unusual deadline ahead |
| `fpl_chips_2026-27.md` | ~300 | any chip played this gameweek; the GW19 chip reset is near (GW16–19); advice about chips is on the menu |
| `fpl_whats_new_2026-27.md` | ~300 | GW1–3 (Reidar grumbles about the changes); a late bonus/DC revision or the 09:00 lock is the story |
| `fpl_bps_2026-27.md` | ~300 | bonus points decided a round or a captaincy; otherwise never |
| `fpl_faq_edge_cases.md` | ~450 | a DGW/BGW; TC on a non-starter; a Free Hit week; a player subbed on 59 min; four from one club; a player who left the PL; a DC/bonus revision |
| `fpl_strategy_notes.md` | ~450 | a chip window opens or closes; a DGW/BGW or golden gameweek is next; the format is advice-shaped; a manager's chip pattern suggests a plan |
| `league_rules.md` | ~230 | GW1; every golden gameweek (`meta.is_golden` or `meta.next_event.is_golden`) |
| `league_history.md` | ~310 | GW1; GW38; a league record is threatened or broken |

`league_rules.md` and `league_history.md` are hand-maintained by the league, not clipped from anywhere — `league_history.md` gets a new section appended at season end. Everything else is derived from the official FPL help pages (`/help/rules`, `/help/new`), retrieved 2026-08-26. The FAQ page (`/help/faqs`) is represented only by `fpl_faq_edge_cases.md` — account, league-admin, assist-definition and ICT questions were deliberately dropped.

## How it is loaded

`fpl/reference_loader.py` implements the table above. `select_reference_docs(report, event_id, format=...)` is a pure function — no I/O — that reads the report JSON and returns the filenames this gameweek's triggers fired, in priority order (chips, strategy notes, what's new, rules, FAQ, deadlines, BPS). `load_reference_docs(filenames)` then reads them and concatenates them under a `### <title>` heading each, stopping once the ~1500-word budget would be exceeded (dropping the lowest-priority tail, never the first doc). `run_narrative_pipeline()` in `fpl/narrative_generator.py` calls both and appends the result to the user message as `## Oppslagsverk (bare for denne runden)` — only when something triggered, never in the system prompt, so the standing context stays small on a quiet week.

## Maintenance

- Refresh at season rollover: re-clip the two pages, regenerate the seven files, bump the season in the filenames, and rewrite the "what's new" file from scratch. Add to `docs/SEASON_ROLLOVER.md`.
- Chip windows and deadlines are also in the API (`bootstrap-static.chips`, `events[].deadline_time`); the files are the readable version, the API is the source of truth if they disagree.
- Keep each file under ~800 words. If a file grows past that, split it rather than let it bloat the prompt.
