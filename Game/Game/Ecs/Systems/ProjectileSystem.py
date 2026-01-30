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
    Projectiles HOMING (suivent leur cible).
    - Recalcule la direction vers la cible à chaque frame
    - Applique les dégâts quand le projectile touche
    - Supprime le projectile si la cible meurt ou n'existe plus
    """

    # Initialise le système de projectiles avec pyramides et récompenses
    def __init__(self, pyramid_by_team: dict[int, int] | None = None, reward_divisor: float = 2.0):
        super().__init__()
        self.pyramid_by_team = pyramid_by_team or {}
        self.reward_divisor = float(reward_divisor) if float(reward_divisor) > 0 else 2.0
        self._sound_manager = None

    # Récupère l'instance du gestionnaire de sons (lazy loading)
    def _get_sound_manager(self):
        if self._sound_manager is None:
            try:
                from Game.Audio.sound_manager import sound_manager
                self._sound_manager = sound_manager
            except ImportError:
                try:
                    from Audio.sound_manager import sound_manager
                    self._sound_manager = sound_manager
                except ImportError:
                    pass
        return self._sound_manager

    # Déplace les projectiles homing vers leur cible et applique les dégâts
    def process(self, dt: float):
        if dt <= 0:
            return

        to_delete = []

        for eid, (t, v, p) in esper.get_components(Transform, Velocity, Projectile):
            tid = int(p.target_entity_id)

            # Vérifier que la cible existe
            try:
                tt = esper.component_for_entity(tid, Transform)
                th = esper.component_for_entity(tid, Health)
                tteam = esper.component_for_entity(tid, Team)
            except Exception:
                to_delete.append(eid)
                continue

            # Cible morte ou même équipe
            if th.is_dead:
                to_delete.append(eid)
                continue

            if int(tteam.id) == int(p.team_id):
                to_delete.append(eid)
                continue

            # Position actuelle du projectile et de la cible
            x, y = t.pos
            tx, ty = tt.pos
            dx = tx - x
            dy = ty - y
            dist = math.hypot(dx, dy)

            # Vérifier si on touche (hit_radius augmenté pour plus de fiabilité)
            effective_hit_radius = max(0.4, float(p.hit_radius))
            
            if dist <= effective_hit_radius:
                # TOUCHÉ !
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

                # Vérifier si la cible meurt
                if old_hp > 0 and th.hp <= 0:
                    shooter_team = int(p.team_id)
                    pyramid_eid = int(self.pyramid_by_team.get(shooter_team, 0))
                    
                    # Son de mort
                    if sm:
                        sm.play("death")

                    # Récompense
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
                continue

            # HOMING: Mettre à jour la vélocité pour suivre la cible
            if dist > 0.01:
                speed = math.hypot(v.vx, v.vy)
                if speed < 1.0:
                    speed = 12.0  # Vitesse par défaut
                v.vx = (dx / dist) * speed
                v.vy = (dy / dist) * speed

            # Déplacer le projectile
            new_x = x + v.vx * dt
            new_y = y + v.vy * dt
            t.pos = (new_x, new_y)

        # Supprimer les projectiles terminés
        for eid in set(to_delete):
            try:
                esper.delete_entity(eid, immediate=True)
            except Exception:
                pass