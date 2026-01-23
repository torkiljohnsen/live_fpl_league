"""Shared test utilities for FPL tests."""

from fpl.participant import Participant


def make_test_participant(
    first_name: str,
    history: list[dict],
    entry_id: int = 1,
    league_rank: int = 1
) -> Participant:
    """Helper to create test Participant objects."""
    return Participant(
        entry_id=entry_id,
        team_name=f"{first_name}'s Team",
        manager_name=f"{first_name} Doe",
        total_score=0,
        history=history,
        last_event={},
        league_rank=league_rank
    )
