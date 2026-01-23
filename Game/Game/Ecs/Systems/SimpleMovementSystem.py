# Game/Ecs/Systems/SimpleMovementSystem.py
"""
SimpleMovementSystem - Mouvement horizontal vers la pyramide ennemie.

Les unités avancent HORIZONTALEMENT (gardent leur Y de spawn = lane).
Elles s'arrêtent si un ennemi est proche pour combattre.
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


class SimpleMovementSystem(esper.Processor):
    """
    Mouvement horizontal vers la pyramide ennemie.
    
    - Les unités gardent leur Y de spawn (créant des "lanes" naturelles)
    - Team 1 (joueur) : va vers la droite (pyramide ennemie)
    - Team 2 (ennemi) : va vers la gauche (pyramide joueur)
    - S'arrête si ennemi à portée ou arrivé à la pyramide
    """

    def __init__(
        self,
        *,
        player_pyr_pos: tuple,  # (x, y) pyramide joueur
        enemy_pyr_pos: tuple,   # (x, y) pyramide ennemi
        pyramid_ids: set,
        combat_range: float = 1.8,  # Distance pour s'arrêter et combattre
    ):
        super().__init__()
        self.player_pyr_x = float(player_pyr_pos[0])
        self.player_pyr_y = float(player_pyr_pos[1])
        self.enemy_pyr_x = float(enemy_pyr_pos[0])
        self.enemy_pyr_y = float(enemy_pyr_pos[1])
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        self.combat_range = float(combat_range)

    def _has_enemy_in_range(self, my_x: float, my_y: float, my_team: int) -> bool:
        """
        Vérifie si un ennemi est à portée de combat.
        """
        for eid, (t, team, hp) in esper.get_components(Transform, Team, Health):
            if hp.is_dead:
                continue
            if team.id == my_team:
                continue
            
            ex, ey = t.pos
            dist = math.hypot(ex - my_x, ey - my_y)
            
            if dist <= self.combat_range:
                return True
        
        return False

    def _near_enemy_pyramid(self, x: float, y: float, team_id: int) -> bool:
        """Vérifie si l'unité est près de la pyramide ennemie."""
        if team_id == 1:  # Joueur -> pyramide ennemie
            dist = math.hypot(x - self.enemy_pyr_x, y - self.enemy_pyr_y)
        else:  # Ennemi -> pyramide joueur
            dist = math.hypot(x - self.player_pyr_x, y - self.player_pyr_y)
        
        return dist < 2.0  # À portée d'attaque de la pyramide

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

            # Vérifier si on doit s'arrêter
            should_stop = False
            
            # 1. A une cible à portée de combat ?
            if esper.has_component(eid, Target):
                target = esper.component_for_entity(eid, Target)
                tid = int(target.entity_id)
                if esper.entity_exists(tid):
                    try:
                        tt = esper.component_for_entity(tid, Transform)
                        th = esper.component_for_entity(tid, Health)
                        if not th.is_dead:
                            dist_to_target = math.hypot(tt.pos[0] - x, tt.pos[1] - y)
                            if dist_to_target <= self.combat_range:
                                should_stop = True
                    except:
                        pass
            
            # 2. Ennemi proche sans cible assignée ?
            if not should_stop and self._has_enemy_in_range(x, y, team.id):
                should_stop = True
            
            # 3. Arrivé près de la pyramide ennemie ?
            if not should_stop and self._near_enemy_pyramid(x, y, team.id):
                should_stop = True

            if should_stop:
                vel.vx = 0.0
                vel.vy = 0.0
            else:
                # Direction HORIZONTALE uniquement (garder Y = lane)
                if team.id == 1:  # Joueur -> droite
                    dir_x = 1.0
                else:  # Ennemi -> gauche
                    dir_x = -1.0
                
                # Vitesse de base
                base_speed = float(speed_comp.base) * float(speed_comp.mult_terrain)
                base_speed = max(0.5, base_speed)
                
                vel.vx = dir_x * base_speed
                vel.vy = 0.0  # Pas de mouvement vertical

            # Appliquer le mouvement
            new_x = x + vel.vx * dt
            new_y = y + vel.vy * dt
            t.pos = (new_x, new_y)
