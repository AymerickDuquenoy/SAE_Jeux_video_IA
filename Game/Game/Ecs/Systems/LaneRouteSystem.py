# Game/Ecs/Systems/LaneRouteSystem.py
"""
LaneRouteSystem - Assigne les chemins pré-calculés aux unités.

PRINCIPE : Les chemins A* sont calculés UNE SEULE FOIS dans game_app._recalculate_all_lanes()
et ce système les assigne aux unités selon leur lane et leur équipe.

- Joueur (team 1) : utilise lane_paths[lane_idx]
- Ennemi (team 2) : utilise lane_paths[lane_idx] INVERSÉ
"""
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.path import Path as PathComponent
from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.lane import Lane


class LaneRouteSystem:
    """
    Assigne les chemins pré-calculés (lane_paths) aux unités.
    """

    def __init__(
        self,
        lanes_y: list[int],
        pyramid_ids: set[int],
    ):
        self.lanes_y = list(lanes_y)
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        
        # Chemins pré-calculés (seront mis à jour par game_app)
        self.lane_paths = [[], [], []]  # Joueur → Ennemi
        
        # Tracking des unités
        self.assigned_ents = set()

    def set_lane_paths(self, lane_paths: list):
        """Met à jour les chemins pré-calculés (appelé par game_app)."""
        self.lane_paths = [list(p) for p in lane_paths] if lane_paths else [[], [], []]
        
        # Forcer le recalcul des chemins pour toutes les unités
        self.assigned_ents.clear()

    def set_lane_for_entity(self, ent: int, lane_idx: int):
        """Assigne une lane à une unité et lui donne le chemin correspondant."""
        lane_idx = max(0, min(2, int(lane_idx)))
        
        # Mettre à jour le composant Lane
        lane_y = float(self.lanes_y[lane_idx])
        try:
            if esper.has_component(ent, Lane):
                lc = esper.component_for_entity(ent, Lane)
                lc.index = lane_idx
                lc.y_position = lane_y
            else:
                esper.add_component(ent, Lane(index=lane_idx, y_position=lane_y))
        except:
            pass
        
        # Forcer la réassignation du chemin
        self.assigned_ents.discard(int(ent))

    def _closest_lane_idx(self, y: int) -> int:
        """Trouve la lane la plus proche de la position Y."""
        best_i = 0
        best_d = 999999
        for i, ly in enumerate(self.lanes_y):
            d = abs(int(ly) - int(y))
            if d < best_d:
                best_d = d
                best_i = i
        return max(0, min(2, best_i))

    def _find_closest_point_on_path(self, pos: tuple, path: list) -> int:
        """Trouve l'index du point le plus proche sur le chemin."""
        if not path:
            return 0
        
        px, py = pos
        best_idx = 0
        best_dist = 999999
        
        for i, (x, y) in enumerate(path):
            d = abs(x - px) + abs(y - py)
            if d < best_dist:
                best_dist = d
                best_idx = i
        
        return best_idx

    def process(self, dt: float):
        # Nettoyer les entités qui n'existent plus
        dead_ents = [ent for ent in self.assigned_ents if not esper.entity_exists(ent)]
        for ent in dead_ents:
            self.assigned_ents.discard(ent)
        
        for ent, (t, team, path) in esper.get_components(Transform, Team, PathComponent):
            if int(ent) in self.pyramid_ids:
                continue
            
            # Si déjà assigné et a un chemin, ne pas toucher
            if int(ent) in self.assigned_ents:
                nodes = getattr(path, "noeuds", [])
                if nodes:
                    continue
            
            # Déterminer la lane
            if esper.has_component(ent, Lane):
                lc = esper.component_for_entity(ent, Lane)
                lane_idx = lc.index
            else:
                # Assigner basé sur la position Y
                lane_idx = self._closest_lane_idx(int(round(t.pos[1])))
                lane_y = float(self.lanes_y[lane_idx])
                esper.add_component(ent, Lane(index=lane_idx, y_position=lane_y))
            
            lane_idx = max(0, min(2, lane_idx))
            
            # Récupérer le chemin pré-calculé
            if not self.lane_paths or lane_idx >= len(self.lane_paths):
                continue
            
            base_path = self.lane_paths[lane_idx]
            if not base_path:
                continue
            
            # Pour l'ennemi (team 2), inverser le chemin
            if team.id == 2:
                full_path = list(reversed(base_path))
            else:
                full_path = list(base_path)
            
            if not full_path:
                continue
            
            # Trouver où l'unité se trouve sur le chemin
            cur_pos = (int(round(t.pos[0])), int(round(t.pos[1])))
            start_idx = self._find_closest_point_on_path(cur_pos, full_path)
            
            # Prendre le chemin à partir de la position actuelle
            remaining_path = full_path[start_idx:]
            
            if len(remaining_path) < 2:
                remaining_path = full_path  # Fallback au chemin complet
            
            # Assigner le chemin
            gp_nodes = [GridPosition(int(x), int(y)) for (x, y) in remaining_path]
            path.noeuds = gp_nodes
            
            # Reset progress
            try:
                if esper.has_component(ent, PathProgress):
                    prog = esper.component_for_entity(ent, PathProgress)
                    prog.index = 0
                else:
                    esper.add_component(ent, PathProgress(index=0))
            except:
                pass
            
            self.assigned_ents.add(int(ent))
