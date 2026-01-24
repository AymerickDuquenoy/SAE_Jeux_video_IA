"""
CombatSystem - Gère les tirs des unités.

RÈGLES SAÉ :
1. Tirs UNIQUEMENT axiaux (horizontal OU vertical)
2. Ne tire que si ALIGNÉ avec la cible (même X ou même Y)
3. Utilise une tolérance pour l'alignement
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


def _sign(x: float) -> float:
    return 1.0 if x >= 0 else -1.0


class CombatSystem(esper.Processor):
    """Combat SAÉ : tirs axiaux uniquement, alignement requis."""

    def __init__(self, *, attack_range: float = 1.8, hit_cooldown: float = 0.6, projectile_speed: float = 12.0):
        super().__init__()
        self.attack_range = float(attack_range)
        self.hit_cooldown = float(hit_cooldown)
        self.projectile_speed = float(projectile_speed)
        self.align_tolerance = 0.5
        self._sound_manager = None
        self._shoot_sound_cooldown = 0.0

    def _get_sound_manager(self):
        if self._sound_manager is None:
            try:
                from Game.App.sound_manager import sound_manager
                self._sound_manager = sound_manager
            except:
                pass
        return self._sound_manager

    def process(self, dt: float):
        if dt <= 0:
            return

        # Cooldown son (éviter spam)
        self._shoot_sound_cooldown = max(0.0, self._shoot_sound_cooldown - dt)

        for eid, (t, team, stats, target) in esper.get_components(Transform, Team, UnitStats, Target):
            if esper.has_component(eid, AttackCooldown):
                cd = esper.component_for_entity(eid, AttackCooldown)
            else:
                cd = AttackCooldown(cooldown=self.hit_cooldown, timer=0.0)
                esper.add_component(eid, cd)

            cd.timer = max(0.0, cd.timer - dt)
            if cd.timer > 0.0:
                continue

            tid = int(target.entity_id)
            if not esper.entity_exists(tid):
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            try:
                tt = esper.component_for_entity(tid, Transform)
                th = esper.component_for_entity(tid, Health)
                tteam = esper.component_for_entity(tid, Team)
            except Exception:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            if th.is_dead or tteam.id == team.id:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            ax, ay = t.pos
            bx, by = tt.pos

            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)

            if dist > self.attack_range:
                continue

            aligned_horizontal = abs(dy) <= self.align_tolerance
            aligned_vertical = abs(dx) <= self.align_tolerance

            if not aligned_horizontal and not aligned_vertical:
                continue

            dmg = max(0.0, float(stats.power))

            if aligned_horizontal:
                fire_dx = _sign(dx)
                fire_dy = 0.0
            else:
                fire_dx = 0.0
                fire_dy = _sign(dy)

            esper.create_entity(
                Transform(pos=(ax, ay)),
                Velocity(vx=fire_dx * self.projectile_speed, vy=fire_dy * self.projectile_speed),
                Projectile(team_id=int(team.id), target_entity_id=tid, damage=dmg, hit_radius=0.25),
                Lifetime(ttl=3.0, despawn_on_death=False)
            )

            # Son de tir (limité pour éviter spam)
            if self._shoot_sound_cooldown <= 0:
                sm = self._get_sound_manager()
                if sm:
                    sm.play("shoot")
                self._shoot_sound_cooldown = 0.15

            cd.timer = cd.cooldown
