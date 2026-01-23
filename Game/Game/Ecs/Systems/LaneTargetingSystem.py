"""
LaneTargetingSystem - Ciblage des ennemis.

Ce système trouve et assigne des cibles aux unités.
Comportements selon le type d'unité:
- Momie/Dromadaire: cible l'ennemi le plus proche
- Sphinx: cible uniquement la pyramide ennemie
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target


class LaneTargetingSystem(esper.Processor):
    """
    Système de ciblage des ennemis.
    
    Trouve la cible la plus appropriée pour chaque unité:
    - Unités normales: ennemi le plus proche à portée
    - Sphinx (unitType='L'): pyramide ennemie uniquement
    """

    def __init__(
        self,
        *,
        pyramid_ids: set,
        pyramid_positions: dict,  # {team_id: (x, y)}
        lanes_y: list,
        attack_range: float = 2.5,
        lane_tolerance: float = 1.5,
    ):
        super().__init__()
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        self.pyramid_positions = {int(k): v for k, v in pyramid_positions.items()}
        self.lanes_y = [float(y) for y in lanes_y]
        self.attack_range = float(attack_range)
        self.lane_tolerance = float(lane_tolerance)

    def _get_enemy_pyramid_id(self, my_team: int) -> int:
        """Retourne l'ID de la pyramide ennemie."""
        enemy_team = 2 if my_team == 1 else 1
        
        for pid in self.pyramid_ids:
            try:
                pteam = esper.component_for_entity(pid, Team)
                if pteam.id == enemy_team:
                    return pid
            except:
                pass
        
        return -1

    def _get_enemy_pyramid_position(self, my_team: int) -> tuple:
        """Retourne la position de la pyramide ennemie."""
        enemy_team = 2 if my_team == 1 else 1
        return self.pyramid_positions.get(enemy_team, (0, 0))

    def _find_closest_enemy(self, eid: int, x: float, y: float, my_team: int, unit_type: str) -> int:
        """
        Trouve l'ennemi le plus proche à portée.
        
        Pour le Sphinx (type L), ne retourne que la pyramide.
        Pour les autres, cherche l'unité ennemie la plus proche.
        """
        # Sphinx = siège, va directement à la pyramide
        if unit_type == 'L':
            pyramid_id = self._get_enemy_pyramid_id(my_team)
            if pyramid_id >= 0:
                px, py = self._get_enemy_pyramid_position(my_team)
                dist = math.hypot(px - x, py - y)
                # Portée étendue pour la pyramide
                if dist <= self.attack_range + 1.0:
                    return pyramid_id
            return -1
        
        # Pour Momie et Dromadaire: chercher l'ennemi le plus proche
        closest_id = -1
        closest_dist = float('inf')
        
        for other_eid, (ot, oteam, ohp) in esper.get_components(Transform, Team, Health):
            # Skip soi-même
            if other_eid == eid:
                continue
            
            # Skip alliés
            if oteam.id == my_team:
                continue
            
            # Skip morts
            if ohp.is_dead:
                continue
            
            ox, oy = ot.pos
            dist = math.hypot(ox - x, oy - y)
            
            # Vérifier la portée
            if dist > self.attack_range:
                continue
            
            # Priorité aux unités sur la même lane
            same_lane = abs(oy - y) <= self.lane_tolerance
            
            if same_lane and dist < closest_dist:
                closest_dist = dist
                closest_id = other_eid
        
        # Si pas d'ennemi sur la lane, chercher n'importe quel ennemi proche
        if closest_id < 0:
            for other_eid, (ot, oteam, ohp) in esper.get_components(Transform, Team, Health):
                if other_eid == eid:
                    continue
                if oteam.id == my_team:
                    continue
                if ohp.is_dead:
                    continue
                
                ox, oy = ot.pos
                dist = math.hypot(ox - x, oy - y)
                
                if dist <= self.attack_range and dist < closest_dist:
                    closest_dist = dist
                    closest_id = other_eid
        
        # Si toujours pas de cible et proche de la pyramide, cibler la pyramide
        if closest_id < 0:
            pyramid_id = self._get_enemy_pyramid_id(my_team)
            if pyramid_id >= 0:
                px, py = self._get_enemy_pyramid_position(my_team)
                dist = math.hypot(px - x, py - y)
                if dist <= self.attack_range + 0.5:
                    return pyramid_id
        
        return closest_id

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            # Skip pyramides
            if eid in self.pyramid_ids:
                continue
            
            # Skip morts
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue
            
            x, y = t.pos
            unit_type = getattr(stats, 'unit_type', 'S')
            
            # Vérifier la cible actuelle
            if esper.has_component(eid, Target):
                current_target = esper.component_for_entity(eid, Target)
                tid = int(current_target.entity_id)
                
                # Vérifier si la cible est toujours valide
                if esper.entity_exists(tid):
                    try:
                        tt = esper.component_for_entity(tid, Transform)
                        
                        # Vérifier si c'est une pyramide ou une unité
                        if tid in self.pyramid_ids:
                            # Pyramide - toujours valide si elle existe
                            th = esper.component_for_entity(tid, Health)
                            if not th.is_dead:
                                continue  # Garder la cible
                        else:
                            # Unité - vérifier qu'elle est vivante et à portée
                            th = esper.component_for_entity(tid, Health)
                            if not th.is_dead:
                                tx, ty = tt.pos
                                dist = math.hypot(tx - x, ty - y)
                                if dist <= self.attack_range + 0.5:
                                    continue  # Garder la cible
                    except:
                        pass
                
                # Cible invalide, la supprimer
                esper.remove_component(eid, Target)
            
            # Chercher une nouvelle cible
            target_id = self._find_closest_enemy(eid, x, y, team.id, unit_type)
            
            if target_id >= 0:
                esper.add_component(eid, Target(entity_id=target_id))
