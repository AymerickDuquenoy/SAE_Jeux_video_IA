# Game/Ecs/Systems/EnemySpawnerSystem.py
import random
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.pathRequest import PathRequest
from Game.Ecs.Components.unitType import UnitType


class EnemySpawnerSystem(esper.Processor):
    """
    Spawn automatique côté ennemi.
    La difficulté (intervalle / burst / poids) est pilotée par DifficultySystem.
    """

    def __init__(self, factory, balance, player_pyramid_eid: int, enemy_pyramid_eid: int, nav_grid):
        super().__init__()
        self.factory = factory
        self.balance = balance
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.nav_grid = nav_grid

        self.last_message = ""

        self.timer = 0.0
        self.spawn_interval = float(balance.get("difficulty", {}).get("spawn_interval_base", 5.0))
        self.start_delay = float(balance.get("difficulty", {}).get("start_delay", 2.0))

        self.wave_index = 0

        # burst (spawn plusieurs unités d'un coup)
        self.burst_count = 1
        self.burst_spacing = float(balance.get("difficulty", {}).get("burst_spacing", 0.25))
        self._burst_left = 0
        self._burst_timer = 0.0

        # poids (modifiable par la difficulté)
        default_weights = balance.get("enemy_ai", {}).get("spawn_weights", {"S": 0.55, "M": 0.30, "L": 0.15})
        self.weights = dict(default_weights)

    def set_params(self, *, spawn_interval: float | None = None, burst_count: int | None = None, weights: dict | None = None):
        if spawn_interval is not None:
            self.spawn_interval = max(0.25, float(spawn_interval))
        if burst_count is not None:
            self.burst_count = max(1, int(burst_count))
        if weights is not None and isinstance(weights, dict) and len(weights) > 0:
            self.weights = dict(weights)

    def hud_line(self) -> str:
        nxt = max(0.0, (self.spawn_interval - self.timer)) if self._burst_left <= 0 else max(0.0, self._burst_timer)
        return f"Enemy waves: {self.wave_index} | next: {nxt:.1f}s | burst: {self.burst_count}x"

    def _lane_centers(self) -> list[int]:
        h = int(getattr(self.nav_grid, "height", 0))
        if h <= 0:
            return [0, 0, 0]

        c1 = max(0, min(h - 1, h // 6))
        c2 = max(0, min(h - 1, h // 2))
        c3 = max(0, min(h - 1, (5 * h) // 6))
        return [c1, c2, c3]

    def _find_walkable_near(self, x: int, y: int, max_r: int = 8):
        for r in range(0, max_r + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx = x + dx
                    ny = y + dy
                    if self.nav_grid.is_walkable(nx, ny):
                        return nx, ny
        return None

    def _v_to_move_speed(self, v_value: float) -> float:
        vb = float(self.balance.get("sae", {}).get("v_plus_b", 100.0))
        vb = vb if vb > 0 else 100.0

        MOVE_SPEED_MAX = 4.0
        ratio = max(0.0, min(1.0, float(v_value) / vb))
        speed = ratio * MOVE_SPEED_MAX
        return max(0.6, speed)

    def _pick_unit_key(self) -> str:
        keys = list(self.weights.keys())
        w = [max(0.0, float(self.weights[k])) for k in keys]
        if sum(w) <= 0:
            return "S"
        return random.choices(keys, weights=w, k=1)[0]

    def _ensure_enemy_wallet(self):
        try:
            esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
        except Exception:
            esper.add_component(self.enemy_pyramid_eid, Wallet(solde=0.0))

    def _spawn_one(self):
        self._ensure_enemy_wallet()

        enemy_wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)

        mp = self.balance.get("map", {})
        spawn = mp.get("enemy_spawn", None)
        if not spawn:
            # fallback: proche de la pyramide ennemie
            et = esper.component_for_entity(self.enemy_pyramid_eid, Transform)
            spawn = [int(round(et.pos[0])), int(round(et.pos[1]))]

        sx = int(spawn[0])
        lane_y = random.choice(self._lane_centers())
        sy = int(lane_y)

        found = self._find_walkable_near(sx - 2, sy, max_r=10)
        if not found:
            self.last_message = "Enemy: no spawn found"
            return
        gx, gy = found

        unit_key = self._pick_unit_key()
        st = self.factory.compute_unit_stats(unit_key)

        # économie : si pas assez => on attend
        if enemy_wallet.solde < st.cost:
            self.last_message = "Enemy: waiting money"
            return

        enemy_wallet.solde -= float(st.cost)

        # goal = pyramide joueur
        pt = esper.component_for_entity(self.player_pyramid_eid, Transform)
        goal_x = int(round(pt.pos[0]))
        goal_y = int(round(pt.pos[1]))

        hp_by_type = {"S": 30, "M": 45, "L": 60}
        hp = int(hp_by_type.get(unit_key, 35))

        move_speed = self._v_to_move_speed(st.speed)

        esper.create_entity(
            Transform(pos=(float(gx), float(gy))),
            GridPosition(gx, gy),
            Velocity(0.0, 0.0),
            Speed(base=float(move_speed), mult_terrain=1.0),
            Team(2),
            Health(hp_max=hp, hp=hp),
            UnitStats(speed=float(st.speed), power=float(st.power), armor=float(st.armor), cost=float(st.cost)),
            UnitType(key=str(unit_key)),
            PathRequest(goal=GridPosition(goal_x, goal_y))
        )

        self.last_message = f"Enemy spawn {unit_key}"

    def process(self, dt: float):
        if dt <= 0:
            return

        # delay au début
        if self.start_delay > 0:
            self.start_delay = max(0.0, self.start_delay - dt)
            return

        # si burst en cours
        if self._burst_left > 0:
            self._burst_timer += dt
            if self._burst_timer >= self.burst_spacing:
                self._burst_timer = 0.0
                self._spawn_one()
                self._burst_left -= 1
            return

        # tick normal
        self.timer += dt
        if self.timer >= self.spawn_interval:
            self.timer = 0.0
            self.wave_index += 1

            # démarre un burst (spawn_one + le reste)
            self._spawn_one()
            self._burst_left = max(0, self.burst_count - 1)
            self._burst_timer = 0.0
