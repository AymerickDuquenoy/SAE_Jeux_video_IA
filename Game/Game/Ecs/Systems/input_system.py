# Game/Ecs/Systems/input_system.py
import pygame
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.lane import Lane


class InputSystem(esper.Processor):
    """
    Input simple (sans IA) :
    - Z / X / C : choisir la lane (1 / 2 / 3)
    - 1 / 2 / 3 : spawn S / M / L dans la lane sélectionnée
    """

    def __init__(self, factory, balance, player_pyramid_eid: int, enemy_pyramid_eid: int, nav_grid, *, lanes_y=None):
        super().__init__()
        self.factory = factory
        self.balance = balance
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.nav_grid = nav_grid

        # lanes calculées dans game_app.py (utile pour cohérence affichage)
        self.lanes_y = list(lanes_y) if lanes_y else None

        self.last_message = ""
        self.selected_lane = 1  # lane 2 par défaut (0..2)

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
        vb = float(self.balance.get("sae", {}).get("v_plus_b", 100.0))
        vb = vb if vb > 0 else 100.0

        MOVE_SPEED_MAX = 4.0  # 100 de V => 4 cases/s (ajustable)
        ratio = max(0.0, min(1.0, float(v_value) / vb))
        speed = ratio * MOVE_SPEED_MAX

        return max(0.6, speed)

    def _spawn_unit_player(self, unit_key: str):
        try:
            wallet = esper.component_for_entity(self.player_pyramid_eid, Wallet)
            p_t = esper.component_for_entity(self.player_pyramid_eid, Transform)
        except KeyError:
            self.last_message = "Match not ready"
            return

        st = self.factory.compute_unit_stats(unit_key)

        if wallet.solde < st.cost:
            self.last_message = f"Not enough money (need {int(st.cost)})"
            return

        px = int(round(p_t.pos[0]))
        py = int(round(p_t.pos[1]))

        # ✅ spawn "collé" à la pyramide selon la lane (haut / droite / bas)
        if self.selected_lane == 0:
            spawn_x = px
            spawn_y = py - 1
        elif self.selected_lane == 1:
            spawn_x = px + 1
            spawn_y = py
        else:
            spawn_x = px
            spawn_y = py + 1

        found = self._find_walkable_near(int(spawn_x), int(spawn_y), max_r=12)
        if not found:
            self.last_message = "No walkable spawn found"
            return

        gx, gy = found

        wallet.solde -= float(st.cost)

        # spawn via factory => respecte SAÉ strict (C=kP, V+B=const, HP=B+1)
        ent = self.factory.create_unit(unit_key, team_id=1, grid_pos=(int(gx), int(gy)))

        # Son de spawn
        try:
            from Game.Audio.sound_manager import sound_manager
            sound_manager.play("spawn")
        except:
            pass

        if not esper.has_component(ent, Velocity):
            esper.add_component(ent, Velocity(0.0, 0.0))

        # Speed.base jouable
        move_speed = self._v_to_move_speed(st.speed)
        try:
            sp = esper.component_for_entity(ent, Speed)
            sp.base = float(move_speed)
        except Exception:
            esper.add_component(ent, Speed(base=float(move_speed), mult_terrain=1.0))

        # Path vide : LaneRouteSystem va le remplir
        if not esper.has_component(ent, Path):
            esper.add_component(ent, Path([]))
        if not esper.has_component(ent, PathProgress):
            esper.add_component(ent, PathProgress(index=0))
        
        # CORRECTION: Assigner le composant Lane avec la lane sélectionnée
        lane_y = float(self.lanes_y[self.selected_lane]) if self.lanes_y else 0.0
        esper.add_component(ent, Lane(index=self.selected_lane, y_position=lane_y))

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

        # 1/2/3 -> types S/M/L (à garder cohérent avec EntityFactory)
        if self._just_pressed(keys, pygame.K_1):
            self._spawn_unit_player("S")
        if self._just_pressed(keys, pygame.K_2):
            self._spawn_unit_player("M")
        if self._just_pressed(keys, pygame.K_3):
            self._spawn_unit_player("L")
