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

    def to_dict(self) -> dict[str, Any]:
        """Convert Participant to dictionary for backward compatibility."""
        return asdict(self)
    golden_win_count: int = field(default=0)
=======
    history: list[dict[str, Any]]
    last_event: dict[str, Any]
>>>>>>> abd78cb (Job 22-23: Wire up ranking_progression to CLI)

    def to_dict(self) -> dict[str, Any]:
        """Convert Participant to dictionary for backward compatibility."""
        return asdict(self)
