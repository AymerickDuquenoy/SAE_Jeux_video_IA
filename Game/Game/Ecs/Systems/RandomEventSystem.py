"""
RandomEventSystem - Événements aléatoires du Game Design

Événements possibles (un seul actif à la fois) :
1. Tempête de sable : échange zones Open ↔ Dusty pendant 10s
2. Nuée de sauterelles : 15 dégâts à TOUTES les troupes (instantané)
3. Livraison de fouets : +25% production pour une équipe pendant 10s
"""
import random
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.incomeRate import IncomeRate


class RandomEventSystem(esper.Processor):
    """
    Gère les événements aléatoires pendant la partie.
    """

    def __init__(self, nav_grid, player_pyramid_eid: int, enemy_pyramid_eid: int, on_terrain_change=None):
        super().__init__()
        self.nav_grid = nav_grid
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.on_terrain_change = on_terrain_change  # Callback pour recalculer les lanes
        
        # Timing
        self.time_since_last_event = 0.0
        self.min_interval = 25.0  # Minimum 25s entre événements
        self.max_interval = 45.0  # Maximum 45s
        self.next_event_time = random.uniform(self.min_interval, self.max_interval)
        
        # État événement actif
        self.active_event = None  # "sandstorm", "locusts", "whip_bonus"
        self.event_timer = 0.0
        self.event_duration = 10.0
        
        # Pour tempête de sable
        self.original_mults = None
        
        # Pour bonus fouets
        self.bonus_team = None
        
        # Message à afficher
        self.current_message = ""
        self.message_timer = 0.0

    def get_message(self) -> str:
        """Retourne le message d'événement actuel."""
        if self.message_timer > 0:
            return self.current_message
        return ""

    def process(self, dt: float):
        if dt <= 0:
            return

        # Gérer événement actif
        if self.active_event:
            self.event_timer -= dt
            self.message_timer -= dt
            
            if self.event_timer <= 0:
                self._end_event()
            return

        # Timer pour prochain événement
        self.time_since_last_event += dt
        
        if self.time_since_last_event >= self.next_event_time:
            self._trigger_random_event()
            self.time_since_last_event = 0.0
            self.next_event_time = random.uniform(self.min_interval, self.max_interval)

    def _trigger_random_event(self):
        """Déclenche un événement aléatoire."""
        event_type = random.choice(["sandstorm", "locusts", "whip_bonus"])
        
        if event_type == "sandstorm":
            self._start_sandstorm()
        elif event_type == "locusts":
            self._start_locusts()
        else:
            self._start_whip_bonus()

    def _start_sandstorm(self):
        """Tempête de sable : échange zones Open ↔ Dusty."""
        self.active_event = "sandstorm"
        self.event_timer = self.event_duration
        self.message_timer = 3.0
        self.current_message = "TEMPETE DE SABLE! Terrain modifie!"
        
        # Sauvegarder et échanger les multiplicateurs
        if hasattr(self.nav_grid, 'mult'):
            h = len(self.nav_grid.mult)
            w = len(self.nav_grid.mult[0]) if h > 0 else 0
            
            self.original_mults = [[self.nav_grid.mult[y][x] for x in range(w)] for y in range(h)]
            
            for y in range(h):
                for x in range(w):
                    m = self.nav_grid.mult[y][x]
                    if m == 1.0:  # Open → Dusty
                        self.nav_grid.mult[y][x] = 0.5
                    elif 0 < m < 1.0:  # Dusty → Open
                        self.nav_grid.mult[y][x] = 1.0
                    # Interdit (0) reste interdit
            
            # Notifier que le terrain a changé → recalculer les lanes
            if self.on_terrain_change:
                self.on_terrain_change()

    def _start_locusts(self):
        """Nuée de sauterelles : 15 dégâts à toutes les troupes."""
        self.active_event = "locusts"
        self.event_timer = 0.5  # Très court, effet instantané
        self.message_timer = 3.0
        self.current_message = "SAUTERELLES! 15 dégâts à tous!"
        
        damage = 15
        
        # Appliquer dégâts à toutes les unités (pas pyramides)
        for eid, (hp, stats) in esper.get_components(Health, UnitStats):
            if hp.is_dead:
                continue
            hp.hp = max(0, hp.hp - damage)

    def _start_whip_bonus(self):
        """Bonus fouets : +25% production pour une équipe."""
        self.active_event = "whip_bonus"
        self.event_timer = self.event_duration
        self.message_timer = 3.0
        
        # Choisir équipe aléatoire
        self.bonus_team = random.choice([1, 2])
        team_name = "JOUEUR" if self.bonus_team == 1 else "ENNEMI"
        self.current_message = f"BONUS FOUETS! {team_name} +25% production!"
        
        # Appliquer bonus via multiplier (jamais modifier rate directement)
        pyramid_eid = self.player_pyramid_eid if self.bonus_team == 1 else self.enemy_pyramid_eid
        if esper.has_component(pyramid_eid, IncomeRate):
            income = esper.component_for_entity(pyramid_eid, IncomeRate)
            income.multiplier = 1.25  # Toujours utiliser multiplier

    def _end_event(self):
        """Termine l'événement actif."""
        if self.active_event == "sandstorm" and self.original_mults:
            # Restaurer le terrain
            h = len(self.original_mults)
            w = len(self.original_mults[0]) if h > 0 else 0
            for y in range(h):
                for x in range(w):
                    self.nav_grid.mult[y][x] = self.original_mults[y][x]
            self.original_mults = None
            
            # Notifier que le terrain a changé → recalculer les lanes
            if self.on_terrain_change:
                self.on_terrain_change()
            
        elif self.active_event == "whip_bonus" and self.bonus_team:
            # Retirer bonus via multiplier (reset propre)
            pyramid_eid = self.player_pyramid_eid if self.bonus_team == 1 else self.enemy_pyramid_eid
            if esper.has_component(pyramid_eid, IncomeRate):
                income = esper.component_for_entity(pyramid_eid, IncomeRate)
                income.multiplier = 1.0  # Reset propre
            self.bonus_team = None
        
        self.active_event = None
