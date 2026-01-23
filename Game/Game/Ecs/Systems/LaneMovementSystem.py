"""
LaneMovementSystem - Mouvement des unités vers la pyramide ennemie.

Les unités avancent horizontalement sur leur "lane" (position Y de spawn).
Elles s'arrêtent uniquement si:
1. Un ennemi est directement devant elles à portée de combat
2. Elles ont atteint la pyramide ennemie
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


class LaneMovementSystem(esper.Processor):
    """
    Système de mouvement sur les lanes.
    
    - Les unités avancent horizontalement vers la pyramide ennemie
    - Elles gardent leur position Y (leur "lane")
    - Elles s'arrêtent pour combattre ou quand elles arrivent
    """

    def __init__(
        self,
        *,
        player_pyr_x: float,
        enemy_pyr_x: float,
        lanes_y: list,
        pyramid_ids: set,
        lane_tolerance: float = 1.5,
        stop_distance: float = 2.0,
    ):
        super().__init__()
        self.player_pyr_x = float(player_pyr_x)
        self.enemy_pyr_x = float(enemy_pyr_x)
        self.lanes_y = [float(y) for y in lanes_y]
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        self.lane_tolerance = float(lane_tolerance)
        self.stop_distance = float(stop_distance)

    def _get_closest_lane(self, y: float) -> int:
        """Trouve la lane la plus proche d'une position Y."""
        if not self.lanes_y:
            return 1  # Lane du milieu par défaut
        
        best_idx = 0
        best_dist = abs(y - self.lanes_y[0])
        
        for i, lane_y in enumerate(self.lanes_y):
            dist = abs(y - lane_y)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        
        return best_idx

    def _get_destination_x(self, team_id: int) -> float:
        """Retourne la position X de destination (pyramide ennemie)."""
        if team_id == 1:  # Joueur -> vers la droite (pyramide ennemie)
            return self.enemy_pyr_x - 1.0  # Position adjacente à la pyramide
        else:  # Ennemi -> vers la gauche (pyramide joueur)
            return self.player_pyr_x + 1.0

    def _has_enemy_ahead(self, eid: int, x: float, y: float, team_id: int, direction: float) -> bool:
        """
        Vérifie si un ennemi est devant l'unité (dans la direction de mouvement).
        """
        for other_eid, (ot, oteam, ohp) in esper.get_components(Transform, Team, Health):
            if other_eid == eid:
                continue
            if ohp.is_dead:
                continue
            if oteam.id == team_id:
                continue  # Même équipe
            
            ox, oy = ot.pos
            
            # Vérifier si sur la même lane (tolérance Y)
            if abs(oy - y) > self.lane_tolerance:
                continue
            
            # Vérifier si l'ennemi est dans la direction de mouvement
            dx = ox - x
            
            # direction > 0 = vers la droite, < 0 = vers la gauche
            if direction > 0 and dx > 0 and dx <= self.stop_distance:
                return True
            elif direction < 0 and dx < 0 and abs(dx) <= self.stop_distance:
                return True
        
        return False

    def _has_reached_goal(self, x: float, team_id: int) -> bool:
        """Vérifie si l'unité a atteint sa destination."""
        dest_x = self._get_destination_x(team_id)
        
        if team_id == 1:  # Joueur va vers la droite
            return x >= dest_x - 0.3
        else:  # Ennemi va vers la gauche
            return x <= dest_x + 0.3

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats, speed_comp) in esper.get_components(Transform, Team, UnitStats, Speed):
            # Skip unités mortes
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue

            # Skip pyramides
            if eid in self.pyramid_ids:
                continue

            # Get or create velocity
            if esper.has_component(eid, Velocity):
                vel = esper.component_for_entity(eid, Velocity)
            else:
                vel = Velocity(vx=0.0, vy=0.0)
                esper.add_component(eid, vel)

            x, y = t.pos
            
            # Direction de mouvement (Team 1 -> droite, Team 2 -> gauche)
            direction = 1.0 if team.id == 1 else -1.0
            
            # Déterminer si on doit s'arrêter
            should_stop = False
            
            # 1. Vérifier si on a atteint la pyramide
            if self._has_reached_goal(x, team.id):
                should_stop = True
            
            # 2. Vérifier si on a une cible (combat en cours)
            elif esper.has_component(eid, Target):
                target = esper.component_for_entity(eid, Target)
                tid = int(target.entity_id)
                
                if esper.entity_exists(tid):
                    try:
                        tt = esper.component_for_entity(tid, Transform)
                        th = esper.component_for_entity(tid, Health)
                        
                        if not th.is_dead:
                            # Cible valide, s'arrêter pour combattre
                            should_stop = True
                    except:
                        pass
            
            # 3. Vérifier si un ennemi est juste devant
            elif self._has_enemy_ahead(eid, x, y, team.id, direction):
                should_stop = True

            if should_stop:
                vel.vx = 0.0
                vel.vy = 0.0
            else:
                # Calculer la vitesse de mouvement
                base_speed = float(speed_comp.base) * float(speed_comp.mult_terrain)
                base_speed = max(0.5, base_speed)
                
                # Mouvement horizontal
                vel.vx = direction * base_speed
                
                # Légère correction Y pour rester sur la lane
                lane_idx = self._get_closest_lane(y)
                target_y = self.lanes_y[lane_idx] if self.lanes_y else y
                
                dy = target_y - y
                if abs(dy) > 0.1:
                    # Correction douce vers la lane
                    vel.vy = dy * 0.5  # Lent ajustement
                else:
                    vel.vy = 0.0

            # Appliquer le mouvement
            new_x = x + vel.vx * dt
            new_y = y + vel.vy * dt
            t.pos = (new_x, new_y)
