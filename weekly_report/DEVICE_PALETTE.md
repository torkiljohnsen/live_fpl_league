# Device Palette

Reidar's visual furniture. The renderer is marked.js: each device below is either
plain markdown (pull quote, list, heading, table) or an HTML block with a class,
CSS for which lives in `docs/style.css` under `.narrative-article`. For any
`<div class="…" markdown="1">`, leave a **blank line** after the opening tag and
before the closing `</div>` — that is what makes marked parse the inside as
markdown instead of swallowing it as raw HTML. Copy the shape exactly.

**Rule:** 2–3 devices per column, never the same set two weeks running. The
short version (`Kortversjonen`) uses none — prose only.

## Pull quote
When it fits: one line worth lifting out — a stat, a verdict, a line of dialogue.
```
> Fire managere kapteinet Haaland i sesongens første runde. Alle fikk 2 poeng.
```

## Fact box
When it fits: a mini-leaderboard, a record snapshot, a stat comparison. One per column max.
```
<div class="fact-box" markdown="1">

**Sesongens fem laveste rundescorer**

- Hedda: **13** (GW13) — ligarekord.
- Eirin: **24** (GW5) — starten ingen vil huske.

</div>
```

## Short list
When it fits: an inventory — bench disaster, captain results, transfer outcomes. 3–5 items.
```
- Wirtz: **null**. Altså bokstavelig null.
- Alderete: 1. Forsvarspoeng og ingenting mer.
```

## Heading (`##`)
When it fits: marking a real turn in the piece. Fewer is better; never one per manager.

## Standalone one-line paragraph
When it fits: the raised eyebrow, a beat to let land. ≤2 per column.

## Table
When it fits: power rankings, report card, H2H, chip tracker — small, ≤6 rows.
Plain GFM pipe table, no wrapper needed. Points/numeric column last so it
right-aligns automatically, or tag a `.num` class cell if it isn't.
```
| Manager | Form | Poeng |
| --- | --- | --- |
| Torkil | Solid | 89 |
| Daniel | Stigende | 72 |
```
If the table has 4+ columns and might overflow on mobile, wrap it so it scrolls
instead of breaking the page:
```
<div class="table-wrap" markdown="1">

| Manager | Wildcard | Bench Boost | Triple Captain |
| --- | --- | --- | --- |
| Torkil | Ledig | Brukt GW1 | Ledig |

</div>
```

## Chip tracker
Use the **table** device above (manager rows × chip columns). No separate
markup or styling — it's the simplest option and there's already CSS for it.

## Big number ("Ukens tall")
When it fits: one number the whole paragraph orbits — a record, a percentile, an absurdity.
```
<div class="big-number" markdown="1">

**89**

Sesongens beste rundescore så langt — den eneste runden som er spilt.

</div>
```

## Receipt
When it fits: Reidar quoting his own earlier column, dated — pairs with the prediction ledger.
Distinct from the pull quote: no giant quote marks, a dateline, styled like a clipping.
```
<div class="receipt" markdown="1">

**GW9, meg:**

Ingen kommer til å huske dette bytteøkonomien om det går bra.

</div>
```

## Timeline
When it fits: the match-day diary shape (`Dagboka`) — a round that swings late, a big DGW.
```
<div class="timeline" markdown="1">

1. **lør 16:00** — Kampene starter. Ingenting skjer ennå.
2. **søn 17:30** — Siste kamp. Alt avgjøres.

</div>
```

## For/against
When it fits: the trial shape (`Retten er satt`) — prosecution vs. defence, two short columns.
Stacks to one column automatically on mobile.
```
<div class="for-against">

<div class="fa-col" markdown="1">

**Aktoratet**

- Bench boost i GW1 er et impulskjøp.

</div>

<div class="fa-col" markdown="1">

**Forsvaret**

- Han vant runden likevel.

</div>

</div>
```
