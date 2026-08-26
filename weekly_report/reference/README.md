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

Everything is derived from the official FPL help pages (`/help/rules`, `/help/new`), retrieved 2026-08-26. The FAQ page (`/help/faqs`) is represented only by `fpl_faq_edge_cases.md` — account, league-admin, assist-definition and ICT questions were deliberately dropped.

## Maintenance

- Refresh at season rollover: re-clip the two pages, regenerate the seven files, bump the season in the filenames, and rewrite the "what's new" file from scratch. Add to `docs/SEASON_ROLLOVER.md`.
- Chip windows and deadlines are also in the API (`bootstrap-static.chips`, `events[].deadline_time`); the files are the readable version, the API is the source of truth if they disagree.
- Keep each file under ~800 words. If a file grows past that, split it rather than let it bloat the prompt.
