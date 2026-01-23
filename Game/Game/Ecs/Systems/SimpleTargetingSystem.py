# Game/Ecs/Systems/SimpleTargetingSystem.py
"""
SimpleTargetingSystem - Ciblage de l'ennemi le plus proche.
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target


class SimpleTargetingSystem(esper.Processor):
    """
    Ciblage simple : vise l'ennemi le plus proche à portée.
    """

    def __init__(self, *, attack_range: float = 2.0, pyramid_ids: dict = None):
        super().__init__()
        self.attack_range = float(attack_range)
        self.pyramid_ids = pyramid_ids or {}

    def process(self, dt: float):
        if dt <= 0:
            return

        # Collecter toutes les entités vivantes par équipe
        team1_units = []  # (eid, x, y)
        team2_units = []
        
        for eid, (t, team, hp) in esper.get_components(Transform, Team, Health):
            if hp.is_dead:
                continue
            x, y = t.pos
            if team.id == 1:
                team1_units.append((eid, x, y))
            else:
                team2_units.append((eid, x, y))

        # Pour chaque unité avec UnitStats, trouver une cible
        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            # Skip pyramides (elles ne ciblent pas)
            if eid in self.pyramid_ids.values():
                continue
                
            # Skip morts
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    if esper.has_component(eid, Target):
                        esper.remove_component(eid, Target)
                    continue

            x, y = t.pos
            
            # Chercher l'ennemi le plus proche
            enemies = team2_units if team.id == 1 else team1_units
            
            best_target = None
            best_dist = float('inf')
            
            for enemy_eid, ex, ey in enemies:
                if enemy_eid == eid:
                    continue
                    
                dist = math.hypot(ex - x, ey - y)
                
                if dist <= self.attack_range and dist < best_dist:
                    best_dist = dist
                    best_target = enemy_eid

            # Mettre à jour la cible
            if best_target is not None:
                if esper.has_component(eid, Target):
                    target = esper.component_for_entity(eid, Target)
                    target.entity_id = best_target
                else:
                    esper.add_component(eid, Target(entity_id=best_target))
            else:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
