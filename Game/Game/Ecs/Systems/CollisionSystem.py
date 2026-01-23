# Game/Ecs/Systems/CollisionSystem.py
"""
Système de collision SAÉ:
- Empêche les unités de se traverser
- Bloque les unités ennemies face à face sur une même lane
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target


class CollisionSystem(esper.Processor):
    """
    Gère les collisions entre unités:
    - Les unités ennemies se bloquent mutuellement
    - Évite les superpositions
    """

    def __init__(self, *, collision_radius: float = 0.4, separation_force: float = 2.0):
        super().__init__()
        self.collision_radius = float(collision_radius)
        self.separation_force = float(separation_force)

    def process(self, dt: float):
        if dt <= 0:
            return

        # Récupère toutes les unités vivantes (avec UnitStats = pas une pyramide)
        units = []
        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue
            units.append((eid, t, team))

        # Vérifie les collisions entre chaque paire
        n = len(units)
        for i in range(n):
            eid_a, t_a, team_a = units[i]
            ax, ay = t_a.pos

            for j in range(i + 1, n):
                eid_b, t_b, team_b = units[j]
                bx, by = t_b.pos

                dx = bx - ax
                dy = by - ay
                dist = math.hypot(dx, dy)

                # Collision détectée
                if dist < self.collision_radius * 2:
                    if dist < 0.01:
                        # Évite division par zéro - décale légèrement
                        dx, dy = 0.1, 0.0
                        dist = 0.1

                    # Calcule la séparation nécessaire
                    overlap = (self.collision_radius * 2) - dist
                    if overlap > 0:
                        # Direction de séparation (normalisée)
                        nx = dx / dist
                        ny = dy / dist

                        # Force de séparation
                        sep = overlap * self.separation_force * dt

                        # Si ennemis: les deux s'arrêtent et se séparent légèrement
                        # Si alliés: juste se décalent pour éviter superposition
                        if team_a.id != team_b.id:
                            # ENNEMIS: collision frontale = STOP + légère séparation
                            # Stoppe les deux
                            if esper.has_component(eid_a, Velocity):
                                v_a = esper.component_for_entity(eid_a, Velocity)
                                v_a.vx = 0.0
                                v_a.vy = 0.0
                            if esper.has_component(eid_b, Velocity):
                                v_b = esper.component_for_entity(eid_b, Velocity)
                                v_b.vx = 0.0
                                v_b.vy = 0.0

                            # ✅ FIX SAÉ: Assigner les cibles mutuellement pour déclencher le combat
                            if not esper.has_component(eid_a, Target):
                                esper.add_component(eid_a, Target(entity_id=eid_b, type="unit"))
                            if not esper.has_component(eid_b, Target):
                                esper.add_component(eid_b, Target(entity_id=eid_a, type="unit"))

                            # Sépare légèrement pour éviter chevauchement
                            half_sep = sep * 0.5
                            t_a.pos = (ax - nx * half_sep, ay - ny * half_sep)
                            t_b.pos = (bx + nx * half_sep, by + ny * half_sep)

                        else:
                            # ALLIÉS: se décalent latéralement (perpendiculaire)
                            # Pour éviter les embouteillages
                            perp_x = -ny
                            perp_y = nx
                            half_sep = sep * 0.3
                            t_a.pos = (ax - perp_x * half_sep, ay - perp_y * half_sep)
                            t_b.pos = (bx + perp_x * half_sep, by + perp_y * half_sep)
