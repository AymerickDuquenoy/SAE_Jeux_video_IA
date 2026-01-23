# Game/Ecs/Systems/SimpleCombatSystem.py
"""
SimpleCombatSystem - Combat avec tirs axiaux (SAÉ).
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.attack_cooldown import AttackCooldown
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.lifetime import Lifetime


class SimpleCombatSystem(esper.Processor):
    """
    Combat SAÉ : tirs axiaux uniquement.
    """

    def __init__(
        self,
        *,
        attack_range: float = 2.0,
        hit_cooldown: float = 0.5,
        projectile_speed: float = 12.0,
    ):
        super().__init__()
        self.attack_range = float(attack_range)
        self.hit_cooldown = float(hit_cooldown)
        self.projectile_speed = float(projectile_speed)

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats, target) in esper.get_components(Transform, Team, UnitStats, Target):
            # Skip morts
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue

            # Cooldown
            if esper.has_component(eid, AttackCooldown):
                cd = esper.component_for_entity(eid, AttackCooldown)
            else:
                cd = AttackCooldown(cooldown=self.hit_cooldown, timer=0.0)
                esper.add_component(eid, cd)

            cd.timer = max(0.0, cd.timer - dt)
            if cd.timer > 0.0:
                continue

            # Vérifier cible
            tid = int(target.entity_id)
            if not esper.entity_exists(tid):
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            try:
                tt = esper.component_for_entity(tid, Transform)
                th = esper.component_for_entity(tid, Health)
                tteam = esper.component_for_entity(tid, Team)
            except:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            if th.is_dead or tteam.id == team.id:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            # Distance
            ax, ay = t.pos
            bx, by = tt.pos
            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)

            if dist > self.attack_range:
                continue

            # SAÉ : Tir AXIAL
            if abs(dx) >= abs(dy):
                dir_x = 1.0 if dx >= 0 else -1.0
                dir_y = 0.0
            else:
                dir_x = 0.0
                dir_y = 1.0 if dy >= 0 else -1.0

            # Créer projectile
            dmg = float(stats.power)
            pvx = dir_x * self.projectile_speed
            pvy = dir_y * self.projectile_speed

            esper.create_entity(
                Transform(pos=(ax, ay)),
                Velocity(vx=pvx, vy=pvy),
                Projectile(
                    team_id=int(team.id),
                    target_entity_id=tid,
                    damage=float(dmg),
                    hit_radius=0.3
                ),
                Lifetime(ttl=2.0, despawn_on_death=False)
            )

            cd.timer = cd.cooldown
