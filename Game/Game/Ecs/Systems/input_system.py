# Game/Ecs/Systems/input_system.py
"""
Input System avec support pour 2 joueurs (mode 1v1).

Joueur 1 (Équipe 1 - Gauche):
- Z / X / C : choisir la lane (1 / 2 / 3)
- 1 / 2 / 3 : spawn Momie / Dromadaire / Sphinx

Joueur 2 (Équipe 2 - Droite, uniquement en mode 1v1):
- I / O / P : choisir la lane (1 / 2 / 3)
- 7 / 8 / 9 : spawn Momie / Dromadaire / Sphinx
"""
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
    Input avec support 1v1.
    En mode solo, seul le joueur 1 est actif.
    En mode 1v1, les deux joueurs peuvent jouer.
    """

    # Initialise le système d'input avec support 1v1, factory et configuration des touches
    def __init__(self, factory, balance, player_pyramid_eid: int, enemy_pyramid_eid: int, nav_grid, *, lanes_y=None, game_mode="solo", keybindings=None):
        super().__init__()
        self.factory = factory
        self.balance = balance
        self.player_pyramid_eid = int(player_pyramid_eid)
        self.enemy_pyramid_eid = int(enemy_pyramid_eid)
        self.nav_grid = nav_grid
        self.game_mode = game_mode  # "solo" ou "1v1"

        # lanes calculées dans game_app.py (utile pour cohérence affichage)
        self.lanes_y = list(lanes_y) if lanes_y else None

        # Configuration des touches
        self.keybindings = keybindings if keybindings else {
            "p1_lane1": pygame.K_z, "p1_lane2": pygame.K_x, "p1_lane3": pygame.K_c,
            "p1_unit_s": pygame.K_1, "p1_unit_m": pygame.K_2, "p1_unit_l": pygame.K_3,
            "p2_lane1": pygame.K_i, "p2_lane2": pygame.K_o, "p2_lane3": pygame.K_p,
            "p2_unit_s": pygame.K_7, "p2_unit_m": pygame.K_8, "p2_unit_l": pygame.K_9,
        }

        self.last_message = ""
        self.last_message_p2 = ""
        self.selected_lane = 1  # Joueur 1 - lane 2 par défaut (0..2)
        self.selected_lane_p2 = 1  # Joueur 2 - lane 2 par défaut

        self._prev = {}

    # Détecte si une touche vient juste d'être pressée (pas maintenue)
    def _just_pressed(self, keys, key_code: int) -> bool:
        now = bool(keys[key_code])
        before = bool(self._prev.get(key_code, False))
        self._prev[key_code] = now
        return now and not before

    # Calcule les positions Y centrales des 3 lanes
    def _lane_centers(self) -> list[int]:
        h = int(getattr(self.nav_grid, "height", 0))
        if h <= 0:
            return [0, 0, 0]
        c1 = max(0, min(h - 1, h // 6))
        c2 = max(0, min(h - 1, h // 2))
        c3 = max(0, min(h - 1, (5 * h) // 6))
        return [c1, c2, c3]

    # Trouve une case marchable proche d'une position donnée
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

    # Convertit la valeur de vitesse SAÉ en vitesse de déplacement
    def _v_to_move_speed(self, v_value: float) -> float:
        vb = float(self.balance.get("sae", {}).get("v_plus_b", 100.0))
        vb = vb if vb > 0 else 100.0

        MOVE_SPEED_MAX = 4.0  # 100 de V => 4 cases/s (ajustable)
        ratio = max(0.0, min(1.0, float(v_value) / vb))
        speed = ratio * MOVE_SPEED_MAX

        return max(0.6, speed)

    # Fait apparaître une unité pour le joueur 1 sur la lane sélectionnée
    def _spawn_unit_player(self, unit_key: str):
        """Spawn une unité pour le joueur 1 (inchangé)."""
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

        # spawn "collé" à la pyramide selon la lane (haut / droite / bas)
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

        # spawn via factory
        ent = self.factory.create_unit(unit_key, team_id=1, grid_pos=(int(gx), int(gy)))

        # Son de spawn
        try:
            from Game.Audio.sound_manager import sound_manager
            sound_manager.play("spawn")
        except ImportError:
            try:
                from Audio.sound_manager import sound_manager
                sound_manager.play("spawn")
            except:
                pass
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
        
        # Assigner le composant Lane avec la lane sélectionnée
        lane_y = float(self.lanes_y[self.selected_lane]) if self.lanes_y else 0.0
        esper.add_component(ent, Lane(index=self.selected_lane, y_position=lane_y))

        self.last_message = f"Spawn {unit_key} in lane {self.selected_lane + 1}"

    # Fait apparaître une unité pour le joueur 2 en mode 1v1
    def _spawn_unit_player2(self, unit_key: str):
        """Spawn une unité pour le joueur 2 (mode 1v1 uniquement)."""
        if self.game_mode != "1v1":
            return
            
        try:
            wallet = esper.component_for_entity(self.enemy_pyramid_eid, Wallet)
            p_t = esper.component_for_entity(self.enemy_pyramid_eid, Transform)
        except KeyError:
            self.last_message_p2 = "P2: Match not ready"
            return

        st = self.factory.compute_unit_stats(unit_key)

        if wallet.solde < st.cost:
            self.last_message_p2 = f"P2: Not enough ({int(st.cost)})"
            return

        px = int(round(p_t.pos[0]))
        py = int(round(p_t.pos[1]))

        # Spawn pour P2 : à gauche de sa pyramide
        if self.selected_lane_p2 == 0:
            spawn_x = px
            spawn_y = py - 1
        elif self.selected_lane_p2 == 1:
            spawn_x = px - 1
            spawn_y = py
        else:
            spawn_x = px
            spawn_y = py + 1

        found = self._find_walkable_near(int(spawn_x), int(spawn_y), max_r=12)
        if not found:
            self.last_message_p2 = "P2: No spawn found"
            return

        gx, gy = found

        wallet.solde -= float(st.cost)

        # Créer l'unité pour l'équipe 2
        ent = self.factory.create_unit(unit_key, team_id=2, grid_pos=(int(gx), int(gy)))

        # Son de spawn
        try:
            from Game.Audio.sound_manager import sound_manager
            sound_manager.play("spawn")
        except ImportError:
            try:
                from Audio.sound_manager import sound_manager
                sound_manager.play("spawn")
            except:
                pass
        except:
            pass

        if not esper.has_component(ent, Velocity):
            esper.add_component(ent, Velocity(0.0, 0.0))

        move_speed = self._v_to_move_speed(st.speed)
        try:
            sp = esper.component_for_entity(ent, Speed)
            sp.base = float(move_speed)
        except Exception:
            esper.add_component(ent, Speed(base=float(move_speed), mult_terrain=1.0))

        if not esper.has_component(ent, Path):
            esper.add_component(ent, Path([]))
        if not esper.has_component(ent, PathProgress):
            esper.add_component(ent, PathProgress(index=0))
        
        # Assigner le composant Lane pour P2
        lane_y = float(self.lanes_y[self.selected_lane_p2]) if self.lanes_y else 0.0
        esper.add_component(ent, Lane(index=self.selected_lane_p2, y_position=lane_y))

        self.last_message_p2 = f"P2: {unit_key} lane {self.selected_lane_p2 + 1}"

    # Traite les inputs clavier pour sélection de lanes et spawn d'unités
    def process(self, dt: float):
        keys = pygame.key.get_pressed()

        # ========== JOUEUR 1 ==========
        # Sélection de lane
        if self._just_pressed(keys, self.keybindings["p1_lane1"]):
            self.selected_lane = 0
            self.last_message = "Lane 1 selected"
        if self._just_pressed(keys, self.keybindings["p1_lane2"]):
            self.selected_lane = 1
            self.last_message = "Lane 2 selected"
        if self._just_pressed(keys, self.keybindings["p1_lane3"]):
            self.selected_lane = 2
            self.last_message = "Lane 3 selected"

        # Spawn unités
        if self._just_pressed(keys, self.keybindings["p1_unit_s"]):
            self._spawn_unit_player("S")
        if self._just_pressed(keys, self.keybindings["p1_unit_m"]):
            self._spawn_unit_player("M")
        if self._just_pressed(keys, self.keybindings["p1_unit_l"]):
            self._spawn_unit_player("L")

        # ========== JOUEUR 2 (mode 1v1 uniquement) ==========
        if self.game_mode == "1v1":
            # Sélection de lane
            if self._just_pressed(keys, self.keybindings["p2_lane1"]):
                self.selected_lane_p2 = 0
                self.last_message_p2 = "P2: Lane 1"
            if self._just_pressed(keys, self.keybindings["p2_lane2"]):
                self.selected_lane_p2 = 1
                self.last_message_p2 = "P2: Lane 2"
            if self._just_pressed(keys, self.keybindings["p2_lane3"]):
                self.selected_lane_p2 = 2
                self.last_message_p2 = "P2: Lane 3"

            # Spawn unités
            if self._just_pressed(keys, self.keybindings["p2_unit_s"]):
                self._spawn_unit_player2("S")
            if self._just_pressed(keys, self.keybindings["p2_unit_m"]):
                self._spawn_unit_player2("M")
            if self._just_pressed(keys, self.keybindings["p2_unit_l"]):
                self._spawn_unit_player2("L")