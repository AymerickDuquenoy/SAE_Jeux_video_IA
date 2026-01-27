# Game/App/utils/lane_pathfinder.py
"""Lane pathfinding utilities for Antique War."""

import heapq


class LanePathfinder:
    """Calcul des chemins A* et des routes de lanes."""

    def __init__(self, app):
        self.app = app

    def cell_cost(self, x: int, y: int) -> float:
        """Coût d'une cellule pour le pathfinding."""
        try:
            m = float(self.app.nav_grid.mult[y][x])
        except Exception:
            m = 1.0
        if m <= 0.0:
            return 999999.0
        return 1.0 / max(0.05, m)

    def astar(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Algorithme A* pour trouver un chemin entre start et goal.
        Retourne une liste de tuples (x, y) ou une liste vide si aucun chemin.
        """
        if not self.app.nav_grid:
            return []
        if start == goal:
            return [start]

        w = int(getattr(self.app.nav_grid, "width", 0))
        h = int(getattr(self.app.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return []

        sx, sy = start
        gx, gy = goal
        if not self.app.nav_grid.is_walkable(sx, sy):
            return []
        if not self.app.nav_grid.is_walkable(gx, gy):
            return []

        def h_manh(a: tuple[int, int], b: tuple[int, int]) -> float:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_heap = []
        heapq.heappush(open_heap, (0.0, 0.0, (sx, sy)))

        came = {}
        gscore = {(sx, sy): 0.0}
        closed = set()

        while open_heap:
            _f, g, cur = heapq.heappop(open_heap)
            if cur in closed:
                continue

            if cur == (gx, gy):
                out = [cur]
                while cur in came:
                    cur = came[cur]
                    out.append(cur)
                out.reverse()
                return out

            closed.add(cur)
            cx, cy = cur

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = cx + dx
                ny = cy + dy
                if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
                    continue
                if not self.app.nav_grid.is_walkable(nx, ny):
                    continue

                ng = g + self.cell_cost(nx, ny)
                if (nx, ny) not in gscore or ng < gscore[(nx, ny)]:
                    gscore[(nx, ny)] = ng
                    came[(nx, ny)] = (cx, cy)
                    nf = ng + h_manh((nx, ny), (gx, gy))
                    heapq.heappush(open_heap, (nf, ng, (nx, ny)))

        return []

    def compute_lane_route(self, lane_idx: int) -> list[tuple[int, int]]:
        """
        Calcule le chemin A* complet d'une lane (pyramide joueur → pyramide ennemie).
        
        - Lane 0: HAUT des pyramides
        - Lane 1: MILIEU (côtés des pyramides)
        - Lane 2: BAS des pyramides
        """
        if not self.app.nav_grid:
            return []

        lane_idx = max(0, min(2, int(lane_idx)))
        lane_y = int(self.app.lanes_y[lane_idx])

        px = int(self.app.player_pyr_pos[0])
        py = int(self.app.player_pyr_pos[1])
        ex = int(self.app.enemy_pyr_pos[0])
        ey = int(self.app.enemy_pyr_pos[1])

        h = int(getattr(self.app.nav_grid, "height", 0))
        w = int(getattr(self.app.nav_grid, "width", 0))

        def clamp_xy(x: int, y: int) -> tuple[int, int]:
            x = max(1, min(w - 2, int(x)))
            y = max(1, min(h - 2, int(y)))
            return (x, y)

        # Ancres selon la lane
        if lane_idx == 0:
            start_anchor = clamp_xy(px, py - 1)
            end_anchor = clamp_xy(ex, ey - 1)
        elif lane_idx == 1:
            start_anchor = clamp_xy(px + 1, py)
            end_anchor = clamp_xy(ex - 1, ey)
        else:
            start_anchor = clamp_xy(px, py + 1)
            end_anchor = clamp_xy(ex, ey + 1)

        # Points d'entrée/sortie sur la lane horizontale
        entry_point = clamp_xy(px + 1, lane_y)
        exit_point = clamp_xy(ex - 1, lane_y)

        # Trouver des cases walkable proches
        from Game.Utils.grid_utils import GridUtils
        grid_utils = GridUtils(self.app)
        
        s = grid_utils.find_walkable_near(start_anchor[0], start_anchor[1], max_r=12)
        e = grid_utils.find_walkable_near(entry_point[0], entry_point[1], max_r=12)
        x = grid_utils.find_walkable_near(exit_point[0], exit_point[1], max_r=12)
        g = grid_utils.find_walkable_near(end_anchor[0], end_anchor[1], max_r=12)

        if not s or not e or not x or not g:
            return []

        # Construire le chemin en 3 segments
        p1 = self.astar(s, e)
        p2 = self.astar(e, x)
        p3 = self.astar(x, g)

        # Assembler le chemin complet
        out = []
        if p1:
            out += p1
        if p2:
            out += p2[1:] if out else p2
        if p3:
            out += p3[1:] if out else p3

        return out

    def recalculate_all_lanes(self):
        """Recalcule tous les chemins de lanes (joueur ET ennemi)."""
        if not self.app.nav_grid:
            return
        
        # Chemins du joueur (gauche → droite)
        self.app.lane_paths = [
            self.compute_lane_route(0),
            self.compute_lane_route(1),
            self.compute_lane_route(2),
        ]
        
        # Chemins de l'ennemi = même chemin inversé
        self.app.lane_paths_enemy = [
            list(reversed(self.app.lane_paths[0])) if self.app.lane_paths[0] else [],
            list(reversed(self.app.lane_paths[1])) if self.app.lane_paths[1] else [],
            list(reversed(self.app.lane_paths[2])) if self.app.lane_paths[2] else [],
        ]
        
        # Informer LaneRouteSystem
        if hasattr(self.app, 'lane_route_system') and self.app.lane_route_system:
            self.app.lane_route_system.set_lane_paths(self.app.lane_paths)
