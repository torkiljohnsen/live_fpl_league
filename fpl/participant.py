from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class Participant:
    entry_id: int
    team_name: str
    manager_name: str
    total_score: int
    history: List[Dict[str, Any]]
    last_event: Dict[str, Any]
