from dataclasses import dataclass, field
from typing import List

@dataclass
class Spawner:
    x: float
    y: float
    team_id: int
    queue: List[str] = field(default_factory=list)
    cooldown: float = 0.8
    timer: float = 0.0
