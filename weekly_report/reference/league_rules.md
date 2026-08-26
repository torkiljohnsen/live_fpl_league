# Ligaens egne regler

Hand-maintained house rules for Sinkaberg The Office (not FPL's own rules — those are in `fpl_rules_2026-27.md`). Source: the league's own rules post, 2026/27 season. Updated 2026-08-26.

## Stakes

- Everyone pays **100 kr** at the start of the season; it goes to the overall winner at the end.
- Every 4th gameweek is a **golden gameweek (GGW)**: GW 4, 8, 12, 16, 20, 24, 28, 32, 36 — nine in all. Each GGW, **50 kr per participant** goes to the manager with the best round score. With ten managers that is 500 kr on the table nine times a season.
- Total buy-in: 100 + 9 × 50 = **550 kr**, paid to the treasurer at the start of the season. The treasurer pays out GGW prizes every 4th week and the main prize at the end. Proposed treasurer: last season's loser, Peder.
- Only the office (4th floor, administration) can join. Last chance to join: the GW4 deadline (the first GGW).
- `meta.is_golden` marks the round just played; `meta.next_event.is_golden` marks the one coming. The points still count normally toward the season table.

This is the league's one genuine strategic quirk: a chip saved for a golden gameweek is money, a chip spent on a double gameweek is season rank.

## Round winner and tie-breaks

**Net points** decide the round winner (gameweek points minus transfer cost).

GGW tie on net points — the better manager wins, decided in this order:

1. most captain points
2. fewest points on the bench
3. fewest transfers made that round
4. fewest transfers made in the season so far

If none of these separate them, the pot is split equally.

## Season winner and tie-breaks

The season table is cumulative net points. A tie at the end is decided in this order:

1. fewest transfers made over the whole season
2. fewest bench points over the whole season
3. highest total team value (player values + bank)

If none of these separate them, the main prize is split equally.

## Pink duck

The lowest score in a round earns the pink rubber duck ("rosa badeand"), a physical object that travels. **Reidar never uses the word.** He writes round losses: "sisteplass i runden", "bunnoteringen", "sist denne runden". If the data mentions ducks or "ender", translate to a round loss.
