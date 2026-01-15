from dataclasses import dataclass
from typing import List

@dataclass
class TileMap:
    width: int
    height: int
    tile_size: int
    tiles: List[int]

    def idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> int:
        return self.tiles[self.idx(x, y)]
