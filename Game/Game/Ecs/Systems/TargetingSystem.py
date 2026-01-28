"""
TargetingSystem - Assigne les cibles aux unités.

RÈGLES :
1. Les troupes ciblent les ennemis sur la MÊME LANE ou proches
2. La pyramide n'est ciblée que si l'unité est ARRIVÉE (chemin terminé)
3. Priorité : troupes ennemies > pyramide
4. TOUTES les unités (Momie, Dromadaire, Sphinx) se défendent
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.lane import Lane


class TargetingSystem(esper.Processor):
    """
    Assigne les cibles en utilisant le composant Lane.index.
    Toutes les unités peuvent cibler et attaquer les ennemis.
    """

    def __init__(self, *, goals_by_team: dict, pyramid_ids: set[int], attack_range: float = 2.0):
        super().__init__()
        self.goals_by_team = goals_by_team
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        self.attack_range = float(attack_range)

    def _get_lane_index(self, ent: int) -> int:
        """Retourne l'index de lane (-1 si pas de lane)."""
        if esper.has_component(ent, Lane):
            return esper.component_for_entity(ent, Lane).index
        return -1

    def _is_arrived(self, ent: int) -> bool:
        """Vérifie si l'unité est arrivée à destination."""
        if not esper.has_component(ent, Path):
            return True
        
        path = esper.component_for_entity(ent, Path)
        nodes = getattr(path, "noeuds", [])
        
        if not nodes:
            return True
        
        if esper.has_component(ent, PathProgress):
            prog = esper.component_for_entity(ent, PathProgress)
            if prog.index >= len(nodes) - 1:
                return True
        
        return False

    def process(self, dt: float):
        # Collecter toutes les cibles potentielles avec leur lane
        candidates = []
        for eid, (t, team, hp) in esper.get_components(Transform, Team, Health):
            if hp.is_dead:
                continue
            is_pyramid = (eid in self.pyramid_ids)
            lane_idx = self._get_lane_index(eid) if not is_pyramid else -1
            candidates.append((eid, t, team, is_pyramid, lane_idx))

        # Pour chaque unité
        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if esper.has_component(eid, Health):
                if esper.component_for_entity(eid, Health).is_dead:
                    continue

            ax, ay = t.pos
            my_lane = self._get_lane_index(eid)
            
            best_unit_id = None
            best_unit_dist = 999999.0
            
            best_pyramid_id = None
            best_pyramid_dist = 999999.0

            for cid, ct, cteam, is_pyramid, enemy_lane in candidates:
                if cid == eid:
                    continue
                if cteam.id == team.id:
                    continue

                bx, by = ct.pos
                d = math.hypot(bx - ax, by - ay)

                if d > self.attack_range:
                    continue

                if is_pyramid:
                    if d < best_pyramid_dist:
                        best_pyramid_dist = d
                        best_pyramid_id = cid
                else:
                    # Logique de ciblage par lane :
                    # 1. Même Lane.index → cibler
                    # 2. Lanes différentes MAIS très proches (chemins croisés) → cibler aussi
                    same_lane = False
                    
                    if my_lane >= 0 and enemy_lane >= 0:
                        if my_lane == enemy_lane:
                            same_lane = True
                        elif abs(ay - by) <= 1.0:
                            # Chemins qui se croisent - assez proches pour combattre
                            same_lane = True
                    else:
                        # Fallback: comparer Y si pas de lane assignée
                        if abs(ay - by) <= 1.0:
                            same_lane = True
                    
                    if not same_lane:
                        continue
                    
                    if d < best_unit_dist:
                        best_unit_dist = d
                        best_unit_id = cid

            # Décision de ciblage - MÊME LOGIQUE POUR TOUTES LES UNITÉS
            # Priorité aux troupes ennemies, puis pyramide si arrivé
            if best_unit_id is not None:
                self._set_target(eid, best_unit_id, "unit")
            elif best_pyramid_id is not None and self._is_arrived(eid):
                self._set_target(eid, best_pyramid_id, "pyramid")
            else:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)

    def _set_target(self, eid: int, target_id: int, target_type: str):
        """Assigne ou met à jour la cible d'une unité."""
        if esper.has_component(eid, Target):
            tg = esper.component_for_entity(eid, Target)
            tg.entity_id = int(target_id)
            tg.type = target_type
        else:
            esper.add_component(eid, Target(entity_id=int(target_id), type=target_type))
