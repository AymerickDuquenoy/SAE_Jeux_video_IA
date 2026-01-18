import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.unitStats import UnitStats


class ProjectileSystem(esper.Processor):
    """
    - Déplace les projectiles via Velocity
    - Si le projectile touche sa cible => applique les dégâts + delete projectile
    - Si la cible n'existe plus => delete projectile
    """

    def __init__(self, pyramid_by_team: dict[int, int] | None = None, reward_divisor: float = 2.0):
        super().__init__()
        self.pyramid_by_team = pyramid_by_team or {}
        self.reward_divisor = float(reward_divisor) if float(reward_divisor) > 0 else 2.0

    def process(self, dt: float):
        if dt <= 0:
            return

        to_delete = []

        for eid, (t, v, p) in esper.get_components(Transform, Velocity, Projectile):
            # move
            x, y = t.pos
            t.pos = (x + v.vx * dt, y + v.vy * dt)

            tid = int(p.target_entity_id)

            # cible encore valide ?
            try:
                tt = esper.component_for_entity(tid, Transform)
                th = esper.component_for_entity(tid, Health)
                tteam = esper.component_for_entity(tid, Team)
            except Exception:
                to_delete.append(eid)
                continue

            if th.is_dead:
                to_delete.append(eid)
                continue

            # sécurité : pas de friendly fire
            if int(tteam.id) == int(p.team_id):
                to_delete.append(eid)
                continue

            dx = tt.pos[0] - t.pos[0]
            dy = tt.pos[1] - t.pos[1]
            dist = math.hypot(dx, dy)

            if dist <= float(p.hit_radius):
                # impact => dégâts (P0 SAÉ strict)
                dmg = float(p.damage)
                dmg_points = int(round(dmg))
                if dmg_points < 0:
                    dmg_points = 0

                old_hp = int(th.hp)
                th.hp = max(0, int(th.hp - dmg_points))

                # reward Ce/m seulement si la cible vient de mourir (old_hp > 0 et new_hp == 0)
                if old_hp > 0 and th.hp <= 0:
                    shooter_team = int(p.team_id)
                    pyramid_eid = int(self.pyramid_by_team.get(shooter_team, 0))

                    if pyramid_eid != 0:
                        # Ce = cost de l'entité détruite (si unité)
                        ce = 0.0
                        if esper.has_component(tid, UnitStats):
                            ce = float(esper.component_for_entity(tid, UnitStats).cost)

                        if ce > 0:
                            try:
                                wallet = esper.component_for_entity(pyramid_eid, Wallet)
                                wallet.solde += (ce / self.reward_divisor)
                            except Exception:
                                pass

                to_delete.append(eid)

        for eid in set(to_delete):
            try:
                esper.delete_entity(eid, immediate=True)
            except Exception:
                pass
