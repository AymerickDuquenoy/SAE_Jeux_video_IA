# Game/Ecs/Systems/RandomEventSystem.py
"""
Événements aléatoires du Game Design:
- Tempête de sable: échange zones rapide/lente pendant 10s
- Nuée de sauterelles: 15 dégâts à toutes les troupes
- Livraison de fouets: production x1.25 pendant 10s (joueur aléatoire)
"""
import random
import esper

from Game.Ecs.Components.health import Health
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.incomeRate import IncomeRate


class RandomEventSystem(esper.Processor):
    """
    Gère les événements aléatoires.
    Un seul événement actif à la fois (comme spécifié).
    """

    def __init__(
        self,
        nav_grid,
        *,
        player_pyramid_eid: int,
        enemy_pyramid_eid: int,
        min_interval: float = 30.0,
        max_interval: float = 60.0,
        event_duration: float = 10.0,
        locust_damage: int = 15,
        whip_multiplier: float = 1.25,
    ):
        super().__init__()
        self.nav_grid = nav_grid
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        
        self.min_interval = float(min_interval)
        self.max_interval = float(max_interval)
        self.event_duration = float(event_duration)
        self.locust_damage = int(locust_damage)
        self.whip_multiplier = float(whip_multiplier)
        
        # État
        self.timer = random.uniform(self.min_interval, self.max_interval)
        self.active_event = None  # None, "sandstorm", "locust", "whip"
        self.event_timer = 0.0
        self.affected_team = 0  # Pour whip bonus
        
        # Pour sandstorm: sauvegarder les multiplicateurs originaux
        self.original_mults = {}
        
        self.last_message = ""

    def _trigger_sandstorm(self):
        """Tempête de sable: échange zones rapide/lente."""
        self.active_event = "sandstorm"
        self.event_timer = self.event_duration
        self.last_message = "⛈️ TEMPÊTE DE SABLE! Terrain modifié pour 10s"
        
        if not self.nav_grid:
            return
            
        # Sauvegarder et inverser les multiplicateurs
        w = getattr(self.nav_grid, 'width', 0)
        h = getattr(self.nav_grid, 'height', 0)
        
        self.original_mults = {}
        for y in range(h):
            for x in range(w):
                try:
                    m = float(self.nav_grid.mult[y][x])
                    self.original_mults[(x, y)] = m
                    
                    # Inverser: rapide (1.0) <-> lent (0.5)
                    if m >= 0.9:
                        new_m = 0.5
                    elif m >= 0.4 and m < 0.9:
                        new_m = 1.0
                    else:
                        new_m = m  # Infranchissable reste infranchissable
                    
                    self.nav_grid.mult[y][x] = new_m
                except:
                    pass

    def _end_sandstorm(self):
        """Restaurer le terrain après tempête."""
        if not self.nav_grid or not self.original_mults:
            return
            
        for (x, y), m in self.original_mults.items():
            try:
                self.nav_grid.mult[y][x] = m
            except:
                pass
        
        self.original_mults = {}
        self.last_message = "Tempête terminée"

    def _trigger_locust(self):
        """Nuée de sauterelles: dégâts à toutes les troupes."""
        self.active_event = "locust"
        self.event_timer = 0.5  # Effet instantané
        self.last_message = f"🦗 SAUTERELLES! {self.locust_damage} dégâts à toutes les troupes"
        
        # Appliquer dégâts
        for eid, (hp, team, stats) in esper.get_components(Health, Team, UnitStats):
            if hp.is_dead:
                continue
            hp.hp = max(0, int(hp.hp) - self.locust_damage)
            if hp.hp <= 0:
                hp.is_dead = True

    def _trigger_whip(self):
        """Livraison de fouets: bonus production."""
        self.active_event = "whip"
        self.event_timer = self.event_duration
        self.affected_team = random.choice([1, 2])
        
        team_name = "Joueur" if self.affected_team == 1 else "Ennemi"
        self.last_message = f"🪶 BONUS FOUETS! {team_name} +25% production pour 10s"
        
        # Appliquer bonus
        pyr_eid = self.player_pyramid_eid if self.affected_team == 1 else self.enemy_pyramid_eid
        
        if esper.entity_exists(pyr_eid) and esper.has_component(pyr_eid, IncomeRate):
            income = esper.component_for_entity(pyr_eid, IncomeRate)
            income.multiplier *= self.whip_multiplier

    def _end_whip(self):
        """Retirer bonus production."""
        pyr_eid = self.player_pyramid_eid if self.affected_team == 1 else self.enemy_pyramid_eid
        
        if esper.entity_exists(pyr_eid) and esper.has_component(pyr_eid, IncomeRate):
            income = esper.component_for_entity(pyr_eid, IncomeRate)
            income.multiplier /= self.whip_multiplier
        
        self.last_message = "Bonus fouets terminé"

    def hud_line(self) -> str:
        """Ligne pour le HUD."""
        if self.active_event:
            return f"Event: {self.active_event} ({self.event_timer:.1f}s)"
        return f"Next event in: {self.timer:.1f}s"

    def process(self, dt: float):
        if dt <= 0:
            return

        # Gérer événement actif
        if self.active_event:
            self.event_timer -= dt
            
            if self.event_timer <= 0:
                # Fin de l'événement
                if self.active_event == "sandstorm":
                    self._end_sandstorm()
                elif self.active_event == "whip":
                    self._end_whip()
                
                self.active_event = None
                self.timer = random.uniform(self.min_interval, self.max_interval)
            return

        # Timer pour prochain événement
        self.timer -= dt
        
        if self.timer <= 0:
            # Déclencher un événement aléatoire
            event_type = random.choice(["sandstorm", "locust", "whip"])
            
            if event_type == "sandstorm":
                self._trigger_sandstorm()
            elif event_type == "locust":
                self._trigger_locust()
            else:
                self._trigger_whip()
