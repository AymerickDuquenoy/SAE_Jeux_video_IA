import heapq
from typing import Dict, List, Optional, Tuple, Set

import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.pathRequest import PathRequest


class AStarPathfindingSystem(esper.Processor):
    """
    Système ECS : calcule les chemins A* sur une grille 2D (4 voisins).

    Esper v3 : pas de World object.
    -> On utilise les fonctions module-level : esper.get_components, esper.add_component, etc.

    - Heuristique : Manhattan (|dx| + |dy|).
    - Déclenchement : toute entité ayant GridPosition + PathRequest.
    - Résultat : ajoute Path(noeuds=[...]) + PathProgress(index=0) puis retire PathRequest.

    Le système a besoin d'une grille de navigation (nav_grid) fournissant au minimum :
        - width, height
        - is_walkable(x, y) -> bool
        - movement_cost(x, y) -> float  (optionnel, si absent on considère 1.0)
    """

    def __init__(self, nav_grid, *, allow_goal_blocked: bool = False, max_search: Optional[int] = None):
        super().__init__()
        self.grid = nav_grid
        self.allow_goal_blocked = allow_goal_blocked
        self.max_search = max_search

    def process(self, dt: float):
        # Esper v3 -> pas self.world.get_components
        for ent, (pos, req) in esper.get_components(GridPosition, PathRequest):
            start = (pos.x, pos.y)
            goal = (req.goal.x, req.goal.y)

            nodes = self._astar(start, goal)

            # on remplace les anciens chemins si présents
            if esper.has_component(ent, Path):
                esper.remove_component(ent, Path)
            if esper.has_component(ent, PathProgress):
                esper.remove_component(ent, PathProgress)

            if nodes:
                path_nodes = [GridPosition(x, y) for (x, y) in nodes]
                esper.add_component(ent, Path(noeuds=path_nodes))
                esper.add_component(ent, PathProgress(index=0))

            # dans tous les cas, la requête a été traitée
            if esper.has_component(ent, PathRequest):
                esper.remove_component(ent, PathRequest)

    # ------------------------------
    # A* core
    # ------------------------------
    def _astar(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        if not self._in_bounds(*start) or not self._in_bounds(*goal):
            return []

        if not self._is_walkable(*start):
            return []

        if not self._is_walkable(*goal) and not self.allow_goal_blocked:
            return []

        open_heap: List[Tuple[float, float, Tuple[int, int]]] = []
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        closed: Set[Tuple[int, int]] = set()

        h0 = self._heuristic(start, goal)
        heapq.heappush(open_heap, (h0, 0.0, start))

        expansions = 0

        while open_heap:
            f, g, current = heapq.heappop(open_heap)

            if current in closed:
                continue
            closed.add(current)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            expansions += 1
            if self.max_search is not None and expansions > self.max_search:
                break

            for nx, ny in self._neighbors(*current):
                neighbor = (nx, ny)

                if neighbor in closed:
                    continue

                if not self._is_walkable(nx, ny) and neighbor != goal:
                    continue

                tentative_g = g_score[current] + self._movement_cost(nx, ny)

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    nf = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_heap, (nf, tentative_g, neighbor))

        return []

    def _reconstruct_path(
        self,
        came_from: Dict[Tuple[int, int], Tuple[int, int]],
        current: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    # ------------------------------
    # Helpers grille
    # ------------------------------
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < int(self.grid.width) and 0 <= y < int(self.grid.height)

    def _neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        return [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]

    def _is_walkable(self, x: int, y: int) -> bool:
        if hasattr(self.grid, "is_walkable"):
            return bool(self.grid.is_walkable(x, y))
        return True

    def _movement_cost(self, x: int, y: int) -> float:
        if hasattr(self.grid, "movement_cost"):
            return float(self.grid.movement_cost(x, y))
        return 1.0
