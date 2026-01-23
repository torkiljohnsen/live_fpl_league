from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Participant:
    entry_id: int
    team_name: str
    manager_name: str
    total_score: int
    history: list[dict[str, Any]]
    last_event: dict[str, Any]
    lowest_rank_count: int = field(default=0)
    win_count: int = field(default=0)
    golden_win_count: int = field(default=0)
    league_rank: int = field(default=0)

    @property
    def player_first_name(self) -> str:
        """Extract first name from manager_name for display purposes."""
        return self.manager_name.split()[0] if self.manager_name else 'Unknown'

    def to_dict(self) -> dict[str, Any]:
        """Convert Participant to dictionary for backward compatibility."""
        return asdict(self)
