from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

@dataclass
class Participant:
    entry_id: int
    team_name: str
    manager_name: str
    total_score: int
    history: List[Dict[str, Any]]
    last_event: Dict[str, Any]
    lowest_rank_count: int = field(default=0)
    win_count: int = field(default=0)
    golden_win_count: int = field(default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Participant to dictionary for backward compatibility."""
        return asdict(self)
