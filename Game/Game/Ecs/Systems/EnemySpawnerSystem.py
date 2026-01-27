# Game/Ecs/Systems/EnemySpawnerSystem.py
"""
Système IA ennemi avec difficulté configurable.

Difficultés:
- Facile (easy): income x0.5, spawn lent, peu d'upgrades
- Moyen (medium): income x1.0, spawn normal, upgrades normaux  
- Difficile (hard): income x1.5, spawn rapide, upgrades fréquents
- Extrême (extreme): income x2.0, spawn très rapide, upgrades agressifs
"""
import random
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.lane import Lane
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.pyramidLevel import PyramidLevel


# Configuration par difficulté
DIFFICULTY_CONFIG = {
    "easy": {
        "income_mult": 0.5,
        "spawn_interval": 7.0,
        "upgrade_chance": 0.05,
        "weights": {"S": 0.70, "M": 0.25, "L": 0.05},
        "max_units": 15,
        "start_money_mult": 0.5,
    },
    "medium": {
        "income_mult": 1.0,
        "spawn_interval": 5.0,
        "upgrade_chance": 0.15,
        "weights": {"S": 0.50, "M": 0.35, "L": 0.15},
        "max_units": 25,
        "start_money_mult": 1.0,
    },
    "hard": {
        "income_mult": 1.5,
        "spawn_interval": 3.5,
        "upgrade_chance": 0.25,
        "weights": {"S": 0.35, "M": 0.40, "L": 0.25},
        "max_units": 35,
        "start_money_mult": 1.2,
    },
    "extreme": {
        "income_mult": 2.0,
        "spawn_interval": 2.5,
        "upgrade_chance": 0.40,
        "weights": {"S": 0.25, "M": 0.40, "L": 0.35},
        "max_units": 50,
        "start_money_mult": 1.5,
    },
}


class EnemySpawnerSystem(esper.Processor):
    """
    IA ennemie avec difficulté configurable.
    
    Fonctionnalités:
    - Revenus proportionnels à la difficulté (même base que joueur × multiplicateur)
    - Spawn aléatoire sur les 3 lanes
    - Choix aléatoire des unités (pondéré par difficulté)
    - Upgrade automatique de la pyramide
    """

    def __init__(
        self,
        factory,
        balance: dict,
        player_pyramid_eid: int,
        enemy_pyramid_eid: int,
        nav_grid,
        *,
        lanes_y: list[int] | None = None,
        match_seed: int = 0,
        difficulty: str = "medium",
    ):
        super().__init__()
        self.factory = factory
        self.balance = balance
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.nav_grid = nav_grid
        self.difficulty = difficulty if difficulty in DIFFICULTY_CONFIG else "medium"
        
        self.lanes_y = list(lanes_y) if lanes_y else None
        self.rng = random.Random(int(match_seed) + 424242)

        # Charger config difficulté
        cfg = DIFFICULTY_CONFIG[self.difficulty]
        
        # Économie - même base que le joueur × multiplicateur
        pyr = self.balance.get("pyramid", {})
        econ = self.balance.get("economy", {})
        
        player_income = float(pyr.get("income_base", 2.5))
        self.income_mult = cfg["income_mult"]
        self.enemy_income_per_sec = player_income * self.income_mult
        
        player_start = float(econ.get("starting_money", 120.0))
        self.enemy_start_money = player_start * cfg["start_money_mult"]
        
        # Spawn
        self.spawn_interval = cfg["spawn_interval"]
        self.weights = cfg["weights"]
        self.max_enemy_units = cfg["max_units"]
        
        # Upgrade
        self.upgrade_chance = cfg["upgrade_chance"]
        self.upgrade_cooldown = 0.0
        self.upgrade_check_interval = 3.0  # Vérifie toutes les 3 secondes
        
        # Coûts d'upgrade (depuis balance)
        self.upgrade_costs = pyr.get("upgrade_costs", [100, 125, 150, 175, 200])
        self.max_pyramid_level = int(pyr.get("level_max", 5))
        
        # Timers
        self.start_delay = 3.0
        self.timer = 0.0
        self.wave_index = 0
        
        self.last_message = ""

    def _lane_centers(self) -> list[int]:
        if self.lanes_y and len(self.lanes_y) >= 3:
            return [int(self.lanes_y[0]), int(self.lanes_y[1]), int(self.lanes_y[2])]

        h = int(getattr(self.nav_grid, "height", 0))
        if h <= 0:
            return [0, 0, 0]

        return [
            max(0, min(h - 1, h // 6)),
            max(0, min(h - 1, h // 2)),
            max(0, min(h - 1, (5 * h) // 6)),
        ]

    def _find_walkable_near(self, x: int, y: int, max_r: int = 10):
        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))

        for r in range(0, max_r + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx = int(x + dx)
                    ny = int(y + dy)

                    if w > 0 and h > 0:
                        if nx < 0 or nx >= w or ny < 0 or ny >= h:
                            continue

                    if hasattr(self.nav_grid, "is_walkable"):
                        try:
                            if self.nav_grid.is_walkable(nx, ny):
                                return nx, ny
                        except Exception:
                            continue
                    else:
                        if 0 <= nx < self.nav_grid.width and 0 <= ny < self.nav_grid.height:
                            if self.nav_grid.walkable[ny][nx]:
                                return nx, ny
        return None

    def _ensure_enemy_wallet(self):
        if not esper.has_component(self.enemy_pyramid_eid, Wallet):
            esper.add_component(self.enemy_pyramid_eid, Wallet(solde=max(0.0, self.enemy_start_money)))

    def _enemy_income_tick(self, dt: float):
        """Ajoute les revenus passifs à l'ennemi."""
        self._ensure_enemy_wallet()
        try:
            wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
            
            # Bonus d'income si pyramide upgradée (comme le joueur)
            income_bonus = 1.0
            if esper.has_component(self.enemy_pyramid_eid, PyramidLevel):
                level = esper.component_for_entity(self.enemy_pyramid_eid, PyramidLevel).level
                income_mult = float(self.balance.get("pyramid", {}).get("income_mult", 1.25))
                income_bonus = income_mult ** (level - 1)
            
            wallet.solde += self.enemy_income_per_sec * income_bonus * dt
        except Exception:
            pass

    def _get_enemy_money(self) -> float:
        try:
            wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
            return float(wallet.solde)
        except Exception:
            return 0.0

    def _get_enemy_pyramid_level(self) -> int:
        try:
            if esper.has_component(self.enemy_pyramid_eid, PyramidLevel):
                return esper.component_for_entity(self.enemy_pyramid_eid, PyramidLevel).level
        except Exception:
            pass
        return 1

    def _try_upgrade_pyramid(self):
        """Tente d'upgrader la pyramide ennemie."""
        try:
            level = self._get_enemy_pyramid_level()
            
            if level >= self.max_pyramid_level:
                return False
            
            # Coût de l'upgrade
            cost_idx = min(level - 1, len(self.upgrade_costs) - 1)
            cost = self.upgrade_costs[cost_idx]
            
            money = self._get_enemy_money()
            
            # L'IA upgrade si elle a assez d'argent ET si le random le permet
            if money >= cost and self.rng.random() < self.upgrade_chance:
                wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
                wallet.solde -= cost
                
                if esper.has_component(self.enemy_pyramid_eid, PyramidLevel):
                    pyr_level = esper.component_for_entity(self.enemy_pyramid_eid, PyramidLevel)
                    pyr_level.level += 1
                    
                    # Augmenter les HP de la pyramide
                    if esper.has_component(self.enemy_pyramid_eid, Health):
                        hp = esper.component_for_entity(self.enemy_pyramid_eid, Health)
                        hp_bonus = 100  # +100 HP par niveau
                        hp.hp_max += hp_bonus
                        hp.hp += hp_bonus
                    
                    self.last_message = f"Enemy upgraded pyramid to Lv.{pyr_level.level}!"
                    return True
        except Exception:
            pass
        return False

    def _pick_unit_key(self) -> str:
        """Choix aléatoire pondéré de l'unité."""
        keys = ["S", "M", "L"]
        weights = [float(self.weights.get(k, 0.33)) for k in keys]
        if sum(weights) <= 0.0:
            return self.rng.choice(keys)
        return self.rng.choices(keys, weights=weights, k=1)[0]

    def _pick_lane_idx(self) -> int:
        """Choix complètement aléatoire de la lane."""
        return self.rng.randint(0, 2)

    def _count_enemy_units(self) -> int:
        """Compte les unités ennemies vivantes."""
        count = 0
        for eid, (team, hp, stats) in esper.get_components(Team, Health, UnitStats):
            if team.id == 2 and not hp.is_dead:
                count += 1
        return count

    def _spawn_one(self):
        """Spawn une unité ennemie."""
        # Vérifier limite
        if self._count_enemy_units() >= self.max_enemy_units:
            self.last_message = f"Enemy: max units ({self.max_enemy_units})"
            return False
        
        self._ensure_enemy_wallet()
        
        try:
            wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
        except Exception:
            return False

        # Choix aléatoire de l'unité
        unit_key = self._pick_unit_key()
        stats = self.factory.compute_unit_stats(unit_key)

        if wallet.solde < float(stats.cost):
            self.last_message = "Enemy: waiting money"
            return False

        wallet.solde -= float(stats.cost)

        # Position de spawn
        try:
            et = esper.component_for_entity(self.enemy_pyramid_eid, Transform)
            ex = int(round(et.pos[0]))
            ey = int(round(et.pos[1]))
        except Exception:
            ex, ey = (0, 0)

        # Lane aléatoire
        lane_idx = self._pick_lane_idx()
        lane_y = int(self._lane_centers()[lane_idx])

        sx = ex - 1
        sy = lane_y

        found = self._find_walkable_near(int(sx), int(sy), max_r=12)
        if not found:
            self.last_message = "Enemy: no spawn found"
            wallet.solde += float(stats.cost)  # Rembourser
            return False

        gx, gy = found

        ent = self.factory.create_unit(unit_key, team_id=2, grid_pos=(int(gx), int(gy)))

        if not esper.has_component(ent, Path):
            esper.add_component(ent, Path([]))
        if not esper.has_component(ent, PathProgress):
            esper.add_component(ent, PathProgress(index=0))
        
        esper.add_component(ent, Lane(index=lane_idx, y_position=float(lane_y)))

        try:
            team = esper.component_for_entity(ent, Team)
            team.id = 2
        except Exception:
            pass

        self.last_message = f"Enemy spawn {unit_key} (lane {lane_idx + 1})"
        return True

    def hud_line(self) -> str:
        """Ligne de debug pour le HUD."""
        nxt = max(0.0, self.spawn_interval - self.timer)
        money = self._get_enemy_money()
        level = self._get_enemy_pyramid_level()
        diff_name = {"easy": "Facile", "medium": "Moyen", "hard": "Difficile", "extreme": "Extreme"}
        return f"Ennemi: {money:.0f} | Nv.{level} | Vague {self.wave_index} | {diff_name.get(self.difficulty, self.difficulty)}"

    def process(self, dt: float):
        if dt <= 0:
            return

        # Revenus passifs
        self._enemy_income_tick(dt)

        # Délai de départ
        if self.start_delay > 0:
            self.start_delay = max(0.0, self.start_delay - dt)
            return

        # Vérifier upgrade périodiquement
        self.upgrade_cooldown -= dt
        if self.upgrade_cooldown <= 0:
            self.upgrade_cooldown = self.upgrade_check_interval
            self._try_upgrade_pyramid()

        # Spawn timer
        self.timer += dt
        if self.timer >= self.spawn_interval:
            self.timer = 0.0
            self.wave_index += 1
            self._spawn_one()
