from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Path:
    nodes: List[Tuple[int, int]]
