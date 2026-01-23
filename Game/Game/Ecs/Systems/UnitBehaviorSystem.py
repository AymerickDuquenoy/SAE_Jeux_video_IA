# Game/Ecs/Systems/UnitBehaviorSystem.py
"""
UnitBehaviorSystem - Système unifié pour le comportement des unités.

Gère :
- Mouvement horizontal vers la pyramide ennemie
- Détection et ciblage des ennemis
- Combat et tir

Principes :
1. Les unités avancent horizontalement sur leur lane
2. Elles s'arrêtent quand un ennemi est à portée
3. Elles tirent vers la cible la plus proche
4. Les unités sur une lane ne ciblent QUE les ennemis sur la même lane (± tolérance)
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.lane import Lane
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.attack_cooldown import AttackCooldown
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.lifetime import Lifetime


class UnitBehaviorSystem(esper.Processor):
    """
    Système de comportement unifié pour toutes les unités.
    """

    def __init__(
        self,
        *,
        player_pyr_pos: tuple,
        enemy_pyr_pos: tuple,
        player_pyr_eid: int,
        enemy_pyr_eid: int,
        lanes_y: list,
        attack_range: float = 2.5,
        lane_tolerance: float = 1.5,
        projectile_speed: float = 12.0,
        attack_cooldown: float = 0.6,
    ):
        super().__init__()
        self.player_pyr_pos = (float(player_pyr_pos[0]), float(player_pyr_pos[1]))
        self.enemy_pyr_pos = (float(enemy_pyr_pos[0]), float(enemy_pyr_pos[1]))
        self.player_pyr_eid = int(player_pyr_eid)
        self.enemy_pyr_eid = int(enemy_pyr_eid)
        self.lanes_y = [float(y) for y in lanes_y]
        self.attack_range = float(attack_range)
        self.lane_tolerance = float(lane_tolerance)
        self.projectile_speed = float(projectile_speed)
        self.attack_cooldown = float(attack_cooldown)

    def process(self, dt: float):
        if dt <= 0:
            return

        # Collecter toutes les unités vivantes
        all_units = []
        for eid, (t, team, hp) in esper.get_components(Transform, Team, Health):
            if hp.is_dead:
                continue
            
            # Déterminer la lane
            lane_idx = -1
            if esper.has_component(eid, Lane):
                lane_idx = esper.component_for_entity(eid, Lane).index
            elif esper.has_component(eid, UnitStats):
                # Auto-assigner la lane la plus proche
                lane_idx = self._closest_lane(t.pos[1])
                esper.add_component(eid, Lane(index=lane_idx))
            
            is_pyramid = (eid == self.player_pyr_eid or eid == self.enemy_pyr_eid)
            all_units.append({
                'eid': eid,
                'x': t.pos[0],
                'y': t.pos[1],
                'team': team.id,
                'lane': lane_idx,
                'is_pyramid': is_pyramid,
            })

        # Traiter chaque unité (pas les pyramides)
        for eid, (t, team, stats, speed_comp) in esper.get_components(Transform, Team, UnitStats, Speed):
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue

            x, y = t.pos
            my_lane = -1
            if esper.has_component(eid, Lane):
                my_lane = esper.component_for_entity(eid, Lane).index

            # 1. Trouver la meilleure cible
            target_info = self._find_best_target(eid, x, y, team.id, my_lane, all_units)
            
            # 2. Mettre à jour le composant Target
            if target_info:
                if esper.has_component(eid, Target):
                    tg = esper.component_for_entity(eid, Target)
                    tg.entity_id = target_info['eid']
                    tg.type = "pyramid" if target_info['is_pyramid'] else "unit"
                else:
                    esper.add_component(eid, Target(
                        entity_id=target_info['eid'],
                        type="pyramid" if target_info['is_pyramid'] else "unit"
                    ))
            else:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)

            # 3. Mouvement ou arrêt
            self._handle_movement(eid, t, team.id, speed_comp, target_info, dt)
            
            # 4. Combat
            if target_info and target_info['dist'] <= self.attack_range:
                self._handle_combat(eid, t, team.id, stats, target_info, dt)

    def _closest_lane(self, y: float) -> int:
        """Trouve l'index de la lane la plus proche."""
        best_idx = 1
        best_dist = float('inf')
        for i, lane_y in enumerate(self.lanes_y):
            d = abs(y - lane_y)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

    def _same_lane(self, lane1: int, lane2: int, y1: float, y2: float) -> bool:
        """Vérifie si deux unités sont sur la même lane."""
        # Si les deux ont une lane assignée, comparer les indices
        if lane1 >= 0 and lane2 >= 0:
            return lane1 == lane2
        # Sinon, comparer les positions Y
        return abs(y1 - y2) <= self.lane_tolerance

    def _find_best_target(self, my_eid: int, my_x: float, my_y: float, 
                          my_team: int, my_lane: int, all_units: list) -> dict:
        """
        Trouve la meilleure cible pour une unité.
        
        Priorité :
        1. Unité ennemie sur la même lane, la plus proche
        2. Pyramide ennemie si à portée
        """
        enemy_team = 2 if my_team == 1 else 1
        direction = 1 if my_team == 1 else -1  # 1 = droite, -1 = gauche
        
        best_unit = None
        best_unit_dist = float('inf')
        
        pyramid_target = None
        pyramid_dist = float('inf')
        
        for unit in all_units:
            if unit['eid'] == my_eid:
                continue
            if unit['team'] == my_team:
                continue
            
            dx = unit['x'] - my_x
            dy = unit['y'] - my_y
            dist = math.hypot(dx, dy)
            
            # Vérifier si l'ennemi est DEVANT nous
            if direction > 0 and dx < -0.5:  # Team 1 va vers la droite
                continue
            if direction < 0 and dx > 0.5:   # Team 2 va vers la gauche
                continue
            
            if unit['is_pyramid']:
                # Pyramide ennemie
                if dist < pyramid_dist:
                    pyramid_dist = dist
                    pyramid_target = unit
            else:
                # Unité ennemie - vérifier même lane
                if self._same_lane(my_lane, unit['lane'], my_y, unit['y']):
                    if dist < best_unit_dist:
                        best_unit_dist = dist
                        best_unit = unit
        
        # Priorité aux unités sur la même lane
        if best_unit and best_unit_dist <= self.attack_range:
            return {**best_unit, 'dist': best_unit_dist}
        
        # Sinon, pyramide si à portée
        if pyramid_target and pyramid_dist <= self.attack_range + 1.0:
            return {**pyramid_target, 'dist': pyramid_dist}
        
        # Retourner l'unité même si pas à portée (pour continuer à avancer vers elle)
        if best_unit:
            return {**best_unit, 'dist': best_unit_dist}
        
        # Retourner la pyramide comme objectif final
        if pyramid_target:
            return {**pyramid_target, 'dist': pyramid_dist}
        
        return None

    def _handle_movement(self, eid: int, transform: Transform, team_id: int, 
                         speed_comp: Speed, target_info: dict, dt: float):
        """Gère le mouvement de l'unité."""
        # Obtenir ou créer Velocity
        if esper.has_component(eid, Velocity):
            vel = esper.component_for_entity(eid, Velocity)
        else:
            vel = Velocity(vx=0.0, vy=0.0)
            esper.add_component(eid, vel)

        x, y = transform.pos
        
        # Si on a une cible à portée d'attaque, on s'arrête
        if target_info and target_info['dist'] <= self.attack_range:
            vel.vx = 0.0
            vel.vy = 0.0
            return

        # Calculer la vitesse de base
        base_speed = float(speed_comp.base) * float(speed_comp.mult_terrain)
        base_speed = max(0.3, min(5.0, base_speed))

        # Direction principale : horizontal vers la pyramide ennemie
        if team_id == 1:
            target_x = self.enemy_pyr_pos[0]
            direction = 1
        else:
            target_x = self.player_pyr_pos[0]
            direction = -1

        # Mouvement horizontal
        vel.vx = direction * base_speed
        
        # Légère correction vers la lane si nécessaire
        if esper.has_component(eid, Lane):
            lane_idx = esper.component_for_entity(eid, Lane).index
            if 0 <= lane_idx < len(self.lanes_y):
                target_y = self.lanes_y[lane_idx]
                dy = target_y - y
                if abs(dy) > 0.05:
                    vel.vy = dy * 3.0  # Correction rapide vers la lane
                    vel.vy = max(-base_speed, min(base_speed, vel.vy))
                else:
                    vel.vy = 0.0
        else:
            vel.vy = 0.0

        # Appliquer le mouvement
        transform.pos = (x + vel.vx * dt, y + vel.vy * dt)

    def _handle_combat(self, eid: int, transform: Transform, team_id: int,
                       stats: UnitStats, target_info: dict, dt: float):
        """Gère le combat (tir)."""
        # Gérer le cooldown
        if esper.has_component(eid, AttackCooldown):
            cd = esper.component_for_entity(eid, AttackCooldown)
        else:
            cd = AttackCooldown(cooldown=self.attack_cooldown, timer=0.0)
            esper.add_component(eid, cd)

        cd.timer = max(0.0, cd.timer - dt)
        if cd.timer > 0.0:
            return

        # Vérifier que la cible existe encore
        tid = target_info['eid']
        if not esper.entity_exists(tid):
            return

        try:
            target_hp = esper.component_for_entity(tid, Health)
            if target_hp.is_dead:
                return
        except:
            return

        # Calculer direction du tir
        ax, ay = transform.pos
        bx, by = target_info['x'], target_info['y']
        
        dx = bx - ax
        dy = by - ay
        dist = math.hypot(dx, dy)
        
        if dist < 0.01:
            return

        # Normaliser la direction
        dir_x = dx / dist
        dir_y = dy / dist

        # Dégâts SAÉ : P = power
        damage = max(0.0, float(stats.power))

        # Créer le projectile
        esper.create_entity(
            Transform(pos=(ax, ay)),
            Velocity(vx=dir_x * self.projectile_speed, vy=dir_y * self.projectile_speed),
            Projectile(
                team_id=team_id,
                target_entity_id=tid,
                damage=damage,
                hit_radius=0.5
            ),
            Lifetime(ttl=3.0, despawn_on_death=False)
        )

        cd.timer = cd.cooldown
