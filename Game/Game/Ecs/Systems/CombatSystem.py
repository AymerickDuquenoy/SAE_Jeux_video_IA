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
    """
    Combat SAÉ strict :
    - tirs UNIQUEMENT en axe (longitudinal / latéral)
    - pas de tir si la cible n'est pas alignée (sinon ça tire dans le vide)
    """

    def __init__(self, *, attack_range: float = 0.85, hit_cooldown: float = 0.7, projectile_speed: float = 10.0):
        super().__init__()
        self.attack_range = float(attack_range)
        self.hit_cooldown = float(hit_cooldown)
        self.projectile_speed = float(projectile_speed)

        # tolérance d'alignement (évite les floats)
        # si dx est presque 0 -> aligné vertical, si dy presque 0 -> aligné horizontal
        self.align_eps = 0.25

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

            cd.timer = max(0.0, cd.timer - dt)
            if cd.timer > 0.0:
                continue

            tid = int(target.entity_id)
            if not esper.entity_exists(tid):
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            # target existe ?
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

            # ✅ SAÉ : PAS DE TIR SI PAS ALIGNÉ (évite tirs dans le vide)
            aligned_h = abs(dy) <= self.align_eps   # même ligne -> tir horizontal
            aligned_v = abs(dx) <= self.align_eps   # même colonne -> tir vertical

            if not aligned_h and not aligned_v:
                # pas aligné => on ne tire pas, l'unité continue d'avancer pour se placer
                continue

            # dégâts (P0 SAÉ strict) : un coup au but retire P
            dmg = float(stats.power)
            if dmg < 0:
                dmg = 0.0

            # direction STRICTEMENT axiale vers la cible
            if aligned_h:
                # horizontal (gauche/droite)
                dirx, diry = _sign(dx), 0.0
            else:
                # vertical (haut/bas)
                dirx, diry = 0.0, _sign(dy)

            pvx = dirx * self.projectile_speed
            pvy = diry * self.projectile_speed

            esper.create_entity(
                Transform(pos=(ax, ay)),
                Velocity(vx=pvx, vy=pvy),
                Projectile(team_id=int(team.id), target_entity_id=tid, damage=float(dmg), hit_radius=0.18),
                Lifetime(ttl=2.0, despawn_on_death=False)
            )

            cd.timer = cd.cooldown
