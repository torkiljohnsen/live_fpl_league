"""Tests for fpl/formatters.py."""

from fpl.formatters import NO_RANK, format_rank_compact


class TestFormatRankCompact:
    def test_below_thousand_shown_as_is(self):
        assert format_rank_compact(1) == "1"
        assert format_rank_compact(999) == "999"

    def test_thousands(self):
        assert format_rank_compact(1234) == "1.23k"
        assert format_rank_compact(23456) == "23.5k"
        assert format_rank_compact(345678) == "345k"

    def test_millions(self):
        assert format_rank_compact(4567890) == "4.57M"
        assert format_rank_compact(56789012) == "56.8M"
        assert format_rank_compact(678901234) == "678M"

    def test_none_rank_returns_dash(self):
        """FPL leaves ranks null until a gameweek is scored (e.g. during GW1)."""
        assert format_rank_compact(None) == NO_RANK
