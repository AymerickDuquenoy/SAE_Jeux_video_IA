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
        self._sound_manager = None

    def _get_sound_manager(self):
        if self._sound_manager is None:
            try:
                from Game.Audio.sound_manager import sound_manager
                self._sound_manager = sound_manager
            except:
                pass
        return self._sound_manager

    def process(self, dt: float):
        if dt <= 0:
            return

        to_delete = []

        for eid, (t, v, p) in esper.get_components(Transform, Velocity, Projectile):
            x, y = t.pos
            t.pos = (x + v.vx * dt, y + v.vy * dt)

            tid = int(p.target_entity_id)

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

            if int(tteam.id) == int(p.team_id):
                to_delete.append(eid)
                continue

            dx = tt.pos[0] - t.pos[0]
            dy = tt.pos[1] - t.pos[1]
            dist = math.hypot(dx, dy)

            if dist <= float(p.hit_radius):
                dmg = float(p.damage)
                dmg_points = int(round(dmg))
                if dmg_points < 0:
                    dmg_points = 0

                old_hp = int(th.hp)
                th.hp = max(0, int(th.hp - dmg_points))
                
                # Son de hit
                sm = self._get_sound_manager()
                if sm:
                    sm.play("hit")

                if old_hp > 0 and th.hp <= 0:
                    shooter_team = int(p.team_id)
                    pyramid_eid = int(self.pyramid_by_team.get(shooter_team, 0))
                    
                    # Son de mort
                    if sm:
                        sm.play("death")

                    if pyramid_eid != 0:
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
