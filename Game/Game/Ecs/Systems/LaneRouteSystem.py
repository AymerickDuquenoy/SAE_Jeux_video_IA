# Game/Ecs/Systems/LaneRouteSystem.py
import heapq
import esper

from Game.Services.NavigationGrid import NavigationGrid

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.path import Path as PathComponent
from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.pathProgress import PathProgress


class LaneRouteSystem:
    """
    Objectif : rendre la sélection de lane VRAIMENT intuitive.
    Chaque unité suit :
      1) un waypoint sur SA lane (près de l’ennemi)
      2) puis une case d'attaque alignée avec la pyramide (haut/milieu/bas)
    """

    def __init__(
        self,
        nav: NavigationGrid,
        lanes_y: list[int],
        player_pyr: tuple[int, int],
        enemy_pyr: tuple[int, int],
        pyramid_ids: set[int],
    ):
        self.nav = nav
        self.lanes_y = list(lanes_y)
        self.player_pyr = (int(player_pyr[0]), int(player_pyr[1]))
        self.enemy_pyr = (int(enemy_pyr[0]), int(enemy_pyr[1]))
        self.pyramid_ids = set(int(x) for x in pyramid_ids)

        self.lane_by_ent = {}
        self.stage_by_ent = {}
        self.goal_by_ent = {}

    def set_lane_for_entity(self, ent: int, lane_idx: int):
        lane_idx = max(0, min(2, int(lane_idx)))
        self.lane_by_ent[int(ent)] = lane_idx
        self.stage_by_ent[int(ent)] = 0
        self.goal_by_ent[int(ent)] = None
        try:
            p = esper.component_for_entity(ent, PathComponent)
            p.noeuds = []
        except Exception:
            pass

        # ✅ reset index au changement lane (évite "décalage fin de chemin")
        try:
            prog = esper.component_for_entity(ent, PathProgress)
            prog.index = 0
        except Exception:
            try:
                esper.add_component(ent, PathProgress(index=0))
            except Exception:
                pass

    def _closest_lane_idx(self, y: int) -> int:
        best_i = 0
        best_d = 999999
        for i, ly in enumerate(self.lanes_y):
            d = abs(int(ly) - int(y))
            if d < best_d:
                best_d = d
                best_i = i
        return max(0, min(2, best_i))

    def _cell_cost(self, x: int, y: int) -> float:
        try:
            m = float(self.nav.mult[y][x])
        except Exception:
            m = 1.0
        if m <= 0.0:
            return 999999.0
        return 1.0 / max(0.05, m)

    def _astar(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        if start == goal:
            return [start]

        w = int(getattr(self.nav, "width", 0))
        h = int(getattr(self.nav, "height", 0))
        if w <= 0 or h <= 0:
            return []

        sx, sy = start
        gx, gy = goal
        if not (0 <= sx < w and 0 <= sy < h):
            return []
        if not (0 <= gx < w and 0 <= gy < h):
            return []
        if not self.nav.is_walkable(sx, sy):
            return []
        if not self.nav.is_walkable(gx, gy):
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
                if not self.nav.is_walkable(nx, ny):
                    continue

                ng = g + self._cell_cost(nx, ny)
                if (nx, ny) not in gscore or ng < gscore[(nx, ny)]:
                    gscore[(nx, ny)] = ng
                    came[(nx, ny)] = (cx, cy)
                    nf = ng + h_manh((nx, ny), (gx, gy))
                    heapq.heappush(open_heap, (nf, ng, (nx, ny)))

        return []

    def _dist(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))

    def _attack_cell(self, team_id: int, lane_idx: int) -> tuple[int, int]:
        """
        ✅ Lane 1 : attaque PAR LE HAUT
        ✅ Lane 2 : attaque AU MILIEU
        ✅ Lane 3 : attaque PAR LE BAS

        C'est ce qui évite "tir dans le vide" -> toujours aligné ligne/colonne.
        """
        w = int(getattr(self.nav, "width", 0))
        h = int(getattr(self.nav, "height", 0))
        px, py = self.player_pyr
        ex, ey = self.enemy_pyr

        if team_id == 1:
            # attaque pyramide ennemie (droite)
            if lane_idx == 0:
                ax, ay = ex, ey - 1
            elif lane_idx == 1:
                ax, ay = ex - 1, ey
            else:
                ax, ay = ex, ey + 1
        else:
            # attaque pyramide joueur (gauche)
            if lane_idx == 0:
                ax, ay = px, py - 1
            elif lane_idx == 1:
                ax, ay = px + 1, py
            else:
                ax, ay = px, py + 1

        ax = max(1, min(w - 2, int(ax)))
        ay = max(1, min(h - 2, int(ay)))
        return (ax, ay)

    def process(self, dt: float):
        for ent, (t, team, path) in esper.get_components(Transform, Team, PathComponent):
            if int(ent) in self.pyramid_ids:
                continue

            if ent not in self.lane_by_ent:
                self.lane_by_ent[ent] = self._closest_lane_idx(int(round(t.pos[1])))
                self.stage_by_ent[ent] = 0
                self.goal_by_ent[ent] = None

            lane_idx = int(self.lane_by_ent[ent])
            lane_y = int(self.lanes_y[lane_idx])

            cur = (int(round(t.pos[0])), int(round(t.pos[1])))

            # waypoint = on va sur la lane près de la pyramide
            w = max(3, int(getattr(self.nav, "width", 0)))
            if team.id == 1:
                wp = (max(1, int(self.enemy_pyr[0]) - 1), lane_y)
            else:
                wp = (min(w - 2, int(self.player_pyr[0]) + 1), lane_y)

            # ✅ case d'attaque lane (haut/milieu/bas)
            final = self._attack_cell(team.id, lane_idx)

            stage = int(self.stage_by_ent.get(ent, 0))

            if stage == 0:
                if self._dist(cur, wp) <= 1:
                    stage = 1
                    self.stage_by_ent[ent] = 1
                    try:
                        path.noeuds = []
                    except Exception:
                        pass

                    try:
                        prog = esper.component_for_entity(ent, PathProgress)
                        prog.index = 0
                    except Exception:
                        try:
                            esper.add_component(ent, PathProgress(index=0))
                        except Exception:
                            pass

            goal = wp if stage == 0 else final

            last_goal = self.goal_by_ent.get(ent, None)
            if last_goal != goal:
                self.goal_by_ent[ent] = goal
                try:
                    path.noeuds = []
                except Exception:
                    pass

            try:
                nodes = getattr(path, "noeuds", [])
            except Exception:
                nodes = []

            if not nodes:
                pts = self._astar(cur, goal)
                if pts and len(pts) >= 2:
                    gp = []
                    for (x, y) in pts:
                        gp.append(GridPosition(int(x), int(y)))
                    path.noeuds = gp

                    # ✅ reset index à chaque rebuild
                    try:
                        prog = esper.component_for_entity(ent, PathProgress)
                        prog.index = 0
                    except Exception:
                        try:
                            esper.add_component(ent, PathProgress(index=0))
                        except Exception:
                            pass
