from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class UIInput:
    mouse_pos: Tuple[int, int] = (0, 0)
    mouse_clicks: List[Tuple[int, int]] = field(default_factory=list) 