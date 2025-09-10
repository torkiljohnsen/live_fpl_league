from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Participant:
    entry_id: int
    team_name: str
    manager_name: str
    total_score: int
    history: List[Dict[str, Any]]
    last_event: Optional[Dict[str, Any]] = None
    # You can add more fields as needed
