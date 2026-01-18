from dataclasses import dataclass
from typing import Optional

@dataclass
class TimedEffect:
    kind: str
    value: float
    remaining: float
    target_team: Optional[int] = None
