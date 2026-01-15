from dataclasses import dataclass
from typing import Tuple

@dataclass
class Sprite:
    width: int
    height: int
    color: Tuple[int, int, int]
