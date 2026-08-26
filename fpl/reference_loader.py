"""On-demand reference-doc loader for Reidar's Rapport.

Context weight is the constraint: the reference shelf in
``weekly_report/reference/`` is never in the system prompt by default.
``select_reference_docs`` decides, purely from the report JSON, which (if
any) of the condensed reference files this gameweek's narrative needs;
``load_reference_docs`` reads them and stitches them into one string within
a word budget, dropping the lowest-priority tail if the budget is exceeded.

See ``weekly_report/reference/README.md`` for what each file covers and the
load-when table this module implements.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "weekly_report" / "reference"
WORD_BUDGET = 1500

# Priority order applied when the word budget forces us to drop docs — the
# lowest-priority names at the tail of a triggered set are dropped first.
_PRIORITY_ORDER = [
    "fpl_chips_2026-27.md",
    "fpl_strategy_notes.md",
    "fpl_whats_new_2026-27.md",
    "fpl_rules_2026-27.md",
    "fpl_faq_edge_cases.md",
    "fpl_deadlines_2026-27.md",
    "fpl_bps_2026-27.md",
]

_ADVICE_FORMATS = {"raadgiveren", "advice"}

# Friday / Saturday: FPL's usual deadline days. Any other weekday is unusual
# enough to warrant the deadlines reference doc.
_USUAL_DEADLINE_WEEKDAYS = {4, 5}


def select_reference_docs(
    report: dict[str, Any],
    event_id: int,
    *,
    format: str | None = None,  # noqa: A002 - name fixed by the spec's public API
) -> list[str]:
    """Return reference filenames (in priority order) for this gameweek.

    Pure; no I/O. `report` is the full weekly report JSON (meta/standings/
    awards/league_summary). `format` is the scheduled narrative shape
    (a later workstream); only the advice-shaped formats affect selection
    here, everything else is ignored.
    """
    meta = report.get("meta") or {}
    standings = report.get("standings") or []
    awards = report.get("awards") or {}
    next_event = meta.get("next_event") or {}

    triggered: set[str] = set()

    if 1 <= event_id <= 3:
        triggered.add("fpl_whats_new_2026-27.md")

    captain_incident = _captain_incident(standings, awards)

    if event_id == 1 or captain_incident or _points_tie_at_top(standings):
        triggered.add("fpl_rules_2026-27.md")

    if _any_chip_played(standings, awards) or 16 <= event_id <= 19 or 35 <= event_id <= 38:
        triggered.add("fpl_chips_2026-27.md")

    if _freehit_played(standings) or captain_incident:
        triggered.add("fpl_faq_edge_cases.md")
    # TODO(DGW/BGW): once meta.next_event carries a fixture count for the
    # next gameweek, add a trigger here for a blank or double gameweek.

    if _is_next_gw_golden(next_event, event_id) or event_id in (1, 18, 19, 20) or (
        format in _ADVICE_FORMATS
    ):
        triggered.add("fpl_strategy_notes.md")

    if _midweek_next_deadline(next_event):
        triggered.add("fpl_deadlines_2026-27.md")

    if _bonus_decided_this_round(report):
        triggered.add("fpl_bps_2026-27.md")

    return [name for name in _PRIORITY_ORDER if name in triggered]


def load_reference_docs(
    filenames: list[str],
    reference_dir: Path = REFERENCE_DIR,
    word_budget: int = WORD_BUDGET,
) -> str:
    """Read files, strip nothing, concatenate with a '### <title>' per file.

    Docs are read in the given order (the caller decides priority) and
    appended until adding the next one would exceed `word_budget`; the tail
    is then dropped. The first doc is always included even if it alone
    exceeds the budget, so a single oversized file never yields nothing.
    """
    sections: list[str] = []
    running_words = 0

    for filename in filenames:
        text = (reference_dir / filename).read_text(encoding="utf-8")
        word_count = len(text.split())

        if sections and running_words + word_count > word_budget:
            break

        sections.append(f"### {_extract_title(text)}\n\n{text}")
        running_words += word_count

    return "\n\n".join(sections)


def _extract_title(text: str) -> str:
    """Pull the title from a doc's leading '# Heading' line."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("#").strip()
    return ""


def _any_chip_played(standings: list[dict[str, Any]], awards: dict[str, Any]) -> bool:
    if awards.get("chip_usage"):
        return True
    return any(p.get("chip_played") for p in standings)


def _freehit_played(standings: list[dict[str, Any]]) -> bool:
    return any(p.get("chip_played") == "freehit" for p in standings)


def _captain_incident(standings: list[dict[str, Any]], awards: dict[str, Any]) -> bool:
    if any((p.get("captain") or {}).get("did_not_play") for p in standings):
        return True
    subs = (awards.get("captain_summary") or {}).get("vice_captain_substitutions")
    return bool(subs)


def _points_tie_at_top(standings: list[dict[str, Any]]) -> bool:
    by_rank = {p.get("league_rank"): p for p in standings}
    first = by_rank.get(1)
    second = by_rank.get(2)
    if first is None or second is None:
        return False
    return bool(first.get("total_points") == second.get("total_points"))


def _is_next_gw_golden(next_event: dict[str, Any], event_id: int) -> bool:
    is_golden = next_event.get("is_golden")
    if is_golden is None:
        # No authoritative field yet — fall back to the every-4th-GW rule.
        return (event_id + 1) % 4 == 0
    return bool(is_golden)


def _midweek_next_deadline(next_event: dict[str, Any]) -> bool:
    deadline = next_event.get("deadline_time")
    if not deadline:
        return False
    try:
        dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    except ValueError:
        return False
    return dt.weekday() not in _USUAL_DEADLINE_WEEKDAYS


def _bonus_decided_this_round(report: dict[str, Any]) -> bool:
    """Whether bonus points were the story this round.

    Stub: the report JSON carries no bonus/BPS data today, so this never
    fires. TODO: wire up once weekly_report_stats exposes a bonus-swing
    angle (workstream F).
    """
    return False
