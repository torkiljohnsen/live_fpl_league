"""Format rotation and season calendar for Reidar's narratives (issue #40,
workstreams A + B).

Principle: shape is scheduled, not chosen by the model (left to itself the
model regresses to the same six-section default every week). This module
picks the week's narrative shape, an optional wildcard constraint, and a
one-line season-calendar note, all deterministically from the report JSON
and a seed derived from season + gameweek so a rerun reproduces the same
assignment.

Public API:
    SHAPES              -- the shape menu (key -> Shape)
    Assignment          -- what one gameweek was assigned
    choose_assignment() -- pick this week's Assignment
    render_assignment() -- the Norwegian block for the user message
    load_recent_shapes()/record_shape() -- shapes.json round-trip, so the
        picker knows what it did the last few weeks

Not wired here: the "kvitteringene" (prediction ledger) shape needs
weekly_report/reidar_memory/{league}/{season}/ledger.md to exist and be
non-empty (workstream C, not yet built). choose_assignment() has no
filesystem access by design (it is a pure function of report + recent
shapes), so kvitteringene's random weight stays at 0 here until a future
change threads ledger availability into the call -- see the "decisions"
note in the issue #40 workstream A/B report.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# The shape menu
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Shape:
    key: str
    title_no: str
    word_max: int
    description_no: str
    devices_hint: str


SHAPES: dict[str, Shape] = {
    "spalten": Shape(
        "spalten", "Spalten", 600,
        "den vante rette kolonnen",
        "pull quote, fact box, standalone-linje",
    ),
    "kortversjonen": Shape(
        "kortversjonen", "Kortversjonen", 250,
        "kort og konsentrert, ingen overskrifter",
        "ingen",
    ),
    "portrettet": Shape(
        "portrettet", "Portrettet", 650,
        "hele saken om én manager",
        "pull quote, standalone-linje",
    ),
    "maktrangeringen": Shape(
        "maktrangeringen", "Maktrangeringen", 500,
        "styrkeforhold etter form, ikke tabellplassering",
        "tabell",
    ),
    "retten_er_satt": Shape(
        "retten_er_satt", "Retten er satt", 500,
        "én avgjørelse for retten: aktorat, forsvar, dom",
        "for/against-blokk",
    ),
    "kvitteringene": Shape(
        "kvitteringene", "Kvitteringene", 450,
        "Reidar sjekker sine egne spådommer",
        "kvittering (receipt)",
    ),
    "brevet": Shape(
        "brevet", "Brevet", 550,
        "et åpent brev til én manager",
        "standalone-linje",
    ),
    "regnearket": Shape(
        "regnearket", "Regnearket", 400,
        "ett tall snudd og vendt fra alle kanter",
        "stort tall (big-number)",
    ),
    "dagboka": Shape(
        "dagboka", "Dagboka", 500,
        "kampdagen, time for time",
        "tidslinje (timeline)",
    ),
    "nekrologen": Shape(
        "nekrologen", "Nekrologen", 400,
        "en nekrolog over et kapteinbind, en chip eller en tittelsjanse",
        "pull quote",
    ),
    "karakterboka": Shape(
        "karakterboka", "Karakterboka", 500,
        "karakterbok, én linje per manager",
        "tabell",
    ),
    "raadgiveren": Shape(
        "raadgiveren", "Rådgiveren", 450,
        "råd om chips, timing og hvem som spiller for hva",
        "fact box, kvittering",
    ),
    "sesongforhaandsomtalen": Shape(
        "sesongforhaandsomtalen", "Sesongforhåndsomtalen", 650,
        "sesongåpning: laget presenteres, ingen rangeringsprat",
        "fact box",
    ),
    "sesongoppsummeringen": Shape(
        "sesongoppsummeringen", "Sesongoppsummeringen", 650,
        "sesongen oppsummert, Reidars årsavslutning",
        "tabell, stort tall",
    ),
}

# Shapes eligible to be picked by the weighted RNG on an ordinary week.
# karakterboka / sesongforhaandsomtalen / sesongoppsummeringen are fixed
# set-pieces only (see _set_piece_shape below) and never compete here.
_ORDINARY_SHAPES = (
    "spalten", "kortversjonen", "portrettet", "maktrangeringen",
    "retten_er_satt", "kvitteringene", "brevet", "regnearket",
    "dagboka", "nekrologen", "raadgiveren",
)

_DEFAULT_SHAPE = "spalten"

# Base weights on a quiet ordinary week (no data triggers). Tuned, together
# with the exclusion rules below, so spalten lands roughly 40% of ordinary
# weeks -- see the simulation test in tests/fpl_tests/test_format_scheduler.py.
_BASE_WEIGHTS: dict[str, int] = {
    "spalten": 90,
    "kortversjonen": 10,
    "portrettet": 8,
    "maktrangeringen": 5,
    "retten_er_satt": 6,
    "kvitteringene": 0,  # needs the prediction ledger -- see module docstring
    "brevet": 6,
    "regnearket": 6,
    "dagboka": 3,  # no DGW detection yet -- TODO, see issue #40 workstream A
    "nekrologen": 5,
    "raadgiveren": 0,  # only weighted in when eligible, see below
}

CONSTRAINTS: list[str] = [
    "ingen tall i det hele tatt",
    "ti nummererte notater",
    "start med tabellen og jobb deg bakover",
    "under 200 ord",
    "bare én manager",
    "ingen adjektiver",
    "hver setning under tolv ord",
]

_CONSTRAINT_SHAPES = ("spalten", "portrettet")
_CONSTRAINT_PROBABILITY = 0.25


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Assignment:
    shape: str
    constraint: str | None
    calendar_line: str
    set_piece: str | None
    reason: str


def choose_assignment(
    report: dict[str, Any],
    recent_shapes: list[str],
    *,
    rng_seed: str | None = None,
) -> Assignment:
    """Pick this gameweek's Assignment.

    Deterministic given the same (report, recent_shapes, rng_seed): the
    default seed is f"{season}-{event_id}" so a rerun of the same
    gameweek reproduces the same assignment.

    `recent_shapes` is the last few weeks' shapes, oldest first (as
    returned by load_recent_shapes) -- recent_shapes[-1] is last week.
    """
    meta = report.get("meta") or {}
    event_id = meta.get("event_id") or 0
    season = meta.get("season") or "unknown"
    seed = rng_seed if rng_seed is not None else f"{season}-{event_id}"
    rng = random.Random(seed)

    calendar_line = _calendar_line(event_id)
    set_piece = _set_piece_note(meta, event_id)

    set_piece_shape, set_piece_reason = _fixed_set_piece(event_id)
    if set_piece_shape is not None:
        return Assignment(
            shape=set_piece_shape,
            constraint=None,
            calendar_line=calendar_line,
            set_piece=set_piece,
            reason=set_piece_reason,
        )

    last_shape = recent_shapes[-1] if recent_shapes else None
    last_three = set(recent_shapes[-3:])
    excluded = {last_shape} if last_shape else set()
    excluded |= {s for s in last_three if s != _DEFAULT_SHAPE}
    excluded.discard(None)

    weights, triggered = _weighted_menu(report, event_id)
    for shape in excluded:
        weights[shape] = 0

    if sum(weights.values()) <= 0:
        # Defensive fallback: everything eligible got excluded (a very
        # short memory window with an unlucky run). Fall back to an equal
        # weight over everything except last week's shape.
        weights = {s: (0 if s == last_shape else 1) for s in _ORDINARY_SHAPES}

    population = list(weights.keys())
    shape = rng.choices(population, weights=[weights[s] for s in population], k=1)[0]

    constraint = None
    if shape in _CONSTRAINT_SHAPES and rng.random() < _CONSTRAINT_PROBABILITY:
        constraint = rng.choice(CONSTRAINTS)

    reason = (
        f"GW{event_id} weighted RNG pick from {list(_ORDINARY_SHAPES)}; "
        f"triggers={triggered or ['none']}; excluded={sorted(filter(None, excluded)) or ['none']} "
        f"-> {shape}"
    )

    return Assignment(
        shape=shape,
        constraint=constraint,
        calendar_line=calendar_line,
        set_piece=set_piece,
        reason=reason,
    )


def _fixed_set_piece(event_id: int) -> tuple[str | None, str]:
    """Fixed calendar set-pieces (workstream A): GW1, GW38, GW10/19/29."""
    if event_id == 1:
        return "sesongforhaandsomtalen", "GW1 fixed set-piece: season preview"
    if event_id == 38:
        return "sesongoppsummeringen", "GW38 fixed set-piece: season review"
    if event_id in (10, 19, 29):
        return (
            "karakterboka",
            f"GW{event_id} fixed set-piece: quarter/half/three-quarter report card",
        )
    return None, ""


def _weighted_menu(
    report: dict[str, Any], event_id: int
) -> tuple[dict[str, int], list[str]]:
    """Base weights plus data-trigger boosts. Returns (weights, triggered names)."""
    weights = dict(_BASE_WEIGHTS)
    triggered: list[str] = []

    standings = report.get("standings") or []
    angles = report.get("angles") or {}
    storylines = report.get("storylines") or []
    global_block = report.get("global") or {}
    meta = report.get("meta") or {}

    max_storyline_score = max((s.get("score") or 0 for s in storylines), default=0)

    if max_storyline_score >= 90:
        weights["portrettet"] += 15
        weights["regnearket"] += 15
        triggered.append("top_storyline")

    global_average = global_block.get("average_score")
    wasted_chip = any(
        p.get("chip_played") in ("3xc", "bboost")
        and global_average is not None
        and (p.get("event_total") or 0) < global_average
        for p in standings
    )
    hit_high = any((p.get("transfer_cost") or 0) >= 8 for p in standings)
    captain_dnp = any((p.get("captain") or {}).get("did_not_play") for p in standings)
    if wasted_chip or hit_high or captain_dnp:
        weights["retten_er_satt"] += 15
        weights["nekrologen"] += 15
        triggered.append("chip_or_hit_or_dnp_incident")

    records = angles.get("records") or {}
    record_set = any(
        isinstance(records.get(side), dict) and records[side].get("event_id") == event_id
        for side in ("best", "worst")
    )
    if record_set:
        weights["regnearket"] += 15
        triggered.append("record_set")

    streaks = angles.get("streaks") or []
    long_streak = any((s.get("length") or 0) >= 4 for s in streaks)
    if long_streak:
        weights["brevet"] += 12
        weights["portrettet"] += 12
        triggered.append("long_streak")

    net_points = [
        p.get("net_points") for p in standings if p.get("net_points") is not None
    ]
    any_chip_played = any(p.get("chip_played") for p in standings)
    if net_points:
        spread = max(net_points) - min(net_points)
        flat_round = spread <= 20 and max_storyline_score < 70 and not any_chip_played
        if flat_round:
            # "Strongly" per the issue: a flat round has nothing for the
            # default column to chew on, so spalten is actively suppressed
            # rather than just outweighed.
            weights["kortversjonen"] += 60
            weights["spalten"] = min(weights["spalten"], 5)
            triggered.append("flat_round")

    if event_id in (9, 11, 20, 21, 30, 31):
        weights["maktrangeringen"] += 40
        triggered.append("quarter_mark_window")

    next_event = meta.get("next_event") or {}
    golden_next = bool(next_event.get("is_golden"))
    chip_window_closing = 17 <= event_id <= 19 or 36 <= event_id <= 38
    if golden_next or chip_window_closing:
        weights["raadgiveren"] += 20
        triggered.append("advice_window")

    return weights, triggered


# ---------------------------------------------------------------------------
# Calendar (workstream B)
# ---------------------------------------------------------------------------


def _calendar_line(event_id: int) -> str:
    if event_id == 1:
        return "Runde 1 av 38 — sesongåpning; ingen har rukket å gjøre noe galt ennå."
    if 2 <= event_id <= 5:
        return (
            f"Runde {event_id} av 38 — rangeringssvingninger er støy; "
            "det er for tidlig å bry seg."
        )
    if 6 <= event_id <= 11:
        return f"Runde {event_id} av 38 — tidlig sesong; ingenting teller ennå."
    if 12 <= event_id <= 19:
        return (
            f"Runde {event_id} av 38 — chip-sesong og julerot; "
            "andre wildcard-vindu nærmer seg."
        )
    if 20 <= event_id <= 25:
        return f"Runde {event_id} av 38 — midtsesong."
    if 26 <= event_id <= 29:
        return (
            f"Runde {event_id} av 38 — kvitteringstid; "
            "planlegging for dobbel- og blank-runder begynner."
        )
    if 30 <= event_id <= 32:
        return f"Runde {event_id} av 38 — sesongen strammer til."
    if 33 <= event_id <= 38:
        remaining = 38 - event_id
        if remaining == 0:
            return "Runde 38 av 38 — sesongens siste runde."
        return f"Runde {event_id} av 38 — innspurten; {remaining} runder igjen."
    return f"Runde {event_id} av 38."


def _set_piece_note(meta: dict[str, Any], event_id: int) -> str | None:
    """Golden-gameweek / quarter-mark callout (append per workstream B)."""
    if meta.get("is_golden"):
        return "Gyllen runde: penger på bordet — dette er alltid en ordentlig krok."
    next_event = meta.get("next_event") or {}
    if next_event.get("is_golden"):
        return "Neste runde er gyllen — pengene er allerede i spill."
    if event_id in (10, 19, 29):
        return "Kvartstopp i sesongen: karakterboka er ute."
    return None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_assignment(a: Assignment) -> str:
    """The Norwegian block passed to the user message (issue #40, workstream A/B).

    Kept to <= 90 words -- see tests/fpl_tests/test_format_scheduler.py.
    """
    shape = SHAPES[a.shape]
    lines = [
        "## Ukens oppdrag",
        f"Ukens form: {shape.title_no} — {shape.description_no}. "
        f"Ordgrense: {shape.word_max}.",
    ]
    if a.constraint:
        lines.append(f"Ukens begrensning: {a.constraint}")
    lines.append(f"Kalender: {a.calendar_line}")
    if a.set_piece:
        lines.append(a.set_piece)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Recent-shapes memory (shapes.json)
# ---------------------------------------------------------------------------


def _read_shapes_file(memory_dir: Path) -> list[dict[str, Any]]:
    path = Path(memory_dir) / "shapes.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def load_recent_shapes(
    memory_dir: Path, event_id: int, window: int = 5
) -> list[str]:
    """The last `window` shapes before event_id, oldest first.

    Reads {memory_dir}/shapes.json. Missing/malformed file yields [].
    """
    entries = [
        e
        for e in _read_shapes_file(memory_dir)
        if isinstance(e.get("event_id"), int) and e["event_id"] < event_id
    ]
    entries.sort(key=lambda e: e["event_id"])
    recent = entries[-window:] if window > 0 else []
    return [e["shape"] for e in recent if e.get("shape")]


def record_shape(memory_dir: Path, event_id: int, assignment: Assignment) -> None:
    """Append/replace this gameweek's entry in {memory_dir}/shapes.json."""
    memory_dir = Path(memory_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)
    data = [e for e in _read_shapes_file(memory_dir) if e.get("event_id") != event_id]
    data.append(
        {
            "event_id": event_id,
            "shape": assignment.shape,
            "constraint": assignment.constraint,
        }
    )
    data.sort(key=lambda e: e.get("event_id", 0))
    path = memory_dir / "shapes.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
