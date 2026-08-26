"""Tests for the format scheduler (issue #40, workstreams A + B)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from fpl.format_scheduler import (
    Assignment,
    choose_assignment,
    load_recent_shapes,
    record_shape,
    render_assignment,
)


def _standing(
    name: str,
    event_total: int = 50,
    net_points: int | None = None,
    chip_played: str | None = None,
    transfer_cost: int = 0,
    did_not_play: bool = False,
) -> dict:
    return {
        "player_first_name": name,
        "event_total": event_total,
        "net_points": net_points if net_points is not None else event_total,
        "chip_played": chip_played,
        "transfer_cost": transfer_cost,
        "captain": {"name": "X", "did_not_play": did_not_play},
    }


def _report(
    event_id: int,
    season: str = "2025-26",
    standings: list[dict] | None = None,
    is_golden: bool = False,
    next_golden: bool = False,
    storylines: list[dict] | None = None,
    records: dict | None = None,
    streaks: list[dict] | None = None,
    average_score: int = 50,
) -> dict:
    return {
        "meta": {
            "event_id": event_id,
            "season": season,
            "is_golden": is_golden,
            "next_event": {"id": event_id + 1, "is_golden": next_golden},
        },
        "standings": standings if standings is not None else [_standing("Ola")],
        "awards": {},
        "global": {"average_score": average_score},
        "angles": {"records": records or {}, "streaks": streaks or []},
        "storylines": storylines or [],
    }


def _quiet_standings() -> list[dict]:
    # Spread > 20 so the flat-round trigger doesn't fire; no chips.
    return [_standing(f"M{i}", event_total=40 + i * 3) for i in range(10)]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_same_assignment(self):
        report = _report(7, standings=_quiet_standings())
        a1 = choose_assignment(report, ["portrettet"], rng_seed="fixed-seed")
        a2 = choose_assignment(report, ["portrettet"], rng_seed="fixed-seed")
        assert a1 == a2

    def test_default_seed_is_season_and_event(self):
        report = _report(7, season="2025-26", standings=_quiet_standings())
        a1 = choose_assignment(report, [])
        a2 = choose_assignment(report, [], rng_seed="2025-26-7")
        assert a1 == a2


# ---------------------------------------------------------------------------
# Set-pieces
# ---------------------------------------------------------------------------


class TestSetPieces:
    def test_gw1_is_season_preview(self):
        report = _report(1, standings=_quiet_standings())
        a = choose_assignment(report, [])
        assert a.shape == "sesongforhaandsomtalen"
        assert a.constraint is None

    def test_gw38_is_season_review(self):
        report = _report(38, standings=_quiet_standings())
        a = choose_assignment(report, ["spalten"])
        assert a.shape == "sesongoppsummeringen"
        assert a.constraint is None

    def test_quarter_marks_are_karakterboka(self):
        for gw in (10, 19, 29):
            report = _report(gw, standings=_quiet_standings())
            a = choose_assignment(report, [])
            assert a.shape == "karakterboka", gw
            assert a.constraint is None

    def test_set_pieces_never_repeat_check_last_week(self):
        # Even if last week WAS karakterboka, GW19 must still be karakterboka.
        report = _report(19, standings=_quiet_standings())
        a = choose_assignment(report, ["karakterboka"])
        assert a.shape == "karakterboka"


# ---------------------------------------------------------------------------
# Exclusion rules
# ---------------------------------------------------------------------------


class TestExclusion:
    def test_never_same_shape_as_last_week(self):
        report = _report(7, standings=_quiet_standings())
        for i in range(60):
            a = choose_assignment(report, ["portrettet"], rng_seed=f"seed-{i}")
            assert a.shape != "portrettet"

    def test_non_default_shape_excluded_for_three_weeks(self):
        # GW22 is an ordinary mid-season week (no quarter-mark window).
        report = _report(22, standings=_quiet_standings())
        recent = ["dagboka", "retten_er_satt", "nekrologen"]
        for i in range(60):
            a = choose_assignment(report, recent, rng_seed=f"seed-{i}")
            assert a.shape not in {"dagboka", "retten_er_satt", "nekrologen"}

    def test_default_shape_not_excluded_by_three_week_rule(self):
        # spalten appeared two weeks ago (inside the last-3-weeks window)
        # but NOT last week -- it must still be eligible this week, unlike
        # a non-default shape in the same position.
        report = _report(22, standings=_quiet_standings())
        recent = ["spalten", "kortversjonen", "brevet"]
        shapes = {
            choose_assignment(report, recent, rng_seed=f"seed-{i}").shape
            for i in range(80)
        }
        assert "spalten" in shapes
        assert "kortversjonen" not in shapes


# ---------------------------------------------------------------------------
# Spalten frequency simulation
# ---------------------------------------------------------------------------


class TestSpaltenFrequencySimulation:
    def test_spalten_lands_30_to_50_percent_over_a_season(self):
        recent: list[str] = []
        counts: Counter[str] = Counter()
        prev_shape: str | None = None
        for gw in range(2, 38):
            report = _report(gw, season="2025-26", standings=_quiet_standings())
            a = choose_assignment(report, recent)
            assert a.shape != prev_shape, f"GW{gw} repeated {a.shape} from previous week"
            counts[a.shape] += 1
            prev_shape = a.shape
            recent.append(a.shape)
            recent = recent[-5:]

        total = sum(counts.values())
        fraction = counts["spalten"] / total
        assert 0.30 <= fraction <= 0.50, f"spalten fraction {fraction} out of range: {counts}"


# ---------------------------------------------------------------------------
# Data triggers
# ---------------------------------------------------------------------------


class TestFlatRoundTrigger:
    def test_flat_round_strongly_favors_kortversjonen(self):
        standings = [_standing(f"M{i}", event_total=50 + (i % 2)) for i in range(10)]
        report = _report(7, standings=standings, storylines=[{"score": 20}])

        counts: Counter[str] = Counter()
        for i in range(60):
            a = choose_assignment(report, [], rng_seed=f"flat-{i}")
            counts[a.shape] += 1

        assert counts.most_common(1)[0][0] == "kortversjonen"
        assert counts["kortversjonen"] / sum(counts.values()) > 0.5


class TestQuarterMarkWindowTrigger:
    def test_gw_9_11_20_21_30_31_favor_maktrangeringen(self):
        # A phase-transition marker, not a guaranteed pick: check the rate
        # is clearly elevated versus an otherwise-identical neutral week,
        # not that it dominates the (still heavily-weighted) default.
        baseline_report = _report(22, standings=_quiet_standings())
        baseline_hits = sum(
            1
            for i in range(120)
            if choose_assignment(baseline_report, [], rng_seed=f"baseline-{i}").shape
            == "maktrangeringen"
        )
        baseline_rate = baseline_hits / 120

        for gw in (9, 11, 20, 21, 30, 31):
            report = _report(gw, standings=_quiet_standings())
            hits = sum(
                1
                for i in range(120)
                if choose_assignment(report, [], rng_seed=f"power-{gw}-{i}").shape
                == "maktrangeringen"
            )
            rate = hits / 120
            assert rate > baseline_rate * 3, (gw, rate, baseline_rate)


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


class TestConstraints:
    def test_constraint_never_on_set_piece_weeks(self):
        for gw in (1, 10, 19, 29, 38):
            report = _report(gw, standings=_quiet_standings())
            for i in range(20):
                a = choose_assignment(report, [], rng_seed=f"constraint-{gw}-{i}")
                assert a.constraint is None

    def test_constraint_only_appears_on_spalten_or_portrettet(self):
        report = _report(22, standings=_quiet_standings())
        for i in range(200):
            a = choose_assignment(report, [], rng_seed=f"c-{i}")
            if a.constraint is not None:
                assert a.shape in ("spalten", "portrettet")

    def test_constraint_roughly_one_in_four_on_spalten_weeks(self):
        # Force spalten every time by feeding it a report with nothing but
        # the RNG deciding shape; instead just count constraint rate when
        # shape happens to land on spalten across many seeds.
        report = _report(22, standings=_quiet_standings())
        spalten_weeks = 0
        constrained = 0
        for i in range(400):
            a = choose_assignment(report, [], rng_seed=f"rate-{i}")
            if a.shape == "spalten":
                spalten_weeks += 1
                if a.constraint is not None:
                    constrained += 1
        assert spalten_weeks > 0
        rate = constrained / spalten_weeks
        assert 0.10 <= rate <= 0.40, rate


# ---------------------------------------------------------------------------
# render_assignment
# ---------------------------------------------------------------------------


class TestRenderAssignment:
    def test_output_is_at_most_90_words(self):
        cases = [
            Assignment(
                shape="spalten",
                constraint="under 200 ord",
                calendar_line="Runde 27 av 38 — kvitteringstid; planlegging for dobbel- og blank-runder begynner.",
                set_piece="Gyllen runde: penger på bordet — dette er alltid en ordentlig krok.",
                reason="test",
            ),
            Assignment(
                shape="kortversjonen",
                constraint=None,
                calendar_line="Runde 3 av 38 — rangeringssvingninger er støy; det er for tidlig å bry seg.",
                set_piece=None,
                reason="test",
            ),
            Assignment(
                shape="sesongoppsummeringen",
                constraint=None,
                calendar_line="Runde 38 av 38 — sesongens siste runde.",
                set_piece=None,
                reason="test",
            ),
        ]
        for a in cases:
            text = render_assignment(a)
            word_count = len(text.split())
            assert word_count <= 90, (a.shape, word_count, text)

    def test_output_includes_heading_and_calendar(self):
        a = Assignment(
            shape="spalten",
            constraint=None,
            calendar_line="Runde 7 av 38 — tidlig sesong; ingenting teller ennå.",
            set_piece=None,
            reason="test",
        )
        text = render_assignment(a)
        assert text.startswith("## Ukens oppdrag")
        assert "Kalender: Runde 7 av 38" in text
        assert "Spalten" in text
        assert "Ukens begrensning" not in text

    def test_constraint_line_present_when_set(self):
        a = Assignment(
            shape="portrettet",
            constraint="bare én manager",
            calendar_line="Runde 12 av 38 — chip-sesong og julerot; andre wildcard-vindu nærmer seg.",
            set_piece=None,
            reason="test",
        )
        text = render_assignment(a)
        assert "Ukens begrensning: bare én manager" in text


# ---------------------------------------------------------------------------
# load_recent_shapes / record_shape round trip
# ---------------------------------------------------------------------------


class TestShapesMemoryRoundTrip:
    def test_load_returns_empty_when_no_file(self, tmp_path: Path):
        assert load_recent_shapes(tmp_path, event_id=5) == []

    def test_record_then_load_round_trip(self, tmp_path: Path):
        for gw in range(1, 5):
            record_shape(
                tmp_path,
                gw,
                Assignment(
                    shape=f"shape{gw}",
                    constraint=None,
                    calendar_line="x",
                    set_piece=None,
                    reason="x",
                ),
            )
        recent = load_recent_shapes(tmp_path, event_id=5, window=5)
        assert recent == ["shape1", "shape2", "shape3", "shape4"]

    def test_load_respects_window(self, tmp_path: Path):
        for gw in range(1, 8):
            record_shape(
                tmp_path,
                gw,
                Assignment(
                    shape=f"shape{gw}", constraint=None, calendar_line="x",
                    set_piece=None, reason="x",
                ),
            )
        recent = load_recent_shapes(tmp_path, event_id=8, window=3)
        assert recent == ["shape5", "shape6", "shape7"]

    def test_record_replaces_existing_entry_for_same_event(self, tmp_path: Path):
        record_shape(
            tmp_path, 3,
            Assignment(shape="spalten", constraint=None, calendar_line="x",
                       set_piece=None, reason="x"),
        )
        record_shape(
            tmp_path, 3,
            Assignment(shape="brevet", constraint="ingen adjektiver",
                       calendar_line="x", set_piece=None, reason="x"),
        )
        data = json.loads((tmp_path / "shapes.json").read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["shape"] == "brevet"
        assert data[0]["constraint"] == "ingen adjektiver"

    def test_load_ignores_malformed_file(self, tmp_path: Path):
        (tmp_path / "shapes.json").write_text("not json", encoding="utf-8")
        assert load_recent_shapes(tmp_path, event_id=5) == []


class TestLedgerGate:
    def _quiet_report(self, event_id: int) -> dict:
        return {
            "meta": {"event_id": event_id, "season": "2026-27", "is_golden": False,
                     "next_event": {"id": event_id + 1, "is_golden": False}},
            "global": {"average_score": 50},
            "standings": [
                {"player_first_name": n, "event_total": 50 + i, "net_points": 50 + i,
                 "chip_played": None, "captain": {}, "transfer_cost": 0,
                 "bench_points": 0, "event_percentile": 50.0, "hit_cost_season": 0}
                for i, n in enumerate("ABCDEFGHIJ")
            ],
            "awards": {"chip_usage": [], "hit_takers": [], "bench_disasters": []},
            "angles": {"streaks": [], "records": {}},
            "storylines": [{"kind": "x", "score": 75, "managers": ["A"], "facts": {}, "summary": ""}],
        }

    def test_kvitteringene_never_without_ledger(self):
        shapes = {
            choose_assignment(self._quiet_report(gw), [], rng_seed=f"s{gw}").shape
            for gw in range(2, 38)
        }
        assert "kvitteringene" not in shapes

    def test_kvitteringene_possible_with_ledger(self):
        shapes = {
            choose_assignment(
                self._quiet_report(gw), [], rng_seed=f"s{gw}", has_ledger=True
            ).shape
            for gw in range(2, 38)
        }
        assert "kvitteringene" in shapes
