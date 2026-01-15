from dataclasses import dataclass
from typing import Tuple

@dataclass
class PathRequest:
    start: Tuple[int, int]
    goal: Tuple[int, int]
