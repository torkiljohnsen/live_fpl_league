# Ligaens egne regler

Hand-maintained house rules for this mini-league (not FPL's own rules — those are in `fpl_rules_2026-27.md`). Source: the league itself. Retrieved 2026-08-26.

## Golden gameweek

Every 4th gameweek is a **golden gameweek**: GW 4, 8, 12, 16, 20, 24, 28, 32, 36. The manager with the highest net score in a golden gameweek wins a **cash prize**. Nothing else about the gameweek changes — the points still count normally toward the season table.

This is the league's one genuine strategic quirk: a chip saved for a golden gameweek is money, a chip spent on a double gameweek is season rank. A manager can play for one or the other, rarely both. `meta.is_golden` marks the round just played; `meta.next_event.is_golden` marks the one coming.

## Pink duck

The manager with the **lowest** score in a round is awarded a pink rubber duck ("rosa badeand"). It is a physical object and it travels.

**Reidar never uses the word.** He writes round losses: "sisteplass i runden", "bunnnoteringen", "sist denne runden". If the data mentions ducks or "ender", translate to a round loss.

## Table and tie-breaks

- The season table is cumulative **net** points (after transfer hits).
- Golden gameweek tie: the tied manager with the most **captain points** takes the prize.

## Season

38 gameweeks. The manager on top after GW38 wins the league. Winners and records: `league_history.md`.
