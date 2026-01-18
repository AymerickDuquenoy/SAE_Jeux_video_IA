import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.attack_cooldown import AttackCooldown
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.lifetime import Lifetime


class CombatSystem(esper.Processor):
    """
    Combat Phase 1 (sans IA) :

    - Si Target dans range => spawn un projectile
    - Dégâts = power (P)  [P0: SAÉ strict, coups au but]
    - Cooldown par entité
    - Projectiles : tir "longitudinal" (dans l'axe du mouvement) OU "latéral" (perpendiculaire),
      pour coller au cadre SAÉ (longitudinaux | latéraux).
    """

    def __init__(self, *, attack_range: float = 0.85, hit_cooldown: float = 0.7, projectile_speed: float = 10.0):
        super().__init__()
        self.attack_range = float(attack_range)
        self.hit_cooldown = float(hit_cooldown)
        self.projectile_speed = float(projectile_speed)

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats, target) in esper.get_components(Transform, Team, UnitStats, Target):
            # cooldown
            if esper.has_component(eid, AttackCooldown):
                cd = esper.component_for_entity(eid, AttackCooldown)
            else:
                cd = AttackCooldown(cooldown=self.hit_cooldown, timer=0.0)
                esper.add_component(eid, cd)

            if cd.timer > 0.0:
                cd.timer = max(0.0, cd.timer - dt)
                continue

            tid = int(target.entity_id)

            # target existe ?
            try:
                tt = esper.component_for_entity(tid, Transform)
                th = esper.component_for_entity(tid, Health)
                tteam = esper.component_for_entity(tid, Team)
            except Exception:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            if th.is_dead:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            if tteam.id == team.id:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            ax, ay = t.pos
            bx, by = tt.pos
            dist = math.hypot(bx - ax, by - ay)

            if dist > self.attack_range:
                continue

            # stop déplacement pendant tir (plus stable)
            if esper.has_component(eid, Path):
                esper.remove_component(eid, Path)
            if esper.has_component(eid, PathProgress):
                esper.remove_component(eid, PathProgress)

            # dégâts (P0 SAÉ strict) : un coup au but retire P
            dmg = float(stats.power)
            if dmg < 0:
                dmg = 0.0

            # direction vers la cible (normalisée)
            if dist <= 0.0001:
                continue
            tx = (bx - ax) / dist
            ty = (by - ay) / dist

            # heading (direction du mouvement) si possible
            hx, hy = 0.0, 0.0
            if esper.has_component(eid, Velocity):
                v = esper.component_for_entity(eid, Velocity)
                vlen = math.hypot(v.vx, v.vy)
                if vlen > 1e-6:
                    hx = v.vx / vlen
                    hy = v.vy / vlen

            # si pas de heading (à l'arrêt), on prend vers la cible
            if abs(hx) < 1e-6 and abs(hy) < 1e-6:
                hx, hy = tx, ty

            # choisir tir longitudinal ou latéral :
            # longitudinal si la cible est "assez" dans l'axe du heading
            dot = abs(hx * tx + hy * ty)

            if dot >= 0.707:  # ~45°
                # longitudinal (dans l'axe)
                dirx, diry = hx, hy
            else:
                # latéral (perpendiculaire) : on prend le côté qui pointe le + vers la cible
                lx1, ly1 = -hy, hx
                lx2, ly2 = hy, -hx
                d1 = lx1 * tx + ly1 * ty
                d2 = lx2 * tx + ly2 * ty
                if d1 >= d2:
                    dirx, diry = lx1, ly1
                else:
                    dirx, diry = lx2, ly2

            pvx = dirx * self.projectile_speed
            pvy = diry * self.projectile_speed

            esper.create_entity(
                Transform(pos=(ax, ay)),
                Velocity(vx=pvx, vy=pvy),
                Projectile(team_id=int(team.id), target_entity_id=tid, damage=float(dmg), hit_radius=0.18),
                Lifetime(ttl=2.0, despawn_on_death=False)
            )

            cd.timer = cd.cooldown
