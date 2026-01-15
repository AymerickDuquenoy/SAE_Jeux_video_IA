from dataclasses import dataclass
from typing import Optional

@dataclass
class GameEventState:
    active: Optional[str] = None
    timer: float = 0.0
