import heapq
from typing import Dict, List, Optional, Set, Tuple
import esper
from components import PathRequest, Path, PathProgress


class AStarSystem(esper.Processor):
    def __init__(self, grid_width: int, grid_height: int, obstacles: Optional[Set[Tuple[int, int]]] = None):
        self.w = grid_width
        self.h = grid_height
        self.obstacles = obstacles or set()

    def process(self, dt: float):
        for ent, req in esper.get_component(PathRequest):
            path = self._a_star(req.start, req.goal)

            if esper.has_component(ent, Path):
                esper.remove_component(ent, Path)
            if esper.has_component(ent, PathProgress):
                esper.remove_component(ent, PathProgress)

            if path and len(path) >= 2:
                esper.add_component(ent, Path(nodes=path))
                esper.add_component(ent, PathProgress(index=0))

            esper.remove_component(ent, PathRequest)

    def _a_star(self, start, goal):
        if not self._in_bounds(start) or not self._in_bounds(goal):
            return None
        if start in self.obstacles or goal in self.obstacles:
            return None
        if start == goal:
            return [start]

        open_heap = []
        heapq.heappush(open_heap, (0, start))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g: Dict[Tuple[int, int], int] = {start: 0}
        closed: Set[Tuple[int, int]] = set()

        while open_heap:
            _, cur = heapq.heappop(open_heap)
            if cur == goal:
                return self._reconstruct(came_from, cur)
            if cur in closed:
                continue
            closed.add(cur)

            for nb in self._neighbors(cur):
                ng = g[cur] + 1
                if ng < g.get(nb, 10**9):
                    came_from[nb] = cur
                    g[nb] = ng
                    f = ng + self._heuristic(nb, goal)
                    heapq.heappush(open_heap, (f, nb))
        return None

    def _neighbors(self, node):
        x, y = node
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            p = (nx, ny)
            if self._in_bounds(p) and p not in self.obstacles:
                yield p

    def _heuristic(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    def _reconstruct(self, came_from, cur):
        path = [cur]
        while cur in came_from:
            cur = came_from[cur]
            path.append(cur)
        path.reverse()
        return path

    def _in_bounds(self, p):
        x, y = p
        return 0 <= x < self.w and 0 <= y < self.h
