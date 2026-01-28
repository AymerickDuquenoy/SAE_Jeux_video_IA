"""
CombatSystem - Gère les tirs des unités.

Projectiles HOMING - les unités tirent directement vers leur cible,
les projectiles suivent la cible jusqu'à l'impact.
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


class CombatSystem(esper.Processor):
    """Combat avec projectiles homing - tire dès qu'une cible est à portée."""

    def __init__(self, *, attack_range: float = 2.0, hit_cooldown: float = 0.6, projectile_speed: float = 12.0, align_tolerance: float = 0.5):
        super().__init__()
        self.attack_range = float(attack_range)
        self.hit_cooldown = float(hit_cooldown)
        self.projectile_speed = float(projectile_speed)
        self.align_tolerance = float(align_tolerance)  # Gardé pour compatibilité mais non utilisé
        self._sound_manager = None
        self._shoot_sound_cooldown = 0.0

    def _get_sound_manager(self):
        if self._sound_manager is None:
            try:
                from Game.Audio.sound_manager import sound_manager
                self._sound_manager = sound_manager
            except ImportError:
                try:
                    # Fallback si structure différente
                    from Audio.sound_manager import sound_manager
                    self._sound_manager = sound_manager
                except ImportError:
                    pass
        return self._sound_manager

    def process(self, dt: float):
        if dt <= 0:
            return

        # Cooldown son (éviter spam)
        self._shoot_sound_cooldown = max(0.0, self._shoot_sound_cooldown - dt)

        for eid, (t, team, stats, target) in esper.get_components(Transform, Team, UnitStats, Target):
            # Gérer le cooldown d'attaque
            if esper.has_component(eid, AttackCooldown):
                cd = esper.component_for_entity(eid, AttackCooldown)
            else:
                cd = AttackCooldown(cooldown=self.hit_cooldown, timer=0.0)
                esper.add_component(eid, cd)

            cd.timer = max(0.0, cd.timer - dt)
            if cd.timer > 0.0:
                continue

            # Vérifier que la cible existe
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

            # Cible morte ou même équipe
            if th.is_dead or tteam.id == team.id:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue

            # Calculer la distance
            ax, ay = t.pos
            bx, by = tt.pos
            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)

            # Vérifier la portée
            if dist > self.attack_range:
                continue

            # TIRER ! Direction initiale vers la cible (projectile homing fera le reste)
            dmg = max(0.0, float(stats.power))
            
            if dist > 0.01:
                fire_dx = (dx / dist) * self.projectile_speed
                fire_dy = (dy / dist) * self.projectile_speed
            else:
                fire_dx = self.projectile_speed
                fire_dy = 0.0

            # Créer le projectile
            esper.create_entity(
                Transform(pos=(ax, ay)),
                Velocity(vx=fire_dx, vy=fire_dy),
                Projectile(team_id=int(team.id), target_entity_id=tid, damage=dmg, hit_radius=0.4),
                Lifetime(ttl=5.0, despawn_on_death=False)
            )

            # Son de tir (limité pour éviter spam)
            if self._shoot_sound_cooldown <= 0:
                sm = self._get_sound_manager()
                if sm:
                    sm.play("shoot")
                self._shoot_sound_cooldown = 0.15

            # Reset cooldown
            cd.timer = cd.cooldown
