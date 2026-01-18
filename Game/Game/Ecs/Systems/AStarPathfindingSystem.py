"""A* pathfinding utilities.

This module provides:
- `astar(grid_map, start, goal, allow_diagonal=False)` which dispatches based on
  the provided map: if `grid_map` has attribute `tiles` it is treated as the
  project's `GridMap` (uses `GridTile` attributes `walkable` and `speed`),
  otherwise if it's a 2D numpy array it will run A* on that array (0=free, 1=blocked).

The implementation for `GridMap` uses tile `speed` to weight movement cost (slower
tiles are more expensive). The numpy-grid implementation uses unit costs.
"""
from typing import List, Tuple, Dict, Optional
import heapq
import math

import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.pathRequest import PathRequest
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress

Point = Tuple[int, int]


def _heuristic(a: Point, b: Point, diagonal: bool) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    if diagonal:
        # Octile distance
        F = math.sqrt(2) - 1
        return (dx + dy) + (F * min(dx, dy)) - min(dx, dy)
    return dx + dy


def _neighbors_4_8(pos: Point, width: Optional[int], height: Optional[int], diagonal: bool) -> List[Point]:
    x, y = pos
    nbrs = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    if diagonal:
        nbrs += [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
    if width is None or height is None:
        return nbrs
    out = []
    for nx, ny in nbrs:
        if 0 <= nx < width and 0 <= ny < height:
            out.append((nx, ny))
    return out


def astar_gridmap(grid_map, start: Point, goal: Point, allow_diagonal: bool = False) -> Optional[List[Point]]:
    """A* using `GridMap` / `GridTile` objects.

    - `grid_map` must expose `.tiles` iterable and optionally `.width` and `.height`.
    - Each tile must have `.x`, `.y`, `.walkable` and `.speed` attributes.
    - `start` and `goal` are `(x,y)` tile coordinates.
    """
    tile_map: Dict[Point, object] = {}
    for t in getattr(grid_map, "tiles", []):
        tile_map[(t.x, t.y)] = t

    speeds = [getattr(t, "speed", 0) for t in tile_map.values() if getattr(t, "speed", 0) > 0]
    max_speed = max(speeds) if speeds else 1.0

    def cost(a: Point, b: Point) -> float:
        tile = tile_map.get(b)
        if tile is None or not getattr(tile, "walkable", True):
            return float("inf")
        s = float(getattr(tile, "speed", max_speed))
        base = 1.0
        if a[0] != b[0] and a[1] != b[1]:
            base *= math.sqrt(2)
        # slower tiles => higher cost
        return base * (max_speed / s)

    width = getattr(grid_map, "width", None)
    height = getattr(grid_map, "height", None)

    open_heap = []
    g_score: Dict[Point, float] = {start: 0.0}
    came_from: Dict[Point, Point] = {}
    f0 = _heuristic(start, goal, allow_diagonal)
    counter = 0
    heapq.heappush(open_heap, (f0, counter, start))
    closed = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        closed.add(current)
        for nbr in _neighbors_4_8(current, width, height, allow_diagonal):
            if nbr in closed:
                continue
            tile = tile_map.get(nbr)
            if tile is None or not getattr(tile, "walkable", True):
                continue
            tentative = g_score.get(current, float("inf")) + cost(current, nbr)
            if tentative < g_score.get(nbr, float("inf")):
                came_from[nbr] = current
                g_score[nbr] = tentative
                f = tentative + _heuristic(nbr, goal, allow_diagonal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nbr))

    return None


def astar_numpy(grid, start: Point, goal: Point, allow_diagonal: bool = True) -> Optional[List[Point]]:
    """A* over a 2D grid (list of lists), where 0 = free, 1 = blocked.

    `start` and `goal` are (x,y) tuples.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    def is_blocked(p: Point) -> bool:
        x, y = p
        return grid[x][y] != 0

    open_heap = []
    g_score: Dict[Point, float] = {start: 0.0}
    came_from: Dict[Point, Point] = {}
    f0 = _heuristic(start, goal, allow_diagonal)
    counter = 0
    heapq.heappush(open_heap, (f0, counter, start))
    closed = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        closed.add(current)
        for nbr in _neighbors_4_8(current, rows, cols, allow_diagonal):
            if nbr in closed:
                continue
            if is_blocked(nbr):
                continue
            step_cost = math.sqrt(2) if (nbr[0] != current[0] and nbr[1] != current[1]) else 1.0
            tentative = g_score.get(current, float("inf")) + step_cost
            if tentative < g_score.get(nbr, float("inf")):
                came_from[nbr] = current
                g_score[nbr] = tentative
                f = tentative + _heuristic(nbr, goal, allow_diagonal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nbr))

    return None


def astar(grid_map_or_grid, start: Point, goal: Point, allow_diagonal: bool = False) -> Optional[List[Point]]:
    """Dispatching helper: accepts either a `GridMap` (has `.tiles`) or a 2D grid (list of lists).

    Returns list of (x,y) points or None when no path found.
    """
    if hasattr(grid_map_or_grid, "tiles"):
        return astar_gridmap(grid_map_or_grid, start, goal, allow_diagonal=allow_diagonal)

    return astar_numpy(grid_map_or_grid, start, goal, allow_diagonal=allow_diagonal)


def astar_navgrid(nav_grid, start: Point, goal: Point, allow_diagonal: bool = False) -> Optional[List[Point]]:
    """A* spécialisé pour NavigationGrid (is_walkable + movement_cost)."""
    width = getattr(nav_grid, "width", None)
    height = getattr(nav_grid, "height", None)

    open_heap = []
    g_score: Dict[Point, float] = {start: 0.0}
    came_from: Dict[Point, Point] = {}
    f0 = _heuristic(start, goal, allow_diagonal)
    counter = 0
    heapq.heappush(open_heap, (f0, counter, start))
    closed = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        closed.add(current)

        for nbr in _neighbors_4_8(current, width, height, allow_diagonal):
            if nbr in closed:
                continue

            x, y = nbr
            if not nav_grid.is_walkable(x, y):
                continue

            base = math.sqrt(2) if (nbr[0] != current[0] and nbr[1] != current[1]) else 1.0
            move_cost = float(nav_grid.movement_cost(x, y))
            if math.isinf(move_cost):
                continue

            tentative = g_score.get(current, float("inf")) + base * move_cost
            if tentative < g_score.get(nbr, float("inf")):
                came_from[nbr] = current
                g_score[nbr] = tentative
                f = tentative + _heuristic(nbr, goal, allow_diagonal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nbr))

    return None


class AStarPathfindingSystem(esper.Processor):
    """
    System Esper : consomme PathRequest et produit Path + PathProgress.
    (Phase 1 sans IA : chemin direct vers objectif)
    """

    def __init__(self, nav_grid, *, allow_diagonal: bool = False):
        super().__init__()
        self.nav_grid = nav_grid
        self.allow_diagonal = bool(allow_diagonal)

    def process(self, dt: float):
        for ent, (gpos, req) in esper.get_components(GridPosition, PathRequest):
            start = (int(gpos.x), int(gpos.y))
            goal = (int(req.goal.x), int(req.goal.y))

            points = astar_navgrid(self.nav_grid, start, goal, allow_diagonal=self.allow_diagonal)
            if not points:
                esper.remove_component(ent, PathRequest)
                continue

            nodes = [GridPosition(x=p[0], y=p[1]) for p in points]

            if esper.has_component(ent, Path):
                esper.remove_component(ent, Path)
            esper.add_component(ent, Path(nodes))

            if esper.has_component(ent, PathProgress):
                esper.remove_component(ent, PathProgress)
            esper.add_component(ent, PathProgress(index=0))

            esper.remove_component(ent, PathRequest)


# alias si tu veux l'importer comme "Processor"
AStarPathfindingProcessor = AStarPathfindingSystem

