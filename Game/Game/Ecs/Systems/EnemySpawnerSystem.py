# Game/Ecs/Systems/EnemySpawnerSystem.py
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


class EnemySpawnerSystem(esper.Processor):
    """
    Spawn automatique côté ennemi (SANS IA décisionnelle).

    Objectif SAÉ :
    - Pas de stratégie/adaptation : on spawn sur timer + difficulté qui monte avec le temps.
    - Les unités sont créées via EntityFactory.create_unit() pour respecter strictement :
        C = kP
        V + B = constante
        HP = B + 1  (=> destruction n*P > B)

    Le mouvement est ensuite géré par LaneRouteSystem + NavigationSystem.
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
    ):
        super().__init__()
        self.factory = factory
        self.balance = balance
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.nav_grid = nav_grid

        self.lanes_y = list(lanes_y) if lanes_y else None
        self.rng = random.Random(int(match_seed) + 424242)

        # timings
        self.start_delay = 3.0
        self.spawn_interval = 5.0

        # burst
        self.burst_count = 1
        self.burst_spacing = 0.25

        # pondérations
        self.weights = {"S": 0.60, "M": 0.30, "L": 0.10}

        # ✅ économie ennemie (SAÉ)
        econ = self.balance.get("economy", {})
        pyr = self.balance.get("pyramid", {})
        diff = self.balance.get("difficulty", {})

        self.enemy_start_money = float(econ.get("starting_money", 100.0)) * 0.60

        self.enemy_income_per_sec = float(econ.get("enemy_income_per_sec", pyr.get("income_base", 2.0)))
        self.enemy_income_per_sec *= float(econ.get("enemy_income_multiplier", 0.85))

        # ✅ Limite max d'unités ennemies (évite lag)
        self.max_enemy_units = int(diff.get("max_enemy_units", 30))

        # état
        self.timer = 0.0
        self.wave_index = 0
        self._burst_left = 0
        self._burst_timer = 0.0

        self.last_message = ""

    # ---------------------------
    # helpers
    # ---------------------------
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
            esper.add_component(self.enemy_pyramid_eid, Wallet(solde=max(0.0, float(self.enemy_start_money))))

    def _enemy_income_tick(self, dt: float):
        self._ensure_enemy_wallet()
        try:
            w = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
            w.solde += float(self.enemy_income_per_sec) * float(dt)
        except Exception:
            pass

    def _pick_unit_key(self) -> str:
        keys = ["S", "M", "L"]
        w = [float(self.weights.get(k, 0.0)) for k in keys]
        if sum(w) <= 0.0:
            return "S"
        return self.rng.choices(keys, weights=w, k=1)[0]

    def _pick_lane_idx(self) -> int:
        if self.wave_index % 4 == 0:
            return 1
        return int(self.rng.choice([0, 1, 2]))

    def hud_line(self) -> str:
        nxt = max(0.0, (self.spawn_interval - self.timer)) if self._burst_left <= 0 else max(0.0, self.burst_spacing - self._burst_timer)
        return f"Enemy waves: {self.wave_index} | next: {nxt:.1f}s | money: {self._enemy_money():.1f}"

    def _enemy_money(self) -> float:
        try:
            w = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
            return float(w.solde)
        except Exception:
            return 0.0

    def _count_enemy_units(self) -> int:
        """Compte les unités ennemies vivantes (team 2)."""
        count = 0
        for eid, (team, hp, stats) in esper.get_components(Team, Health, UnitStats):
            if team.id == 2 and not hp.is_dead:
                count += 1
        return count

    # ---------------------------
    # spawn
    # ---------------------------
    def _spawn_one(self):
        # Vérifier limite d'unités ennemies (évite lag)
        if self._count_enemy_units() >= self.max_enemy_units:
            self.last_message = f"Enemy: max units ({self.max_enemy_units})"
            return
        
        self._ensure_enemy_wallet()
        enemy_wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)

        unit_key = self._pick_unit_key()
        st = self.factory.compute_unit_stats(unit_key)

        if enemy_wallet.solde < float(st.cost):
            self.last_message = "Enemy: waiting money"
            return

        enemy_wallet.solde -= float(st.cost)

        # position pyramide ennemie
        try:
            et = esper.component_for_entity(self.enemy_pyramid_eid, Transform)
            ex = int(round(et.pos[0]))
            ey = int(round(et.pos[1]))
        except Exception:
            ex, ey = (0, 0)

        lane_idx = self._pick_lane_idx()
        lane_y = int(self._lane_centers()[lane_idx])

        # ✅ spawn "miroir" du joueur : 1 case à gauche de la pyramide ennemie sur la lane
        sx = ex - 1
        sy = lane_y

        found = self._find_walkable_near(int(sx), int(sy), max_r=12)
        if not found:
            self.last_message = "Enemy: no spawn found"
            return

        gx, gy = found

        ent = self.factory.create_unit(unit_key, team_id=2, grid_pos=(int(gx), int(gy)))

        if not esper.has_component(ent, Path):
            esper.add_component(ent, Path([]))
        if not esper.has_component(ent, PathProgress):
            esper.add_component(ent, PathProgress(index=0))
        
        # CORRECTION: Assigner le composant Lane avec l'index choisi
        # Cela garantit que l'ennemi reste sur la bonne lane même si spawn décalé
        esper.add_component(ent, Lane(index=lane_idx, y_position=float(lane_y)))

        try:
            team = esper.component_for_entity(ent, Team)
            team.id = 2
        except Exception:
            pass

        self.last_message = f"Enemy spawn {unit_key} (lane {lane_idx + 1})"

    def process(self, dt: float):
        if dt <= 0:
            return

        # ✅ prod/sec ennemi en continu
        self._enemy_income_tick(dt)

        if self.start_delay > 0:
            self.start_delay = max(0.0, self.start_delay - dt)
            return

        if self._burst_left > 0:
            self._burst_timer += dt
            if self._burst_timer >= self.burst_spacing:
                self._burst_timer = 0.0
                self._spawn_one()
                self._burst_left -= 1
            return

        self.timer += dt
        if self.timer >= self.spawn_interval:
            self.timer = 0.0
            self.wave_index += 1

            self._spawn_one()
            self._burst_left = max(0, self.burst_count - 1)
            self._burst_timer = 0.0
