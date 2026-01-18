# Game/Ecs/Systems/input_system.py
import pygame
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


class InputSystem(esper.Processor):
    """
    Input simple (sans IA) :
    - Z / X / C : choisir la lane (1 / 2 / 3)
    - 1 / 2 / 3 : spawn Momie / Dromadaire / Sphinx dans la lane sélectionnée
    """

    def __init__(self, factory, balance, player_pyramid_eid: int, enemy_pyramid_eid: int, nav_grid):
        super().__init__()
        self.factory = factory
        self.balance = balance
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.nav_grid = nav_grid

        self.last_message = ""
        self.selected_lane = 1  # 0..2 (par défaut lane 2)

        self._prev = {}

    def _just_pressed(self, keys, key_code: int) -> bool:
        now = bool(keys[key_code])
        before = bool(self._prev.get(key_code, False))
        self._prev[key_code] = now
        return now and not before

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
                    if hasattr(self.nav_grid, "is_walkable"):
                        if self.nav_grid.is_walkable(nx, ny):
                            return nx, ny
                    else:
                        if 0 <= nx < self.nav_grid.width and 0 <= ny < self.nav_grid.height:
                            if self.nav_grid.walkable[ny][nx]:
                                return nx, ny
        return None

    def _v_to_move_speed(self, v_value: float) -> float:
        """
        Convertit le V de la SAE (ex: 0..100) en vitesse de déplacement (cases / seconde).
        On garde V dans UnitStats pour l'affichage/contrainte, mais Speed.base doit être "jouable".
        """
        vb = float(self.balance.get("sae", {}).get("v_plus_b", 100.0))  # typiquement 100
        vb = vb if vb > 0 else 100.0

        MOVE_SPEED_MAX = 4.0  # 100 de V => 4 cases/s (ajustable)
        ratio = max(0.0, min(1.0, float(v_value) / vb))
        speed = ratio * MOVE_SPEED_MAX

        # évite une vitesse trop lente
        return max(0.6, speed)

    def _spawn_unit_player(self, unit_key: str):
        # sécurité: si jamais le match a été reset et qu'on appuie pile au mauvais moment
        try:
            wallet = esper.component_for_entity(self.player_pyramid_eid, Wallet)
            p_t = esper.component_for_entity(self.player_pyramid_eid, Transform)
            e_t = esper.component_for_entity(self.enemy_pyramid_eid, Transform)
        except KeyError:
            self.last_message = "Match not ready"
            return

        st = self.factory.compute_unit_stats(unit_key)

        if wallet.solde < st.cost:
            self.last_message = f"Not enough money (need {int(st.cost)})"
            return

        px = int(round(p_t.pos[0]))
        ex = int(round(e_t.pos[0]))
        ey = int(round(e_t.pos[1]))

        lane_y = self._lane_centers()[self.selected_lane]

        spawn_x = px + 2
        spawn_y = lane_y

        found = self._find_walkable_near(spawn_x, spawn_y, max_r=10)
        if not found:
            self.last_message = "No walkable spawn found"
            return

        gx, gy = found

        hp_by_type = {"S": 30, "M": 45, "L": 60}
        hp = int(hp_by_type.get(unit_key, 35))

        wallet.solde -= float(st.cost)

        move_speed = self._v_to_move_speed(st.speed)

        esper.create_entity(
            Transform(pos=(float(gx), float(gy))),
            GridPosition(gx, gy),
            Velocity(0.0, 0.0),
            Speed(base=float(move_speed), mult_terrain=1.0),  # <-- FIX IMPORTANT
            Team(1),
            Health(hp_max=hp, hp=hp),
            UnitStats(speed=float(st.speed), power=float(st.power), armor=float(st.armor), cost=float(st.cost)),
            PathRequest(goal=GridPosition(ex, ey))
        )

        self.last_message = f"Spawn {unit_key} in lane {self.selected_lane + 1}"

    def process(self, dt: float):
        keys = pygame.key.get_pressed()

        if self._just_pressed(keys, pygame.K_z):
            self.selected_lane = 0
            self.last_message = "Lane 1 selected"
        if self._just_pressed(keys, pygame.K_x):
            self.selected_lane = 1
            self.last_message = "Lane 2 selected"
        if self._just_pressed(keys, pygame.K_c):
            self.selected_lane = 2
            self.last_message = "Lane 3 selected"

        if self._just_pressed(keys, pygame.K_1):
            self._spawn_unit_player("S")  # Momie
        if self._just_pressed(keys, pygame.K_2):
            self._spawn_unit_player("M")  # Dromadaire
        if self._just_pressed(keys, pygame.K_3):
            self._spawn_unit_player("L")  # Sphinx
