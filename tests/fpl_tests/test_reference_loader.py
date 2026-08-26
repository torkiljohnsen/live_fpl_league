"""Tests for the reference-doc loader (fpl/reference_loader.py)."""

from __future__ import annotations

from pathlib import Path

from fpl.reference_loader import load_reference_docs, select_reference_docs

WHATS_NEW = "fpl_whats_new_2026-27.md"
RULES = "fpl_rules_2026-27.md"
CHIPS = "fpl_chips_2026-27.md"
FAQ = "fpl_faq_edge_cases.md"
STRATEGY = "fpl_strategy_notes.md"
DEADLINES = "fpl_deadlines_2026-27.md"
BPS = "fpl_bps_2026-27.md"


def _report(
    *,
    standings: list[dict] | None = None,
    awards: dict | None = None,
    next_event: dict | None = None,
) -> dict:
    meta: dict = {"event_id": 7}
    if next_event is not None:
        meta["next_event"] = next_event
    return {
        "meta": meta,
        "standings": standings or [],
        "awards": awards or {},
        "league_summary": {},
    }


def _participant(**overrides: object) -> dict:
    base = {
        "player_first_name": "Ola",
        "league_rank": 1,
        "total_points": 50,
        "chip_played": None,
        "captain": {"name": "Haaland", "did_not_play": False},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# select_reference_docs — the quiet baseline
# ---------------------------------------------------------------------------


class TestQuietWeek:
    def test_ordinary_gw7_selects_nothing(self):
        # GW7, no chips, next deadline on a Friday, next GW explicitly not golden.
        report = _report(
            standings=[
                _participant(player_first_name="Ola", league_rank=1, total_points=50),
                _participant(player_first_name="Kari", league_rank=2, total_points=45),
            ],
            next_event={
                "id": 8,
                "deadline_time": "2026-10-30T17:30:00Z",  # a Friday
                "is_golden": False,
            },
        )

        assert select_reference_docs(report, event_id=7) == []


# ---------------------------------------------------------------------------
# select_reference_docs — individual triggers
# ---------------------------------------------------------------------------


class TestGW1:
    def test_gw1_selects_rules_and_whats_new(self):
        report = _report(standings=[_participant()], next_event=None)

        docs = select_reference_docs(report, event_id=1)

        assert RULES in docs
        assert WHATS_NEW in docs


class TestWhatsNew:
    def test_gw2_triggers_whats_new(self):
        report = _report()
        assert WHATS_NEW in select_reference_docs(report, event_id=2)

    def test_gw3_triggers_whats_new(self):
        report = _report()
        assert WHATS_NEW in select_reference_docs(report, event_id=3)

    def test_gw4_does_not_trigger_whats_new(self):
        report = _report(next_event={"id": 5, "deadline_time": None, "is_golden": False})
        assert WHATS_NEW not in select_reference_docs(report, event_id=4)


class TestChips:
    def test_chip_played_triggers_chips_doc(self):
        report = _report(
            standings=[_participant(chip_played="bboost")],
        )
        assert CHIPS in select_reference_docs(report, event_id=7)

    def test_chip_usage_award_triggers_chips_doc(self):
        report = _report(awards={"chip_usage": [{"player_name": "Ola", "chip": "3xc"}]})
        assert CHIPS in select_reference_docs(report, event_id=7)

    def test_gw16_to_19_trigger_chips_doc(self):
        for gw in (16, 17, 18, 19):
            report = _report(next_event={"id": gw + 1, "deadline_time": None, "is_golden": False})
            assert CHIPS in select_reference_docs(report, event_id=gw), gw

    def test_gw35_to_38_trigger_chips_doc(self):
        for gw in (35, 36, 37, 38):
            report = _report()
            assert CHIPS in select_reference_docs(report, event_id=gw), gw

    def test_gw20_does_not_trigger_chips_doc(self):
        report = _report(
            standings=[_participant()],
            next_event={"id": 21, "deadline_time": None, "is_golden": False},
        )
        assert CHIPS not in select_reference_docs(report, event_id=20)


class TestCaptainIncidentAndRules:
    def test_captain_did_not_play_triggers_rules_and_faq(self):
        report = _report(
            standings=[
                _participant(captain={"name": "Haaland", "did_not_play": True}),
            ],
        )
        docs = select_reference_docs(report, event_id=7)
        assert RULES in docs
        assert FAQ in docs

    def test_vice_captain_substitution_award_triggers_rules_and_faq(self):
        report = _report(
            standings=[_participant()],
            awards={
                "captain_summary": {
                    "vice_captain_substitutions": [
                        {"player_name": "Ola", "original_captain": "Haaland"}
                    ]
                }
            },
        )
        docs = select_reference_docs(report, event_id=7)
        assert RULES in docs
        assert FAQ in docs

    def test_tie_at_top_of_standings_triggers_rules(self):
        report = _report(
            standings=[
                _participant(player_first_name="Ola", league_rank=1, total_points=50),
                _participant(player_first_name="Kari", league_rank=2, total_points=50),
            ],
        )
        assert RULES in select_reference_docs(report, event_id=7)

    def test_no_tie_does_not_trigger_rules(self):
        report = _report(
            standings=[
                _participant(player_first_name="Ola", league_rank=1, total_points=50),
                _participant(player_first_name="Kari", league_rank=2, total_points=45),
            ],
            next_event={"id": 8, "deadline_time": "2026-10-30T17:30:00Z", "is_golden": False},
        )
        assert select_reference_docs(report, event_id=7) == []


class TestFreehitFaq:
    def test_freehit_played_triggers_faq(self):
        report = _report(standings=[_participant(chip_played="freehit")])
        assert FAQ in select_reference_docs(report, event_id=7)

    def test_freehit_played_does_not_trigger_faq_when_other_chip(self):
        report = _report(
            standings=[_participant(chip_played="wildcard")],
            next_event={"id": 8, "deadline_time": "2026-10-30T17:30:00Z", "is_golden": False},
        )
        assert FAQ not in select_reference_docs(report, event_id=7)


class TestStrategyNotes:
    def test_next_gw_golden_via_explicit_flag(self):
        report = _report(next_event={"id": 8, "deadline_time": None, "is_golden": True})
        assert STRATEGY in select_reference_docs(report, event_id=7)

    def test_next_gw_golden_via_fallback_formula(self):
        # No explicit is_golden field at all -> fall back to (event_id+1) % 4 == 0.
        report = _report()
        assert STRATEGY in select_reference_docs(report, event_id=7)

    def test_explicit_is_golden_false_overrides_fallback(self):
        # event_id=7 would be golden-next under the fallback formula, but an
        # explicit is_golden=False from the API must win.
        report = _report(next_event={"id": 8, "deadline_time": None, "is_golden": False})
        assert STRATEGY not in select_reference_docs(report, event_id=7)

    def test_gw18_and_gw19_trigger_strategy_notes(self):
        for gw in (18, 19):
            report = _report(next_event={"id": gw + 1, "deadline_time": None, "is_golden": False})
            assert STRATEGY in select_reference_docs(report, event_id=gw), gw

    def test_gw20_triggers_strategy_notes(self):
        report = _report(next_event={"id": 21, "deadline_time": None, "is_golden": False})
        assert STRATEGY in select_reference_docs(report, event_id=20)

    def test_advice_shaped_format_triggers_strategy_notes(self):
        report = _report(next_event={"id": 8, "deadline_time": None, "is_golden": False})
        assert STRATEGY in select_reference_docs(report, event_id=7, format="raadgiveren")
        assert STRATEGY in select_reference_docs(report, event_id=7, format="advice")

    def test_other_format_does_not_trigger_strategy_notes(self):
        report = _report(next_event={"id": 8, "deadline_time": None, "is_golden": False})
        assert STRATEGY not in select_reference_docs(report, event_id=7, format="kortversjonen")


class TestDeadlines:
    def test_midweek_deadline_triggers_doc(self):
        # 2026-11-04 is a Wednesday.
        report = _report(
            next_event={"id": 11, "deadline_time": "2026-11-04T18:00:00Z", "is_golden": False}
        )
        assert DEADLINES in select_reference_docs(report, event_id=10)

    def test_friday_deadline_does_not_trigger_doc(self):
        report = _report(
            next_event={"id": 11, "deadline_time": "2026-10-30T17:30:00Z", "is_golden": False}
        )
        assert DEADLINES not in select_reference_docs(report, event_id=10)

    def test_saturday_deadline_does_not_trigger_doc(self):
        report = _report(
            next_event={"id": 11, "deadline_time": "2026-10-31T11:00:00Z", "is_golden": False}
        )
        assert DEADLINES not in select_reference_docs(report, event_id=10)

    def test_missing_next_event_never_triggers_doc(self):
        report = _report()
        assert DEADLINES not in select_reference_docs(report, event_id=10)


class TestBps:
    def test_bps_never_triggers_automatically(self):
        # Stub: no bonus data in the report JSON today.
        report = _report(
            standings=[_participant(chip_played="bboost")],
            awards={"chip_usage": [{"player_name": "Ola", "chip": "bboost"}]},
        )
        assert BPS not in select_reference_docs(report, event_id=1)


class TestPriorityOrder:
    def test_docs_returned_in_priority_order(self):
        # Force every trigger except bps to fire and check ordering.
        report = _report(
            standings=[
                _participant(
                    player_first_name="Ola",
                    league_rank=1,
                    total_points=50,
                    chip_played="freehit",
                    captain={"name": "Haaland", "did_not_play": True},
                ),
            ],
            next_event={"id": 2, "deadline_time": "2026-08-19T18:00:00Z", "is_golden": True},
        )

        docs = select_reference_docs(report, event_id=1, format="raadgiveren")

        assert docs == [CHIPS, STRATEGY, WHATS_NEW, RULES, FAQ, DEADLINES]


# ---------------------------------------------------------------------------
# load_reference_docs
# ---------------------------------------------------------------------------


class TestLoadReferenceDocs:
    def test_empty_list_returns_empty_string(self):
        assert load_reference_docs([]) == ""

    def test_reads_and_titles_real_docs(self):
        content = load_reference_docs([RULES])
        assert "### FPL rules 2026/27" in content
        assert "Source: https://fantasy.premierleague.com" in content

    def test_concatenates_multiple_docs_in_order(self):
        content = load_reference_docs([WHATS_NEW, RULES])
        assert content.index("What's new") < content.index("FPL rules 2026/27")

    def test_typical_week_stays_within_default_budget(self):
        # Every real doc combined is still well under the 1500-word ceiling.
        all_docs = [WHATS_NEW, RULES, CHIPS, FAQ, STRATEGY, DEADLINES, BPS]
        content = load_reference_docs(all_docs)
        assert len(content.split()) <= 3500  # sanity: not literally unbounded

    def test_budget_drops_the_tail(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("# A\n\n" + ("word " * 100), encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n\n" + ("word " * 100), encoding="utf-8")
        (tmp_path / "c.md").write_text("# C\n\n" + ("word " * 100), encoding="utf-8")

        content = load_reference_docs(
            ["a.md", "b.md", "c.md"], reference_dir=tmp_path, word_budget=150
        )

        assert "### A" in content
        assert "### B" not in content
        assert "### C" not in content

    def test_first_doc_always_included_even_over_budget(self, tmp_path: Path):
        (tmp_path / "big.md").write_text("# Big\n\n" + ("word " * 200), encoding="utf-8")

        content = load_reference_docs(["big.md"], reference_dir=tmp_path, word_budget=10)

        assert "### Big" in content

    def test_budget_allows_second_doc_when_it_fits(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("# A\n\n" + ("word " * 10), encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n\n" + ("word " * 10), encoding="utf-8")

        content = load_reference_docs(
            ["a.md", "b.md"], reference_dir=tmp_path, word_budget=100
        )

        assert "### A" in content
        assert "### B" in content
