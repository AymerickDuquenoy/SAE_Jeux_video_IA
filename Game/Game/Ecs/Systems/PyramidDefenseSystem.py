"""
PyramidDefenseSystem - Les pyramides tirent sur les ennemis à portée.

La pyramide tire automatiquement sur l'ennemi le plus proche dans sa portée.
Respecte les règles SAÉ : tirs axiaux uniquement.
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.lifetime import Lifetime


def _sign(x: float) -> float:
    return 1.0 if x >= 0 else -1.0


class PyramidDefenseSystem(esper.Processor):
    """
    Système de défense automatique des pyramides.
    """

    def __init__(self, pyramid_ids: set[int], attack_range: float = 3.0, 
                 damage: float = 8.0, cooldown: float = 1.2, projectile_speed: float = 10.0):
        super().__init__()
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        self.attack_range = float(attack_range)
        self.damage = float(damage)
        self.cooldown = float(cooldown)
        self.projectile_speed = float(projectile_speed)
        self.align_tolerance = 0.8  # Plus tolérant pour les pyramides
        
        # Cooldown par pyramide
        self.timers = {pid: 0.0 for pid in self.pyramid_ids}

    # Mettre à jour les timers
    def process(self, dt: float):
        if dt <= 0:
            return

        # Mettre à jour les timers
        for pid in self.pyramid_ids:
            if pid in self.timers:
                self.timers[pid] = max(0.0, self.timers[pid] - dt)

        # Collecter les ennemis potentiels (unités avec UnitStats)
        enemies_by_team = {1: [], 2: []}  # team_id -> [(eid, transform)]
        for eid, (t, team, stats, hp) in esper.get_components(Transform, Team, UnitStats, Health):
            if hp.is_dead:
                continue
            if team.id in enemies_by_team:
                enemies_by_team[team.id].append((eid, t))

        # Chaque pyramide tire sur les ennemis
        for pid in self.pyramid_ids:
            if not esper.entity_exists(pid):
                continue
                
            # Vérifier cooldown
            if self.timers.get(pid, 0.0) > 0.0:
                continue

            try:
                pt = esper.component_for_entity(pid, Transform)
                pteam = esper.component_for_entity(pid, Team)
                php = esper.component_for_entity(pid, Health)
            except:
                continue

            if php.is_dead:
                continue

            px, py = pt.pos
            
            # Trouver l'ennemi le plus proche
            enemy_team = 2 if pteam.id == 1 else 1
            enemies = enemies_by_team.get(enemy_team, [])
            
            best_target = None
            best_dist = 999999.0
            best_pos = None

            for eid, et in enemies:
                ex, ey = et.pos
                d = math.hypot(ex - px, ey - py)
                
                if d <= self.attack_range and d < best_dist:
                    # Vérifier alignement axial
                    dx = ex - px
                    dy = ey - py
                    aligned_h = abs(dy) <= self.align_tolerance
                    aligned_v = abs(dx) <= self.align_tolerance
                    
                    if aligned_h or aligned_v:
                        best_dist = d
                        best_target = eid
                        best_pos = (ex, ey)

            # Tirer si cible trouvée
            if best_target is not None and best_pos is not None:
                ex, ey = best_pos
                dx = ex - px
                dy = ey - py
                
                # Direction axiale
                if abs(dy) <= self.align_tolerance:
                    fire_dx = _sign(dx)
                    fire_dy = 0.0
                else:
                    fire_dx = 0.0
                    fire_dy = _sign(dy)

                # Créer projectile
                esper.create_entity(
                    Transform(pos=(px, py)),
                    Velocity(vx=fire_dx * self.projectile_speed, vy=fire_dy * self.projectile_speed),
                    Projectile(team_id=int(pteam.id), target_entity_id=best_target, 
                              damage=self.damage, hit_radius=0.3),
                    Lifetime(ttl=3.0, despawn_on_death=False)
                )
                
                # Reset cooldown
                self.timers[pid] = self.cooldown
