# Game/Ecs/Systems/RandomEventSystem.py
import random
import esper

from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.incomeRate import IncomeRate

from Game.Ecs.Components.affectable_by_event import AffectableByEvent, EventFlag


class RandomEventSystem(esper.Processor):
    """
    P1.3 - Evénements aléatoires pour rendre le jeu "rejouable" façon jeu flash.

    Events inclus :
    - sandstorm : inverse temporairement open/dusty (via nav_grid.mult)
    - locusts   : dégâts réguliers sur les unités (en hits), neutre (pas de reward)
    - delivery  : buff économie (IncomeRate x1.25 pendant X secondes)
    """

    def __init__(self, *, balance: dict, nav_grid, player_pyramid_eid: int):
        super().__init__()
        self.balance = balance or {}
        self.nav_grid = nav_grid
        self.player_pyramid_eid = int(player_pyramid_eid)

        cfg = dict(self.balance.get("events", {}) or {})

        self.interval_min = float(cfg.get("interval_min", 12.0))
        self.interval_max = float(cfg.get("interval_max", 22.0))

        self.weight_sandstorm = float(cfg.get("weight_sandstorm", 0.40))
        self.weight_locusts = float(cfg.get("weight_locusts", 0.35))
        self.weight_delivery = float(cfg.get("weight_delivery", 0.25))

        self.sandstorm_duration = float(cfg.get("sandstorm_duration", 9.0))
        self.locust_duration = float(cfg.get("locust_duration", 8.0))
        self.locust_tick = float(cfg.get("locust_tick", 1.0))
        self.locust_power = float(cfg.get("locust_power", 6.0))

        self.delivery_duration = float(cfg.get("delivery_duration", 10.0))
        self.delivery_mult = float(cfg.get("delivery_mult", 1.25))

        # Etat runtime
        self.active_event = None
        self.time_left = 0.0

        self._next_timer = self._roll_next_timer()

        # Sandstorm : on stock la grille de base pour restore
        self._base_mult = None
        self._dusty_ref = float(cfg.get("sandstorm_dusty_mult", 0.60))

        # Locusts : tick interne
        self._locust_tick_timer = 0.0

        # Delivery : restore income
        self._delivery_saved_income = None

        self._cache_base_grid()

    def _roll_next_timer(self) -> float:
        a = min(self.interval_min, self.interval_max)
        b = max(self.interval_min, self.interval_max)
        return random.uniform(a, b)

    def _cache_base_grid(self):
        if not self.nav_grid:
            return

        try:
            self._base_mult = [row[:] for row in self.nav_grid.mult]
        except Exception:
            self._base_mult = None
            return

        # essaye de deviner une valeur "dusty" depuis la map si possible
        # (on prend un mult entre 0 et 1 qui n'est pas ~1)
        candidates = []
        for row in self._base_mult:
            for m in row:
                try:
                    m = float(m)
                except Exception:
                    continue
                if 0.0 < m < 0.98:
                    candidates.append(m)

        if candidates:
            candidates.sort()
            self._dusty_ref = candidates[len(candidates) // 2]  # médiane

        # garde-fous
        self._dusty_ref = max(0.10, min(0.95, float(self._dusty_ref)))

    def hud_line(self) -> str:
        if self.active_event is None:
            return f"Next event: {self._next_timer:.1f}s"
        return f"Event: {self._event_pretty_name(self.active_event)} ({self.time_left:.1f}s)"

    def _event_pretty_name(self, ev: str) -> str:
        if ev == "sandstorm":
            return "Sandstorm (swap zones)"
        if ev == "locusts":
            return "Locust swarm"
        if ev == "delivery":
            return "Whip delivery"
        return str(ev)

    def _start_random_event(self):
        events = [
            ("sandstorm", self.weight_sandstorm),
            ("locusts", self.weight_locusts),
            ("delivery", self.weight_delivery),
        ]

        total = sum(max(0.0, w) for _, w in events)
        if total <= 0.0:
            self._next_timer = self._roll_next_timer()
            return

        r = random.uniform(0.0, total)
        acc = 0.0
        choice = "sandstorm"
        for name, w in events:
            w = max(0.0, float(w))
            acc += w
            if r <= acc:
                choice = name
                break

        self.active_event = choice

        if choice == "sandstorm":
            self.time_left = self.sandstorm_duration
            self._start_sandstorm()
        elif choice == "locusts":
            self.time_left = self.locust_duration
            self._start_locusts()
        elif choice == "delivery":
            self.time_left = self.delivery_duration
            self._start_delivery()
        else:
            self.time_left = 6.0

    def _end_current_event(self):
        ev = self.active_event
        if ev == "sandstorm":
            self._end_sandstorm()
        elif ev == "locusts":
            self._end_locusts()
        elif ev == "delivery":
            self._end_delivery()

        self.active_event = None
        self.time_left = 0.0
        self._next_timer = self._roll_next_timer()

    # ---------------------------
    # Sandstorm
    # ---------------------------
    def _start_sandstorm(self):
        if not self.nav_grid or self._base_mult is None:
            return

        h = int(getattr(self.nav_grid, "height", 0))
        w = int(getattr(self.nav_grid, "width", 0))
        if w <= 0 or h <= 0:
            return

        for y in range(h):
            for x in range(w):
                base = float(self._base_mult[y][x])
                if base <= 0.0:
                    self.nav_grid.mult[y][x] = 0.0
                    continue

                # open (≈1) devient dusty, dusty devient open
                if base >= 0.98:
                    self.nav_grid.mult[y][x] = float(self._dusty_ref)
                else:
                    self.nav_grid.mult[y][x] = 1.0

    def _end_sandstorm(self):
        if not self.nav_grid or self._base_mult is None:
            return

        h = int(getattr(self.nav_grid, "height", 0))
        w = int(getattr(self.nav_grid, "width", 0))
        if w <= 0 or h <= 0:
            return

        for y in range(h):
            for x in range(w):
                self.nav_grid.mult[y][x] = float(self._base_mult[y][x])

    # ---------------------------
    # Locusts
    # ---------------------------
    def _start_locusts(self):
        self._locust_tick_timer = 0.0

    def _end_locusts(self):
        self._locust_tick_timer = 0.0

    def _apply_locust_hit_once(self):
        # Dégâts neutres (pas de "reward"), juste pour mettre la pression.
        # On reste simple : on touche uniquement les unités (UnitStats + Health).
        dmg = int(round(float(self.locust_power)))
        if dmg <= 0:
            return

        for eid, (stats, hp) in esper.get_components(UnitStats, Health):
            if hp.is_dead:
                continue

            # si l'unité a un filtre d'events, on le respecte
            if esper.has_component(eid, AffectableByEvent):
                aff = esper.component_for_entity(eid, AffectableByEvent)
                if not aff.accepts(EventFlag.DAMAGE):
                    continue

            hp.hp = max(0, int(hp.hp - dmg))

    # ---------------------------
    # Delivery
    # ---------------------------
    def _start_delivery(self):
        # Buff uniquement côté joueur (sinon ça sert à rien pour l'instant)
        try:
            income = esper.component_for_entity(self.player_pyramid_eid, IncomeRate)
        except Exception:
            # si pas présent, on crée un rate de base
            base_income = float(self.balance.get("pyramid", {}).get("income_base", 2.0))
            income = IncomeRate(rate=base_income)
            esper.add_component(self.player_pyramid_eid, income)

        self._delivery_saved_income = float(income.rate)
        income.rate = float(income.rate) * float(self.delivery_mult)

    def _end_delivery(self):
        if self._delivery_saved_income is None:
            return
        try:
            income = esper.component_for_entity(self.player_pyramid_eid, IncomeRate)
            income.rate = float(self._delivery_saved_income)
        except Exception:
            pass
        self._delivery_saved_income = None

    # ---------------------------
    # process
    # ---------------------------
    def process(self, dt: float):
        if dt <= 0:
            return

        # Pas d'event actif => on attend
        if self.active_event is None:
            self._next_timer -= float(dt)
            if self._next_timer <= 0.0:
                self._start_random_event()
            return

        # Event actif
        self.time_left -= float(dt)

        if self.active_event == "locusts":
            self._locust_tick_timer -= float(dt)
            while self._locust_tick_timer <= 0.0:
                self._apply_locust_hit_once()
                self._locust_tick_timer += max(0.1, float(self.locust_tick))

        if self.time_left <= 0.0:
            self._end_current_event()
