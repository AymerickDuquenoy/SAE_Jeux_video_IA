# Game/Ecs/Systems/DifficultySystem.py
import esper

from Game.Ecs.Components.incomeRate import IncomeRate


class DifficultySystem(esper.Processor):
    """
    Monte la difficulté au fil du temps:
    - intervalle de spawn ennemi diminue
    - burst augmente
    - poids S/M/L évoluent
    - income ennemi augmente (pour pouvoir payer les gros spawns)
    """

    def __init__(self, balance: dict, enemy_spawner, enemy_pyramid_eid: int):
        super().__init__()
        self.balance = balance
        self.enemy_spawner = enemy_spawner
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)

        cfg = balance.get("difficulty", {})
        self.step_seconds = float(cfg.get("step_seconds", 20.0))
        self.level_max = int(cfg.get("level_max", 20))

        self.spawn_interval_base = float(cfg.get("spawn_interval_base", 5.0))
        self.spawn_interval_min = float(cfg.get("spawn_interval_min", 1.8))
        self.spawn_interval_decay = float(cfg.get("spawn_interval_decay", 0.93))

        self.burst_every_levels = int(cfg.get("burst_every_levels", 3))
        self.burst_max = int(cfg.get("burst_max", 5))

        self.enemy_income_base = float(cfg.get("enemy_income_base", 2.0))
        self.enemy_income_per_level = float(cfg.get("enemy_income_per_level", 0.25))

        self.elapsed = 0.0
        self.level = 1
        self._next_step = self.step_seconds

        self._apply()  # init

    def hud_line(self) -> str:
        left = max(0.0, self._next_step - self.elapsed)
        return f"Difficulty: {self.level}/{self.level_max} | next in {left:.0f}s"

    def _ensure_enemy_income(self):
        try:
            esper.component_for_entity(self.enemy_pyramid_eid, IncomeRate)
        except Exception:
            esper.add_component(self.enemy_pyramid_eid, IncomeRate(rate=self.enemy_income_base))

    def _weights_for_level(self, lvl: int) -> dict:
        # début: beaucoup de S, puis on glisse vers M/L
        t = max(0.0, min(1.0, (lvl - 1) / max(1, (self.level_max - 1))))
        wS = 0.60 - 0.35 * t
        wM = 0.30 + 0.15 * t
        wL = 0.10 + 0.20 * t
        return {"S": max(0.05, wS), "M": max(0.05, wM), "L": max(0.05, wL)}

    def _apply(self):
        lvl = max(1, min(self.level_max, int(self.level)))

        # intervalle
        interval = self.spawn_interval_base * (self.spawn_interval_decay ** (lvl - 1))
        interval = max(self.spawn_interval_min, interval)

        # burst
        burst = 1 + ((lvl - 1) // max(1, self.burst_every_levels))
        burst = max(1, min(self.burst_max, burst))

        # poids
        weights = self._weights_for_level(lvl)

        self.enemy_spawner.set_params(spawn_interval=interval, burst_count=burst, weights=weights)

        # income ennemi
        self._ensure_enemy_income()
        inc = esper.component_for_entity(self.enemy_pyramid_eid, IncomeRate)
        inc.rate = max(0.0, self.enemy_income_base + (lvl - 1) * self.enemy_income_per_level)

    def process(self, dt: float):
        if dt <= 0:
            return

        self.elapsed += dt

        if self.level < self.level_max and self.elapsed >= self._next_step:
            self.level += 1
            self._next_step += self.step_seconds
            self._apply()
