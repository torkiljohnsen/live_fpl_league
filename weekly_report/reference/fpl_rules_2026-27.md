# FPL rules 2026/27 — condensed

Source: https://fantasy.premierleague.com/en/help/rules (retrieved 2026-08-26). Chips are in `fpl_chips_2026-27.md`; the full BPS table in `fpl_bps_2026-27.md`.

## Squad and line-up

- 15 players: 2 GK, 5 DEF, 5 MID, 3 FWD. Budget £100m. Max 3 players from one club.
- Start 11 each gameweek. Any formation with 1 GK, ≥3 DEF, ≥1 FWD.
- Captain scores double. If the captain plays no minutes, the vice-captain is doubled instead. If neither plays, nobody is doubled.
- "Playing" = any minutes on the pitch, or receiving a card.

## Automatic substitutions

Processed at the end of the gameweek, in the manager's bench order:
- A GK who doesn't play is replaced by the bench GK, if he played.
- An outfield player who doesn't play is replaced by the highest-priority bench player who played *and* keeps the formation legal (e.g. with 3 starting defenders, a defender can only be replaced by a defender).

## Transfers

- Unlimited free transfers before the manager's first deadline.
- Then 1 free transfer per gameweek. Each extra transfer costs **−4** (deducted at the start of the next gameweek).
- Unused free transfers roll over; **max 5 stored**.
- Max 20 transfers in one gameweek (not when playing Wildcard or Free Hit).
- Selling price: you keep half of any price rise since purchase, rounded down to £0.1m (bought 7.5, now 7.8 → sells for 7.6).
- Prices change daily at midnight UK time based on transfer activity.

## Deadlines

90 minutes before the first kick-off of the gameweek; never changed within 24 h of the scheduled time. All team changes (line-up, transfers, captain, bench order) must be in by the deadline. Full table in `fpl_deadlines_2026-27.md`.

## Scoring

| Action | Points |
|---|---|
| Playing up to 60 min | 1 |
| Playing 60+ min (excl. stoppage time) | 2 |
| Goal: GK / DEF / MID / FWD | 10 / 6 / 5 / 4 |
| Assist | 3 |
| Clean sheet: GK or DEF / MID | 4 / 1 |
| Every 3 saves (GK) | 1 |
| Defensive contribution (see below) | 2 |
| Penalty save | 5 |
| Penalty miss | −2 |
| Bonus (best three players in a match) | 1–3 |
| Every 2 goals conceded (GK/DEF) | −1 |
| Yellow / red card | −1 / −3 |
| Own goal | −2 |

- **Defensive contribution**: DEF with ≥10 clearances+blocks+interceptions+tackles in a match → 2 pts. MID/FWD with ≥12 of those plus recoveries → 2 pts. Does not stack (20 CBIT is still 2 pts).
- **Clean sheet** requires 60+ minutes on the pitch without conceding while on; being subbed off before a goal keeps it.
- A red-carded player keeps being penalised for goals his team concedes; the −3 includes any yellow.
- **Bonus**: top three BPS scores in each match get 3/2/1. Ties: shared 1st → 3, 3, 1; shared 2nd → 3, 2, 2; shared 3rd → 3, 2, 1, 1.
- **Assists** (short version): last attacking touch before the goal — pass, inadvertent touch, or a shot that is saved/blocked/hits the woodwork and is then scored. Killed by two or more defensive touches, or by the scorer converting his own rebound. Winning a penalty or direct free-kick that someone *else* scores is an assist; winning a corner or throw-in is not. Opta decides, FPL has the final word.

## When points are final

Points can change until **09:00 UK on the day after the gameweek's last match** (Opta's post-match review; new for 2026/27). After that, changes only in extraordinary circumstances.

## League tie-breaks (classic scoring)

Equal total points → the team with **fewer transfers** ranks higher. Transfers made on a Wildcard or Free Hit don't count.
