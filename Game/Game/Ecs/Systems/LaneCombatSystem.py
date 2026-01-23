"""
LaneCombatSystem - Combat avec tirs axiaux (contrainte SAÉ).

Les unités tirent des projectiles vers leurs cibles.
Les tirs sont AXIAUX (horizontaux ou verticaux uniquement).
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
    """Retourne le signe d'un nombre."""
    return 1.0 if x >= 0 else -1.0


class LaneCombatSystem(esper.Processor):
    """
    Système de combat.
    
    - Crée des projectiles quand une unité tire sur sa cible
    - Tirs AXIAUX uniquement (horizontal ou vertical)
    - Respecte le cooldown entre les tirs
    """

    def __init__(
        self,
        *,
        attack_range: float = 2.5,
        hit_cooldown: float = 0.7,
        projectile_speed: float = 12.0,
    ):
        super().__init__()
        self.attack_range = float(attack_range)
        self.hit_cooldown = float(hit_cooldown)
        self.projectile_speed = float(projectile_speed)
        
        # Tolérance pour considérer l'alignement
        self.align_eps = 0.8  # Plus permissif pour éviter les tirs dans le vide

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats, target) in esper.get_components(Transform, Team, UnitStats, Target):
            # Gestion du cooldown
            if esper.has_component(eid, AttackCooldown):
                cd = esper.component_for_entity(eid, AttackCooldown)
            else:
                cd = AttackCooldown(cooldown=self.hit_cooldown, timer=0.0)
                esper.add_component(eid, cd)

            # Décrémenter le cooldown
            cd.timer = max(0.0, cd.timer - dt)
            
            if cd.timer > 0.0:
                continue  # Encore en cooldown
            
            # Vérifier que la cible existe
            tid = int(target.entity_id)
            
            if not esper.entity_exists(tid):
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue
            
            # Récupérer les infos de la cible
            try:
                tt = esper.component_for_entity(tid, Transform)
                th = esper.component_for_entity(tid, Health)
                tteam = esper.component_for_entity(tid, Team)
            except:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue
            
            # Vérifier que la cible est valide
            if th.is_dead or tteam.id == team.id:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)
                continue
            
            # Calculer la distance et direction
            ax, ay = t.pos
            bx, by = tt.pos
            
            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)
            
            # Vérifier la portée
            if dist > self.attack_range:
                continue
            
            # Déterminer la direction du tir (AXIAL - contrainte SAÉ)
            # Priorité à l'axe dominant
            if abs(dx) >= abs(dy):
                # Tir horizontal
                dir_x = _sign(dx)
                dir_y = 0.0
            else:
                # Tir vertical
                dir_x = 0.0
                dir_y = _sign(dy)
            
            # Créer le projectile
            damage = float(stats.power)
            if damage < 0:
                damage = 0.0
            
            pvx = dir_x * self.projectile_speed
            pvy = dir_y * self.projectile_speed
            
            esper.create_entity(
                Transform(pos=(ax, ay)),
                Velocity(vx=pvx, vy=pvy),
                Projectile(
                    team_id=int(team.id),
                    target_entity_id=tid,
                    damage=damage,
                    hit_radius=0.5,  # Rayon de détection généreux
                ),
                Lifetime(ttl=3.0, despawn_on_death=False)
            )
            
            # Réinitialiser le cooldown
            cd.timer = cd.cooldown
