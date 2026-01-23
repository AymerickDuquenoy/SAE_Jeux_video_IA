# Game/Ecs/Systems/UnitAISystem.py
"""
IA spécifique par type d'unité (Game Design).

- Momie (S): Flocking + attaque corps à corps
- Dromadaire (M): Tank solitaire, cible troupe la plus proche
- Sphinx (L): Ignore troupes, va droit vers pyramide
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target


class UnitAISystem(esper.Processor):
    """
    Comportements IA différenciés par type d'unité.
    Gère le mouvement ET le ciblage.
    """

    def __init__(
        self,
        *,
        player_pyr_pos: tuple,
        enemy_pyr_pos: tuple,
        pyramid_ids: dict,  # {team_id: eid}
        flocking_radius: float = 3.0,
        attack_range: float = 2.0,
    ):
        super().__init__()
        self.player_pyr_pos = tuple(player_pyr_pos)
        self.enemy_pyr_pos = tuple(enemy_pyr_pos)
        self.pyramid_ids = dict(pyramid_ids)
        self.flocking_radius = float(flocking_radius)
        self.attack_range = float(attack_range)

    def _get_unit_type(self, stats: UnitStats) -> str:
        """Détermine le type S/M/L basé sur le coût."""
        cost = float(stats.cost)
        if cost <= 15:
            return "S"  # Momie
        elif cost <= 50:
            return "M"  # Dromadaire
        else:
            return "L"  # Sphinx

    def _get_enemy_pyramid_pos(self, team_id: int) -> tuple:
        """Position de la pyramide ennemie."""
        if team_id == 1:
            return self.enemy_pyr_pos
        return self.player_pyr_pos

    def _get_enemy_pyramid_eid(self, team_id: int) -> int:
        """ID de la pyramide ennemie."""
        enemy_team = 2 if team_id == 1 else 1
        return self.pyramid_ids.get(enemy_team, 0)

    def _find_nearby_allies(self, x: float, y: float, team_id: int, unit_type: str, max_dist: float) -> list:
        """Trouve les alliés Momies proches (pour flocking)."""
        allies = []
        for eid, (t, team, hp, stats) in esper.get_components(Transform, Team, Health, UnitStats):
            if hp.is_dead or team.id != team_id:
                continue
            # Seulement les Momies pour le flocking
            if self._get_unit_type(stats) != "S":
                continue
            ax, ay = t.pos
            dist = math.hypot(ax - x, ay - y)
            if 0 < dist <= max_dist:
                allies.append((eid, ax, ay, dist))
        return allies

    def _find_closest_enemy_unit(self, x: float, y: float, team_id: int) -> tuple:
        """Trouve l'unité ennemie la plus proche (pas pyramide)."""
        closest = None
        closest_dist = float('inf')
        
        for eid, (t, team, hp, stats) in esper.get_components(Transform, Team, Health, UnitStats):
            if hp.is_dead or team.id == team_id:
                continue
            # Skip pyramides
            if eid in self.pyramid_ids.values():
                continue
            ex, ey = t.pos
            dist = math.hypot(ex - x, ey - y)
            if dist < closest_dist:
                closest_dist = dist
                closest = (eid, ex, ey)
        
        return (closest, closest_dist) if closest else (None, float('inf'))

    def _apply_flocking(self, x: float, y: float, allies: list) -> tuple:
        """Calcul flocking pour Momies. Retourne (dx, dy)."""
        if not allies:
            return (0.0, 0.0)
        
        # Cohésion: aller vers le centre de masse
        cx = sum(a[1] for a in allies) / len(allies)
        cy = sum(a[2] for a in allies) / len(allies)
        
        dx = cx - x
        dy = cy - y
        
        dist = math.hypot(dx, dy)
        if dist > 0.1:
            dx = (dx / dist) * 0.3
            dy = (dy / dist) * 0.3
        
        return (dx, dy)

    def _set_target(self, eid: int, target_eid: int):
        """Assigne une cible à l'unité."""
        if esper.has_component(eid, Target):
            target = esper.component_for_entity(eid, Target)
            target.entity_id = target_eid
        else:
            esper.add_component(eid, Target(entity_id=target_eid))

    def _clear_target(self, eid: int):
        """Retire la cible de l'unité."""
        if esper.has_component(eid, Target):
            esper.remove_component(eid, Target)

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats, speed_comp) in esper.get_components(Transform, Team, UnitStats, Speed):
            # Skip morts
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue

            # Skip pyramides
            if eid in self.pyramid_ids.values():
                continue

            x, y = t.pos
            unit_type = self._get_unit_type(stats)
            
            # Get/create velocity
            if esper.has_component(eid, Velocity):
                vel = esper.component_for_entity(eid, Velocity)
            else:
                vel = Velocity(vx=0.0, vy=0.0)
                esper.add_component(eid, vel)

            base_speed = float(speed_comp.base) * float(speed_comp.mult_terrain)
            base_speed = max(0.5, base_speed)

            # ============================================
            # SPHINX (L): Ignore troupes, va vers pyramide
            # ============================================
            if unit_type == "L":
                pyr_pos = self._get_enemy_pyramid_pos(team.id)
                pyr_eid = self._get_enemy_pyramid_eid(team.id)
                
                dx = pyr_pos[0] - x
                dy = pyr_pos[1] - y
                dist = math.hypot(dx, dy)
                
                if dist < 2.5:
                    # Proche -> cibler pyramide et s'arrêter
                    if pyr_eid and esper.entity_exists(pyr_eid):
                        self._set_target(eid, pyr_eid)
                    vel.vx = 0.0
                    vel.vy = 0.0
                else:
                    # Avancer vers pyramide
                    self._clear_target(eid)
                    if dist > 0.1:
                        vel.vx = (dx / dist) * base_speed
                        vel.vy = (dy / dist) * base_speed
                
                # Appliquer mouvement
                t.pos = (x + vel.vx * dt, y + vel.vy * dt)
                continue

            # ============================================
            # MOMIE (S) et DROMADAIRE (M)
            # ============================================
            
            # Chercher ennemi proche
            closest, closest_dist = self._find_closest_enemy_unit(x, y, team.id)
            
            # Ennemi à portée -> s'arrêter et combattre
            if closest and closest_dist <= self.attack_range:
                self._set_target(eid, closest[0])
                vel.vx = 0.0
                vel.vy = 0.0
                t.pos = (x + vel.vx * dt, y + vel.vy * dt)
                continue

            # Pas d'ennemi à portée -> avancer
            self._clear_target(eid)

            # Direction de base (horizontale)
            dir_x = 1.0 if team.id == 1 else -1.0
            dir_y = 0.0

            # MOMIE: ajouter flocking léger
            if unit_type == "S":
                allies = self._find_nearby_allies(x, y, team.id, unit_type, self.flocking_radius)
                if allies:
                    flock_dx, flock_dy = self._apply_flocking(x, y, allies)
                    dir_x += flock_dx
                    dir_y += flock_dy

            # Normaliser et appliquer
            mag = math.hypot(dir_x, dir_y)
            if mag > 0.1:
                vel.vx = (dir_x / mag) * base_speed
                vel.vy = (dir_y / mag) * base_speed
            else:
                vel.vx = 0.0
                vel.vy = 0.0

            # Appliquer mouvement
            t.pos = (x + vel.vx * dt, y + vel.vy * dt)
