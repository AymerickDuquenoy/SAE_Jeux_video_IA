# Game/App/game_app.py
import json
import random
import os
import pygame
import esper
from pathlib import Path
import xml.etree.ElementTree as ET

# Pour le blur du menu
try:
    from PIL import Image, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from Game.Ecs.world import World
from Game.Utils.clock import GameClock
from Game.Utils.event_bus import EventBus
from Game.Map.GridMap import GridMap
from Game.Utils.balance_config import BalanceConfig
from Game.Factory.entity_factory import EntityFactory

from Game.Map.NavigationGrid import NavigationGrid
from Game.Map.GridTile import GridTile

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.path import Path as PathComponent
from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.incomeRate import IncomeRate
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.pyramidLevel import PyramidLevel

from Game.Ecs.Systems.EnemySpawnerSystem import EnemySpawnerSystem

from Game.Ecs.Systems.LaneRouteSystem import LaneRouteSystem
from Game.Map.terrain_randomizer import apply_random_terrain

from Game.Rendering.game_renderer import GameRenderer
from Game.Utils.lane_pathfinder import LanePathfinder
from Game.Utils.grid_utils import GridUtils


# UI : si tu as déjà Game/App/ui.py, il sera pris
try:
    from Game.App.ui import UIButton, UIToggle, UIMenuButton, UISelector
except Exception:
    class UIButton:
        def __init__(self, rect, text, font):
            self.rect = rect
            self.text = text
            self.font = font

        def handle_event(self, event):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                return self.rect.collidepoint(mx, my)
            return False

        def draw(self, screen):
            pygame.draw.rect(screen, (35, 35, 40), self.rect, border_radius=12)
            pygame.draw.rect(screen, (80, 80, 90), self.rect, width=2, border_radius=12)
            s = self.font.render(self.text, True, (240, 240, 240))
            r = s.get_rect(center=self.rect.center)
            screen.blit(s, r)

    class UIToggle:
        def __init__(self, rect, label, font, value=False):
            self.rect = rect
            self.label = label
            self.font = font
            self.value = bool(value)

        def handle_event(self, event):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if self.rect.collidepoint(mx, my):
                    self.value = not self.value
                    return True
            return False

        def draw(self, screen):
            pygame.draw.rect(screen, (35, 35, 40), self.rect, border_radius=12)
            pygame.draw.rect(screen, (80, 80, 90), self.rect, width=2, border_radius=12)

            txt = f"{self.label}: {'ON' if self.value else 'OFF'}"
            s = self.font.render(txt, True, (240, 240, 240))
            screen.blit(s, (self.rect.x + 16, self.rect.y + 14))


def _write_generated_tmx(
    output_path: Path,
    *,
    seed: int,
    width: int,
    height: int,
    tilewidth: int,
    tileheight: int,
    sand_tileset_source: str = "sable.tsx",
    quicksand_tileset_source: str = "sable_mouvant.tsx",
    sand_firstgid: int = 1,
    sand_tilecount: int = 24,
    quicksand_firstgid: int = 25,
    quicksand_tile_id: int = 20,  # => gid 45 (25+20)
    quicksand_rects: int = 7,
):
    """
    Génère un TMX VISUEL aléatoire à chaque partie :
    - sable : gid dans [1..24] (variations visuelles)
    - sables mouvants : gid = 25 + 20 = 45 (tilset sable_mouvant.tsx tile id 20)
    On ne gère pas ici la zone "interdit" (ça reste ta couche SAÉ apply_random_terrain sur NavigationGrid)
    """
    rng = random.Random(seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    quick_gid = int(quicksand_firstgid + quicksand_tile_id)

    # Base sable random
    grid = []
    for _y in range(height):
        row = []
        for _x in range(width):
            row.append(rng.randint(sand_firstgid, sand_firstgid + sand_tilecount - 1))
        grid.append(row)

    # Patchs quicksand
    for _ in range(int(quicksand_rects)):
        rw = rng.randint(3, 8)
        rh = rng.randint(2, 5)
        x0 = rng.randint(1, max(1, width - 2 - rw))
        y0 = rng.randint(1, max(1, height - 2 - rh))

        for yy in range(y0, min(height - 1, y0 + rh)):
            for xx in range(x0, min(width - 1, x0 + rw)):
                grid[yy][xx] = quick_gid

    # CSV compatible pytmx :
    row_lines = []
    for row in grid:
        row_lines.append(",".join(str(v) for v in row))

    # Important : virgule entre les lignes
    csv_text = ",\n".join(row_lines)

    # XML TMX minimal
    root = ET.Element(
        "map",
        {
            "version": "1.10",
            "tiledversion": "1.11.2",
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "width": str(width),
            "height": str(height),
            "tilewidth": str(tilewidth),
            "tileheight": str(tileheight),
            "infinite": "0",
            "nextlayerid": "2",
            "nextobjectid": "1",
        },
    )

    ET.SubElement(root, "tileset", {"firstgid": str(sand_firstgid), "source": sand_tileset_source})
    ET.SubElement(root, "tileset", {"firstgid": str(quicksand_firstgid), "source": quicksand_tileset_source})

    layer = ET.SubElement(
        root,
        "layer",
        {"id": "1", "name": "Calque de Tuiles 1", "width": str(width), "height": str(height)},
    )
    data = ET.SubElement(layer, "data", {"encoding": "csv"})
    data.text = "\n" + csv_text + "\n"

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


class GameApp:
    def __init__(self, width: int = 800, height: int = 600, title: str = "Antique War"):
        # Résolution de base (interne) - le jeu est TOUJOURS rendu à cette taille
        self.base_width = 960
        self.base_height = 640
        
        # Résolution de la fenêtre (mode fenêtré)
        self.window_width = width
        self.window_height = height
        
        # Résolution actuelle de l'écran (peut changer selon le mode)
        self.width = width
        self.height = height
        self.title = title

        self.screen = None
        self.game_surface = None  # Surface de rendu interne (toujours 960x640)
        self.running = False
        
        # Résolution native de l'écran (sera mise à jour dans boot())
        self.native_width = 1920
        self.native_height = 1080
        
        # Scaling info
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.render_offset_x = 0
        self.render_offset_y = 0

        self.font = None
        self.font_small = None
        self.font_big = None

        self.clock = GameClock(fps=60)
        self.bus = EventBus()

        self.game_root = Path(__file__).resolve().parents[1]  # .../Game
        self.save_path = self.game_root / "assets" / "config" / "save.json"

        self.game_map = None
        self.balance = None

        self.map_files = []
        self.nav_grid = None

        # match state
        self.world = None
        self.match_index = 0

        self.player_pyramid_eid = None
        self.enemy_pyramid_eid = None

        self.factory = None

        self.input_system = None
        self.economy_system = None
        self.upgrade_system = None
        self.astar_system = None
        self.terrain_system = None
        self.nav_system = None
        self.targeting_system = None
        self.combat_system = None
        self.projectile_system = None
        self.cleanup_system = None
        self.enemy_spawner_system = None
        self.difficulty_system = None
        self.random_event_system = None
        self.pyramid_defense_system = None
        self.ai_behavior_system = None


        # ✅ AJOUT : enemy systems (sinon aucun spawn)
        self.difficulty_system = None
        self.enemy_spawner_system = None

        # Renderer
        self.renderer = None
        
        # Utils
        self.pathfinder = None
        self.grid_utils = None

        self.camera_x = 0.0
        self.camera_y = 0.0

        # UI / state machine
        self.state = "menu"  # menu/options/controls/difficulty_select/playing/pause/game_over
        self.state_return = "menu"
        self.game_over_text = ""
        
        # Difficulté choisie
        self.selected_difficulty = "medium"  # easy/medium/hard/extreme

        # options
        self.opt_show_terrain = False
        self.opt_show_paths = False
        self.opt_show_lanes = False
        
        # Options d'affichage
        self.available_resolutions = [
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1280, 800),
            (1366, 768),
            (1440, 900),
            (1600, 900),
            (1920, 1080),
        ]
        self.current_resolution_index = 0  # 800x600 par défaut
        
        # Mode d'affichage simplifié : juste fenêtré ou plein écran
        self.is_fullscreen = False

        # ✅ lane sélectionnée (0..2) -> lane2 par défaut
        self.selected_lane_idx = 1

        # stats (replay)
        self.match_time = 0.0
        self.enemy_kills = 0
        self.best_time = 0.0
        self.best_kills = 0
        self._prev_enemy_ids = set()

        # random map info
        self.last_map_seed = 0
        self.last_zone_counts = {"open": 0, "dusty": 0, "forbidden": 0}
        self.last_map_name = "map.tmx"

        # lanes (réelles, basées sur la pyramide)
        self.lanes_y = [0, 0, 0]
        self.player_pyr_pos = (0, 0)
        self.enemy_pyr_pos = (0, 0)

        # chemins lane (3 lanes) => affichage réaliste
        self.lane_paths = [[], [], []]        # Joueur → Ennemi
        self.lane_paths_enemy = [[], [], []]  # Ennemi → Joueur

        # preview lane (court)
        self.lane_flash_timer = 0.0
        self.lane_flash_duration = 0.85
        self.lane_preview_path = []

        # ✅ AJOUT : tracker unités déjà vues (pour snap spawn lane)
        self._known_units = set()

        # buttons
        self.btn_play = None
        self.btn_options = None
        self.btn_controls = None
        self.btn_quit = None
        self.btn_back = None

        self.btn_resume = None
        self.btn_restart = None
        self.btn_pause_options = None
        self.btn_menu = None

        # toggle options
        self.tog_terrain = None
        self.tog_paths = None
        self.tog_lanes = None
        
        # Options d'affichage
        self.tog_fullscreen = None
        self.sel_resolution = None
        self.btn_apply_display = None

        # lane selector HUD
        self.lane_btn_rects = []
        
        # Boutons HUD (unités + upgrade)
        self.unit_btn_rects = {}  # {"S": rect, "M": rect, "L": rect}
        self.upgrade_btn_rect = None
        self.unit_icons_cache = {}  # Cache pour les icônes des unités
        self.whip_icon = None  # Icône du fouet chargée depuis PNG (image originale)
        self.whip_icons_cache = {}  # Cache pour différentes tailles d'icônes du fouet

    # ----------------------------
    # Selected lane helpers
    # ----------------------------
    def _get_selected_lane_index(self) -> int:
        idx = int(self.selected_lane_idx)

        # si InputSystem a une valeur, on essaye de sync sans casser
        if self.input_system:
            for name in ("selected_lane", "selectedLane", "selected_lane_idx", "lane_selected", "lane_index"):
                if hasattr(self.input_system, name):
                    try:
                        v = int(getattr(self.input_system, name))
                        # accepte 0..2
                        if 0 <= v <= 2:
                            idx = v
                        # accepte 1..3 (si jamais)
                        elif 1 <= v <= 3:
                            idx = v - 1
                    except Exception:
                        pass

        idx = max(0, min(2, idx))
        self.selected_lane_idx = idx
        return idx

    def _set_selected_lane_index(self, idx: int):
        idx = max(0, min(2, int(idx)))
        self.selected_lane_idx = idx

        # on pousse aussi dans InputSystem si possible
        if self.input_system:
            for name in ("selected_lane", "selectedLane", "selected_lane_idx", "lane_selected", "lane_index"):
                try:
                    setattr(self.input_system, name, idx)
                except Exception:
                    pass

    # ----------------------------
    # Save
    # ----------------------------
    def _load_save(self):
        self.best_time = 0.0
        self.best_kills = 0
        try:
            if self.save_path.exists():
                data = json.loads(self.save_path.read_text(encoding="utf-8"))
                self.best_time = float(data.get("best_time", 0.0))
                self.best_kills = int(data.get("best_kills", 0))
        except Exception:
            self.best_time = 0.0
            self.best_kills = 0

    def _save_save(self):
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"best_time": float(self.best_time), "best_kills": int(self.best_kills)}
            self.save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ----------------------------
    # Boot
    # ----------------------------
    def boot(self):
        pygame.init()
        pygame.display.set_caption(self.title)
        
        # Stocker la résolution native de l'écran AVANT de créer une fenêtre
        # Utiliser get_desktop_sizes() qui est plus fiable (pygame 2.x)
        try:
            desktop_sizes = pygame.display.get_desktop_sizes()
            if desktop_sizes:
                self.native_width, self.native_height = desktop_sizes[0]
            else:
                info = pygame.display.Info()
                self.native_width = info.current_w
                self.native_height = info.current_h
        except AttributeError:
            # Fallback pour les anciennes versions de pygame
            info = pygame.display.Info()
            self.native_width = info.current_w
            self.native_height = info.current_h
        
        print(f"[INFO] Native screen resolution: {self.native_width}x{self.native_height}")
        
        # Charger les paramètres d'affichage sauvegardés
        self._load_display_settings()
        
        # Créer la fenêtre
        self._apply_display_mode()
        
        # Créer la surface de rendu interne (toujours à la résolution de base)
        self.game_surface = pygame.Surface((self.base_width, self.base_height))
        
        # Calculer le scaling initial
        self._update_scaling()

        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_big = pygame.font.SysFont("consolas", 42)
        
        # Police pour le titre du menu (style égyptien)
        self.font_title = pygame.font.SysFont("georgia", 72)
        
        # Créer le renderer
        self.renderer = GameRenderer(self)
        
        # Créer les utils
        self.pathfinder = LanePathfinder(self)
        self.grid_utils = GridUtils(self)
        
        # Charger l'image de fond du menu (à la taille de BASE, pas de la fenêtre)
        self.menu_background = None
        try:
            menu_bg_path = self.game_root / "assets" / "menu_background.png"
            if menu_bg_path.exists():
                self.menu_background = pygame.image.load(str(menu_bg_path)).convert()
                self.menu_background = pygame.transform.scale(self.menu_background, (self.base_width, self.base_height))
        except Exception as e:
            print(f"[WARN] Could not load menu background: {e}")

        self._load_save()

        balance_file = self.game_root / "assets" / "config" / "balance.json"
        self.balance = BalanceConfig.load(str(balance_file)).data

        maps_dir = self.game_root / "assets" / "map"
        self.map_files = sorted(maps_dir.glob("map_*.tmx"))
        if not self.map_files:
            self.map_files = [maps_dir / "map.tmx"]

        # charge une map pour l’écran menu (juste visuel)
        self._load_map_for_visual(random.choice(self.map_files))

        # Options au boot
        self.opt_show_terrain = False
        self.opt_show_paths = False
        self.opt_show_lanes = False

        # ✅ lane par défaut = 2 au boot
        self.selected_lane_idx = 1

        self._build_ui()

    def shutdown(self):
        pygame.quit()

    # ----------------------------
    # Scaling / Display
    # ----------------------------
    def _update_scaling(self):
        """Calcule les facteurs de scale pour remplir tout l'écran."""
        # Vérifier la vraie taille de l'écran
        actual_size = self.screen.get_size()
        print(f"[SCALE] self.width={self.width}, self.height={self.height}, screen.get_size()={actual_size}")
        
        # Utiliser la vraie taille de l'écran
        self.width, self.height = actual_size
        
        # Scale séparé pour X et Y (remplit tout l'écran, légère déformation possible)
        self.scale_x = self.width / self.base_width
        self.scale_y = self.height / self.base_height
        
        # Pas d'offset - on remplit tout
        self.render_offset_x = 0
        self.render_offset_y = 0
        
        print(f"[SCALE] Final: {self.width}x{self.height} -> scale ({self.scale_x:.3f}, {self.scale_y:.3f})")
        
        print(f"[SCALE] {self.width}x{self.height} -> scale ({self.scale_x:.2f}, {self.scale_y:.2f})")

    def _screen_to_game_coords(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Convertit les coordonnées écran en coordonnées de jeu (surface interne)."""
        if self.scale_x <= 0 or self.scale_y <= 0:
            return screen_x, screen_y
        
        # Convertir avec les facteurs de scale
        game_x = screen_x / self.scale_x
        game_y = screen_y / self.scale_y
        
        # Clamper aux limites de la surface de jeu
        game_x = max(0, min(self.base_width - 1, int(game_x)))
        game_y = max(0, min(self.base_height - 1, int(game_y)))
        
        return game_x, game_y

    def _render_to_screen(self):
        """Scale et affiche la game_surface sur l'écran (remplit tout)."""
        # Scaler la surface de jeu pour remplir tout l'écran
        if self.width > 0 and self.height > 0:
            scaled_surface = pygame.transform.scale(self.game_surface, (self.width, self.height))
            self.screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()

    # ----------------------------
    # UI
    # ----------------------------
    def _sync_toggle_value(self, toggle, value: bool):
        """Sécurise le OFF/ON même si ton ui.py a une logique différente."""
        try:
            toggle.value = bool(value)
        except Exception:
            pass
        for attr in ("is_on", "on", "checked", "state"):
            if hasattr(toggle, attr):
                try:
                    setattr(toggle, attr, bool(value))
                except Exception:
                    pass

    def _apply_display_mode(self):
        """Applique le mode d'affichage actuel."""
        if self.is_fullscreen:
            target_w, target_h = self.window_width, self.window_height
            
            # Si c'est la résolution native, utiliser FULLSCREEN_DESKTOP (pas de changement de résolution)
            if target_w == self.native_width and target_h == self.native_height:
                # Borderless fullscreen - ne change pas la résolution du moniteur
                self.screen = pygame.display.set_mode((self.native_width, self.native_height), pygame.FULLSCREEN_DESKTOP)
                self.width, self.height = self.screen.get_size()
                print(f"[INFO] Using FULLSCREEN_DESKTOP for native resolution")
            else:
                # Fullscreen avec changement de résolution (pour les résolutions inférieures)
                self.width, self.height = target_w, target_h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
                print(f"[INFO] Using FULLSCREEN with resolution change")
        else:
            # Fenêtré : utiliser la résolution de l'index sélectionné
            # Cela évite les problèmes si window_width/height sont à la résolution native
            if 0 <= self.current_resolution_index < len(self.available_resolutions):
                target_w, target_h = self.available_resolutions[self.current_resolution_index]
            else:
                target_w, target_h = self.available_resolutions[0]  # Fallback à la première
                self.current_resolution_index = 0
            
            # Sécurité : ne jamais créer une fenêtre aussi grande que l'écran
            if target_w >= self.native_width or target_h >= self.native_height:
                # Trouver la plus grande résolution qui rentre dans l'écran
                for i in range(len(self.available_resolutions) - 1, -1, -1):
                    res_w, res_h = self.available_resolutions[i]
                    if res_w < self.native_width and res_h < self.native_height:
                        target_w, target_h = res_w, res_h
                        self.current_resolution_index = i
                        break
                else:
                    # Fallback ultime
                    target_w, target_h = self.available_resolutions[0]
                    self.current_resolution_index = 0
                print(f"[INFO] Adjusted window size to {target_w}x{target_h}")
            
            self.window_width, self.window_height = target_w, target_h
            self.width, self.height = target_w, target_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            
            # Mettre à jour l'UI si elle existe
            if self.sel_resolution:
                self.sel_resolution.index = self.current_resolution_index
        
        # Recréer la surface de jeu si elle existe
        if self.game_surface is not None:
            self.game_surface = pygame.Surface((self.base_width, self.base_height))
        
        self._update_scaling()
        print(f"[OK] Display: {self.width}x{self.height}, fullscreen={self.is_fullscreen}")

    def _toggle_fullscreen(self):
        """Bascule entre fenêtré et plein écran (F11)."""
        self.is_fullscreen = not self.is_fullscreen
        self._apply_display_mode()
        
        # Mettre à jour le toggle si on est dans les options
        if self.tog_fullscreen:
            self.tog_fullscreen.value = self.is_fullscreen
        
        self._save_display_settings()

    def _apply_display_settings(self):
        """Applique les paramètres d'affichage depuis le menu Options."""
        # Récupérer les nouvelles valeurs
        if self.tog_fullscreen:
            self.is_fullscreen = self.tog_fullscreen.value
        
        if self.sel_resolution:
            new_resolution = self.sel_resolution.get_value()
            if new_resolution:
                self.window_width, self.window_height = new_resolution
                self.current_resolution_index = self.sel_resolution.index
        
        self._apply_display_mode()
        self._save_display_settings()

    def _save_display_settings(self):
        """Sauvegarde les paramètres d'affichage."""
        try:
            data = {}
            if self.save_path.exists():
                with open(self.save_path, "r") as f:
                    data = json.load(f)
            
            # Sauvegarder la résolution de l'index actuel (pas window_width qui peut être la native)
            if 0 <= self.current_resolution_index < len(self.available_resolutions):
                save_w, save_h = self.available_resolutions[self.current_resolution_index]
            else:
                save_w, save_h = self.window_width, self.window_height
            
            data["display"] = {
                "window_width": save_w,
                "window_height": save_h,
                "fullscreen": self.is_fullscreen,
                "resolution_index": self.current_resolution_index,
            }
            
            with open(self.save_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[SAVE] Display settings: {save_w}x{save_h}, fullscreen={self.is_fullscreen}, index={self.current_resolution_index}")
        except Exception as e:
            print(f"[WARN] Could not save display settings: {e}")

    def _load_display_settings(self):
        """Charge les paramètres d'affichage sauvegardés."""
        try:
            if self.save_path.exists():
                with open(self.save_path, "r") as f:
                    data = json.load(f)
                
                display = data.get("display", {})
                if display:
                    self.is_fullscreen = display.get("fullscreen", False)
                    self.current_resolution_index = display.get("resolution_index", 0)
                    
                    # Valider et utiliser l'index pour définir window_width/height
                    if 0 <= self.current_resolution_index < len(self.available_resolutions):
                        self.window_width, self.window_height = self.available_resolutions[self.current_resolution_index]
                    else:
                        # Index invalide, utiliser les valeurs sauvegardées ou défaut
                        self.window_width = display.get("window_width", 800)
                        self.window_height = display.get("window_height", 600)
                        self.current_resolution_index = 0
                    
                    print(f"[LOAD] Display settings: {self.window_width}x{self.window_height}, fullscreen={self.is_fullscreen}, index={self.current_resolution_index}")
        except Exception as e:
            print(f"[WARN] Could not load display settings: {e}")

    def _build_ui(self):
        cx = self.base_width // 2
        cy = self.base_height // 2
        w = 280
        h = 54
        gap = 14

        # Boutons du menu principal avec style égyptien
        self.btn_play = UIMenuButton(pygame.Rect(cx - w // 2, cy - (h + gap) * 1, w, h), "Jouer", self.font)
        self.btn_options = UIMenuButton(pygame.Rect(cx - w // 2, cy, w, h), "Options", self.font)
        self.btn_controls = UIMenuButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 1, w, h), "Commandes", self.font)
        self.btn_quit = UIMenuButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 2, w, h), "Quitter", self.font)

        self.btn_back = UIMenuButton(pygame.Rect(18, 18, 160, 44), "Retour", self.font)

        self.btn_resume = UIButton(pygame.Rect(cx - w // 2, cy - (h + gap) * 1, w, h), "Reprendre", self.font)
        self.btn_restart = UIButton(pygame.Rect(cx - w // 2, cy, w, h), "Recommencer", self.font)
        self.btn_pause_options = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 1, w, h), "Options", self.font)
        self.btn_menu = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 2, w, h), "Menu", self.font)

        # Boutons de sélection de difficulté
        diff_y = cy - 60
        diff_h = 50
        diff_gap = 12
        self.btn_diff_easy = UIMenuButton(pygame.Rect(cx - w // 2, diff_y, w, diff_h), "Facile", self.font)
        self.btn_diff_medium = UIMenuButton(pygame.Rect(cx - w // 2, diff_y + (diff_h + diff_gap), w, diff_h), "Moyen", self.font)
        self.btn_diff_hard = UIMenuButton(pygame.Rect(cx - w // 2, diff_y + (diff_h + diff_gap) * 2, w, diff_h), "Difficile", self.font)
        self.btn_diff_extreme = UIMenuButton(pygame.Rect(cx - w // 2, diff_y + (diff_h + diff_gap) * 3, w, diff_h), "Extreme", self.font)

        ox = cx - 320
        oy = 130
        tw = 640
        th = 54
        tg = 16

        # Options de jeu (3 toggles) - labels courts pour tenir dans le panneau
        self.tog_lanes = UIToggle(pygame.Rect(ox, oy, tw, th), "Lanes", self.font, self.opt_show_lanes)
        self.tog_terrain = UIToggle(pygame.Rect(ox, oy + (th + tg), tw, th), "Terrain", self.font, self.opt_show_terrain)
        self.tog_paths = UIToggle(pygame.Rect(ox, oy + (th + tg) * 2, tw, th), "Chemins", self.font, self.opt_show_paths)

        # Options d'affichage
        self.tog_fullscreen = UIToggle(pygame.Rect(ox, oy, tw, th), "Plein ecran", self.font, self.is_fullscreen)
        self.sel_resolution = UISelector(
            pygame.Rect(ox, oy + (th + tg), tw, th),
            "Resolution",
            self.font,
            self.available_resolutions,
            self.current_resolution_index
        )
        self.btn_apply_display = UIMenuButton(pygame.Rect(cx - 100, oy + (th + tg) * 2 + 20, 200, 50), "Appliquer", self.font)

        # In-game lane buttons (repositionnés sous le nouveau HUD)
        bx = 12
        by = 175  # Sous le panneau de coûts des unités
        bw = 75
        bh = 30
        gap = 8
        self.lane_btn_rects = [
            pygame.Rect(bx + i * (bw + gap), by, bw, bh)
            for i in range(3)
        ]

        # sécurité : on resync
        self._sync_toggle_value(self.tog_lanes, self.opt_show_lanes)
        self._sync_toggle_value(self.tog_terrain, self.opt_show_terrain)
        self._sync_toggle_value(self.tog_paths, self.opt_show_paths)

    # ----------------------------
    # Map loading
    # ----------------------------
    def _load_map_for_visual(self, map_path: Path):
        self.last_map_name = map_path.name
        self.game_map = GridMap(str(map_path))

    # ----------------------------
    # Helpers
    # ----------------------------
    def _clamp(self, v: int, lo: int, hi: int) -> int:
        return lo if v < lo else hi if v > hi else v


    def _selected_lane_index(self) -> int:
        return self._get_selected_lane_index()

    def _snap_new_friendly_units_to_lane_start(self):
        if not self.world or not self.lane_paths or not self.nav_grid:
            return
        if not self.player_pyramid_eid or not self.enemy_pyramid_eid:
            return

        self.world._activate()

        pyramid_ids = {int(self.player_pyramid_eid), int(self.enemy_pyramid_eid)}
        lane_idx = self._get_selected_lane_index()

        # Occupation actuelle (pour éviter stack sur la même case)
        occupied = set()
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if int(ent) in pyramid_ids:
                continue
            if team.id != 1:
                continue
            occupied.add((int(round(t.pos[0])), int(round(t.pos[1]))))

        px, py = int(self.player_pyr_pos[0]), int(self.player_pyr_pos[1])

        candidates = []
        path = self.lane_paths[lane_idx]
        if path:
            start_i = 0
            if (px, py) in path:
                start_i = path.index((px, py)) + 1
            for c in path[start_i:start_i + 10]:
                cx, cy = int(c[0]), int(c[1])
                if (cx, cy) != (px, py):
                    candidates.append((cx, cy))

        if not candidates:
            entry_x = px + 1
            entry_y = int(self.lanes_y[lane_idx]) if self.lanes_y else py
            for dx in range(0, 10):
                candidates.append((entry_x + dx, entry_y))

        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        cleaned = []
        for (cx, cy) in candidates:
            if 1 <= cx < w - 1 and 1 <= cy < h - 1 and self.nav_grid.is_walkable(cx, cy):
                cleaned.append((cx, cy))
        candidates = cleaned

        if not candidates:
            return

        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if int(ent) in pyramid_ids:
                continue
            if team.id != 1:
                continue

            if ent in self._known_units:
                continue

            target = None
            for c in candidates:
                if c not in occupied:
                    target = c
                    break

            if target is None:
                target = candidates[0]

            tx, ty = int(target[0]), int(target[1])

            t.pos = (float(tx), float(ty))

            try:
                gp = esper.component_for_entity(ent, GridPosition)
                gp.x = int(tx)
                gp.y = int(ty)
            except Exception:
                pass

            try:
                p = esper.component_for_entity(ent, PathComponent)
                p.noeuds = []
            except Exception:
                pass

            try:
                prog = esper.component_for_entity(ent, PathProgress)
                prog.index = 0
            except Exception:
                try:
                    esper.add_component(ent, PathProgress(index=0))
                except Exception:
                    pass

            if self.lane_route_system:
                try:
                    self.lane_route_system.set_lane_for_entity(int(ent), int(lane_idx))
                except Exception:
                    pass

            occupied.add((tx, ty))
            self._known_units.add(ent)


    def _flash_lane(self):
        self.lane_flash_timer = float(self.lane_flash_duration)
        idx = self._get_selected_lane_index()
        if self.lane_paths and 0 <= idx < len(self.lane_paths):
            self.lane_preview_path = list(self.lane_paths[idx])
        else:
            self.lane_preview_path = []

    # ----------------------------
    # Match lifecycle
    # ----------------------------
    def _teardown_match(self):
        self.world = None
        self.factory = None

        self.player_pyramid_eid = None
        self.enemy_pyramid_eid = None

        self.input_system = None
        self.economy_system = None
        self.upgrade_system = None
        self.astar_system = None
        self.terrain_system = None
        self.nav_system = None
        self.targeting_system = None
        self.combat_system = None
        self.projectile_system = None
        self.cleanup_system = None
        self.enemy_spawner_system = None
        self.difficulty_system = None


        # ✅ reset enemy systems
        self.difficulty_system = None
        self.enemy_spawner_system = None

        self.match_time = 0.0
        self.enemy_kills = 0
        self._prev_enemy_ids = set()

        self.camera_x = 0.0
        self.camera_y = 0.0

        self.lane_flash_timer = 0.0
        self.lane_preview_path = []
        self.lane_paths = [[], [], []]
        self.lane_paths_enemy = [[], [], []]

        self._known_units = set()

        # ✅ reset lane -> lane2
        self.selected_lane_idx = 1

    def _setup_match(self):
        self.match_index += 1

        # ✅ lane par défaut = lane2
        self.selected_lane_idx = 1

        # 0) seed du match (sert aussi au visuel)
        self.last_map_seed = int(random.randint(1, 2_000_000_000))

        # 1) map visuelle
        maps_dir = self.game_root / "assets" / "map"
        use_generated = (len(self.map_files) == 1 and self.map_files[0].name == "map.tmx")

        if use_generated:
            gen_path = maps_dir / "_generated.tmx"

            gen_w = int(self.balance.get("map", {}).get("width", 30))
            gen_h = int(self.balance.get("map", {}).get("height", 20))
            gen_tw = int(self.balance.get("map", {}).get("tilewidth", 32))
            gen_th = int(self.balance.get("map", {}).get("tileheight", 32))

            dusty_rects_visuel = int(self.balance.get("map", {}).get("dusty_rects", 7))

            _write_generated_tmx(
                gen_path,
                seed=self.last_map_seed,
                width=gen_w,
                height=gen_h,
                tilewidth=gen_tw,
                tileheight=gen_th,
                quicksand_rects=dusty_rects_visuel,
            )

            chosen = gen_path
        else:
            chosen = random.choice(self.map_files)

        self._load_map_for_visual(chosen)

        # 2) nav depuis TMX
        self.nav_grid = self.grid_utils.build_nav_from_map()

        mp = self.balance.get("map", {})

        # 3) positions pyramides d’abord
        def safe_pos(pos):
            x = int(pos[0])
            y = int(pos[1])
            found = self.grid_utils.find_walkable_near(x, y, max_r=12)
            return found if found else (x, y)

        self.player_pyr_pos = safe_pos(mp.get("player_pyramid", (2, 10)))
        self.enemy_pyr_pos = safe_pos(mp.get("enemy_pyramid", (27, 10)))

        # 4) lanes collées à ta pyramide (lane1 haut / lane2 milieu / lane3 bas)
        h = int(getattr(self.nav_grid, "height", 0))
        base_y = int(self.player_pyr_pos[1])

        spacing = 1  # Cases adjacentes à la pyramide

        l2 = self._clamp(base_y, 1, h - 2)
        l1 = self._clamp(base_y - spacing, 1, h - 2)
        l3 = self._clamp(base_y + spacing, 1, h - 2)

        self.lanes_y = [l1, l2, l3]

        # 5) couche random SAÉ
        rng = random.Random(self.last_map_seed + 1337)

        protect = []
        for key in ("player_pyramid", "enemy_pyramid", "player_spawn", "enemy_spawn"):
            if key in mp:
                protect.append(tuple(mp[key]))

        protect.append(tuple(self.player_pyr_pos))
        protect.append(tuple(self.enemy_pyr_pos))

        w = int(getattr(self.nav_grid, "width", 0))
        for ly in self.lanes_y:
            px = int(self.player_pyr_pos[0])
            ex = int(self.enemy_pyr_pos[0])
            entry_p = (self._clamp(px + 1, 1, w - 2), int(ly))
            entry_e = (self._clamp(ex - 1, 1, w - 2), int(ly))
            protect.append(entry_p)
            protect.append(entry_e)

        dusty_div = float(self.balance.get("sae", {}).get("dusty_divisor", 2.0))
        dusty_rects = int(self.balance.get("map", {}).get("dusty_rects", 7))
        forbidden_rects = int(self.balance.get("map", {}).get("forbidden_rects", 3))

        self.last_zone_counts = apply_random_terrain(
            self.nav_grid,
            lanes_y=self.lanes_y,
            protected_positions=protect,
            rng=rng,
            dusty_divisor=dusty_div,
            dusty_rects=dusty_rects,
            forbidden_rects=forbidden_rects,
            corridor_half_height=1,
        )

        # ✅ connectors lanes haut/milieu/bas + cases d’attaque walkable
        self.grid_utils.carve_pyramid_connectors()

        # 6) pré-calcul des 3 lanes (joueur ET ennemi)
        self.pathfinder.recalculate_all_lanes()

        # 7) world propre par match
        self.world = World(name=f"match_{self.match_index}")

        tile_size = int(self.game_map.tilewidth)
        self.factory = EntityFactory(self.world, tile_size=tile_size, balance=self.balance)

        self.player_pyramid_eid = self.factory.create_pyramid(team_id=1, grid_pos=tuple(self.player_pyr_pos))
        self.enemy_pyramid_eid = self.factory.create_pyramid(team_id=2, grid_pos=tuple(self.enemy_pyr_pos))

        # Systems
        from Game.Ecs.Systems.input_system import InputSystem
        from Game.Ecs.Systems.AStarPathfindingSystem import AStarPathfindingSystem
        from Game.Ecs.Systems.TerrainEffectSystem import TerrainEffectSystem
        from Game.Ecs.Systems.NavigationSystem import NavigationSystem
        from Game.Ecs.Systems.TargetingSystem import TargetingSystem
        from Game.Ecs.Systems.CombatSystem import CombatSystem
        from Game.Ecs.Systems.ProjectileSystem import ProjectileSystem
        from Game.Ecs.Systems.CleanupSystem import CleanupSystem
        from Game.Ecs.Systems.EconomySystem import EconomySystem
        from Game.Ecs.Systems.UpgradeSystem import UpgradeSystem
        from Game.Ecs.Systems.RandomEventSystem import RandomEventSystem
        from Game.Ecs.Systems.PyramidDefenseSystem import PyramidDefenseSystem
        from Game.Ecs.Systems.AIBehaviorSystem import AIBehaviorSystem

        self.input_system = InputSystem(
            self.factory,
            self.balance,
            self.player_pyramid_eid,
            self.enemy_pyramid_eid,
            self.nav_grid,
            lanes_y=self.lanes_y,
        )

        # ✅ force lane2 au démarrage même si InputSystem met lane1
        self._set_selected_lane_index(1)

        default_income = float(self.balance.get("pyramid", {}).get("income_base", 2.0))
        self.economy_system = EconomySystem(player_pyramid_eid=self.player_pyramid_eid, default_income=default_income)

        # UpgradeSystem avec les coûts de balance.json
        pyramid_cfg = self.balance.get("pyramid", {})
        upgrade_costs = pyramid_cfg.get("upgrade_costs", [100, 125, 150, 175, 200])
        max_level = int(pyramid_cfg.get("level_max", 5))
        self.upgrade_system = UpgradeSystem(
            player_pyramid_eid=self.player_pyramid_eid,
            max_level=max_level,
            upgrade_costs=upgrade_costs
        )

        self.astar_system = AStarPathfindingSystem(self.nav_grid)
        self.terrain_system = TerrainEffectSystem(self.nav_grid)
        
        # ✅ Paramètres de combat centralisés depuis balance.json
        combat_cfg = self.balance.get("combat", {})
        attack_range = float(combat_cfg.get("attack_range", 2.0))
        align_tolerance = float(combat_cfg.get("align_tolerance", 0.5))
        hit_cooldown = float(combat_cfg.get("hit_cooldown", 0.6))
        projectile_speed = float(combat_cfg.get("projectile_speed", 12.0))
        
        self.nav_system = NavigationSystem(arrive_radius=0.05, attack_range=attack_range, align_tolerance=align_tolerance)

        # objectifs fallback (lane2)
        goal_team1 = self.grid_utils.attack_cell_for_lane(1, 1)  # milieu
        goal_team2 = self.grid_utils.attack_cell_for_lane(2, 1)  # milieu

        goals_by_team = {
            1: GridPosition(int(goal_team1[0]), int(goal_team1[1])),
            2: GridPosition(int(goal_team2[0]), int(goal_team2[1])),
        }

        pyramid_ids = {int(self.player_pyramid_eid), int(self.enemy_pyramid_eid)}

        self.targeting_system = TargetingSystem(
            goals_by_team=goals_by_team,
            pyramid_ids=pyramid_ids,
            attack_range=attack_range
        )

        self.combat_system = CombatSystem(
            attack_range=attack_range,
            hit_cooldown=hit_cooldown,
            projectile_speed=projectile_speed,
            align_tolerance=align_tolerance
        )

        try:
            reward_divisor = float(self.balance.get("sae", {}).get("reward_divisor", 2.0))
            self.projectile_system = ProjectileSystem(
                pyramid_by_team={1: int(self.player_pyramid_eid), 2: int(self.enemy_pyramid_eid)},
                reward_divisor=reward_divisor
            )
        except TypeError:
            self.projectile_system = ProjectileSystem()

        self.cleanup_system = CleanupSystem(protected_entities=pyramid_ids)

        # lane route gameplay - utilise les chemins pré-calculés
        self.lane_route_system = LaneRouteSystem(
            self.lanes_y,
            pyramid_ids=pyramid_ids
        )
        # Passer les chemins pré-calculés
        self.lane_route_system.set_lane_paths(self.lane_paths)

        # ✅ Plus de DifficultySystem dynamique - la difficulté est choisie au menu
        self.difficulty_system = None

        # ✅ EnemySpawnerSystem avec la difficulté choisie
        self.enemy_spawner_system = None
        try:
            self.enemy_spawner_system = EnemySpawnerSystem(
                self.factory,
                self.balance,
                self.player_pyramid_eid,
                self.enemy_pyramid_eid,
                self.nav_grid,
                lanes_y=self.lanes_y,
                difficulty=self.selected_difficulty,
            )
            print(f"[OK] EnemySpawnerSystem created (difficulty: {self.selected_difficulty})")
        except Exception as e:
            print(f"[WARN] EnemySpawnerSystem failed: {e}")
            self.enemy_spawner_system = None

        # ✅ RandomEventSystem pour les événements aléatoires
        try:
            self.random_event_system = RandomEventSystem(
                self.nav_grid,
                self.player_pyramid_eid,
                self.enemy_pyramid_eid,
                on_terrain_change=self.pathfinder.recalculate_all_lanes  # Recalculer les lanes au sandstorm
            )
            print("[OK] RandomEventSystem created")
        except Exception as e:
            print(f"[WARN] RandomEventSystem failed: {e}")
            self.random_event_system = None

        # ✅ PyramidDefenseSystem - les pyramides tirent sur les ennemis
        try:
            pyramid_ids = {self.player_pyramid_eid, self.enemy_pyramid_eid}
            self.pyramid_defense_system = PyramidDefenseSystem(
                pyramid_ids=pyramid_ids,
                attack_range=3.5,  # Portée de défense
                damage=8.0,        # Dégâts par tir
                cooldown=1.0,      # Temps entre tirs
            )
            print("[OK] PyramidDefenseSystem created")
        except Exception as e:
            print(f"[WARN] PyramidDefenseSystem failed: {e}")
            self.pyramid_defense_system = None

        # ✅ AIBehaviorSystem - comportements IA différenciés
        try:
            self.ai_behavior_system = AIBehaviorSystem(
                pyramid_ids={self.player_pyramid_eid, self.enemy_pyramid_eid}
            )
            print("[OK] AIBehaviorSystem created")
        except Exception as e:
            print(f"[WARN] AIBehaviorSystem failed: {e}")
            self.ai_behavior_system = None

        self.world.add_system(self.input_system, priority=10)
        self.world.add_system(self.economy_system, priority=15)
        self.world.add_system(self.upgrade_system, priority=18)

        # ✅ enemy systems assez tôt
        if self.difficulty_system is not None:
            self.world.add_system(self.difficulty_system, priority=19)
        if self.enemy_spawner_system is not None:
            self.world.add_system(self.enemy_spawner_system, priority=21)

        # ✅ RandomEventSystem
        if self.random_event_system is not None:
            self.world.add_system(self.random_event_system, priority=22)

        self.world.add_system(self.astar_system, priority=20)
        self.world.add_system(self.lane_route_system, priority=23)

        self.world.add_system(self.terrain_system, priority=25)
        self.world.add_system(self.nav_system, priority=30)
        self.world.add_system(self.targeting_system, priority=40)
        self.world.add_system(self.combat_system, priority=50)
        
        # ✅ PyramidDefenseSystem après combat
        if self.pyramid_defense_system is not None:
            self.world.add_system(self.pyramid_defense_system, priority=55)
        
        # ✅ AIBehaviorSystem - comportements IA différenciés
        if self.ai_behavior_system is not None:
            self.world.add_system(self.ai_behavior_system, priority=35)  # Entre targeting et combat
        
        self.world.add_system(self.projectile_system, priority=60)
        self.world.add_system(self.cleanup_system, priority=90)

        self.camera_x = 0.0
        self.camera_y = 0.0
        self.match_time = 0.0
        self.enemy_kills = 0
        self._prev_enemy_ids = set()
        self.game_over_text = ""

        self._known_units = set()

        # ✅ preview au spawn (lane2)
        self._flash_lane()

    # ----------------------------
    # Draw helpers
    # ----------------------------
    def _handle_hud_click(self, mx: int, my: int) -> bool:
        """Gère les clics sur les boutons HUD (unités et upgrade)."""
        # Vérifier clic sur boutons d'unités
        for unit_key, rect in self.unit_btn_rects.items():
            if rect and rect.collidepoint(mx, my):
                # Spawn l'unité correspondante via input_system
                if self.input_system and hasattr(self.input_system, '_spawn_unit_player'):
                    self.input_system._spawn_unit_player(unit_key)
                    return True
        
        # Vérifier clic sur bouton upgrade
        if self.upgrade_btn_rect and self.upgrade_btn_rect.collidepoint(mx, my):
            if self.upgrade_system and hasattr(self.upgrade_system, 'request_upgrade'):
                self.upgrade_system.request_upgrade()
                return True
        
        return False

    def _handle_lane_selector_click(self, mx: int, my: int) -> bool:
        # Gérer aussi les clics HUD
        if self._handle_hud_click(mx, my):
            return True
        
        for i, r in enumerate(self.lane_btn_rects):
            if r.collidepoint(mx, my):
                self._set_selected_lane_index(i)
                self._flash_lane()
                return True
        return False

    def _open_options(self):
        self.state_return = self.state
        self.state = "options"
        self._sync_toggle_value(self.tog_lanes, self.opt_show_lanes)
        self._sync_toggle_value(self.tog_terrain, self.opt_show_terrain)
        self._sync_toggle_value(self.tog_paths, self.opt_show_paths)

    def _open_controls(self):
        self.state_return = self.state
        self.state = "controls"

    def _return_from_submenu(self):
        self.state = self.state_return if self.state_return else "menu"

    def _start_game_with_difficulty(self):
        """Démarre une partie avec la difficulté sélectionnée."""
        self._teardown_match()
        self._setup_match()
        self.state = "playing"

    # ----------------------------
    # Stats
    # ----------------------------
    def _update_kills_tracker(self):
        if self.world:
            self.world._activate()

        current = set()
        for ent, (team,) in esper.get_components(Team):
            if ent in (self.player_pyramid_eid, self.enemy_pyramid_eid):
                continue
            if team.id == 2:
                current.add(ent)

        if self._prev_enemy_ids:
            dead = self._prev_enemy_ids - current
            if dead:
                self.enemy_kills += len(dead)

        self._prev_enemy_ids = current

    def _play_sound(self, sound_name: str):
        """Joue un son via le sound_manager."""
        try:
            from Game.Audio.sound_manager import sound_manager
            sound_manager.play(sound_name)
        except:
            pass

    def _check_record(self):
        updated = False
        if self.match_time > self.best_time:
            self.best_time = float(self.match_time)
            updated = True
        if self.enemy_kills > self.best_kills:
            self.best_kills = int(self.enemy_kills)
            updated = True
        if updated:
            self._save_save()

    # ----------------------------
    # Main loop
    # ----------------------------
    def run(self):
        self.boot()
        self.running = True

        while self.running:
            dt = self.clock.tick()

            if self.lane_flash_timer > 0.0:
                self.lane_flash_timer -= float(dt)
                if self.lane_flash_timer < 0.0:
                    self.lane_flash_timer = 0.0

            for event in pygame.event.get():
                # Convertir les coordonnées souris pour le scaling
                if hasattr(event, 'pos'):
                    screen_x, screen_y = event.pos
                    game_x, game_y = self._screen_to_game_coords(screen_x, screen_y)
                    # Créer un nouvel événement avec les coordonnées converties
                    event = pygame.event.Event(event.type, {
                        **{attr: getattr(event, attr) for attr in ['button', 'buttons', 'rel', 'touch'] if hasattr(event, attr)},
                        'pos': (game_x, game_y)
                    })
                
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Gestion du redimensionnement de fenêtre (mode fenêtré uniquement)
                if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.window_width, self.window_height = event.w, event.h
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self._update_scaling()

                if event.type == pygame.KEYDOWN:
                    if self.state in ("options", "controls") and event.key == pygame.K_ESCAPE:
                        self._return_from_submenu()
                    
                    # F11 pour basculer plein écran
                    if event.key == pygame.K_F11:
                        self._toggle_fullscreen()

                # MENU
                if self.state == "menu":
                    if self.btn_play.handle_event(event):
                        self.state = "difficulty_select"

                    if self.btn_options.handle_event(event):
                        self._open_options()

                    if self.btn_controls.handle_event(event):
                        self._open_controls()

                    if self.btn_quit.handle_event(event):
                        self.running = False

                # DIFFICULTY SELECT
                elif self.state == "difficulty_select":
                    if self.btn_back.handle_event(event):
                        self.state = "menu"
                    
                    if self.btn_diff_easy.handle_event(event):
                        self.selected_difficulty = "easy"
                        self._start_game_with_difficulty()
                    
                    if self.btn_diff_medium.handle_event(event):
                        self.selected_difficulty = "medium"
                        self._start_game_with_difficulty()
                    
                    if self.btn_diff_hard.handle_event(event):
                        self.selected_difficulty = "hard"
                        self._start_game_with_difficulty()
                    
                    if self.btn_diff_extreme.handle_event(event):
                        self.selected_difficulty = "extreme"
                        self._start_game_with_difficulty()

                # OPTIONS
                elif self.state == "options":
                    if self.btn_back.handle_event(event):
                        self._return_from_submenu()

                    if self.tog_lanes.handle_event(event):
                        self.opt_show_lanes = self.tog_lanes.value
                    if self.tog_terrain.handle_event(event):
                        self.opt_show_terrain = self.tog_terrain.value
                    if self.tog_paths.handle_event(event):
                        self.opt_show_paths = self.tog_paths.value
                    
                    # Options d'affichage
                    self.tog_fullscreen.handle_event(event)
                    self.sel_resolution.handle_event(event)
                    if self.btn_apply_display.handle_event(event):
                        self._apply_display_settings()

                # CONTROLS
                elif self.state == "controls":
                    if self.btn_back.handle_event(event):
                        self._return_from_submenu()

                # PLAYING
                elif self.state == "playing":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        self._handle_lane_selector_click(mx, my)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "pause"

                        # sélection lane au clavier => preview
                        if event.key in (pygame.K_z, pygame.K_w):
                            self._set_selected_lane_index(0)
                            self._flash_lane()
                        elif event.key == pygame.K_x:
                            self._set_selected_lane_index(1)
                            self._flash_lane()
                        elif event.key == pygame.K_c:
                            self._set_selected_lane_index(2)
                            self._flash_lane()

                        if event.key == pygame.K_u and self.upgrade_system:
                            self.upgrade_system.request_upgrade()

                # PAUSE
                elif self.state == "pause":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = "playing"

                    if self.btn_resume.handle_event(event):
                        self.state = "playing"

                    if self.btn_restart.handle_event(event):
                        self._teardown_match()
                        self._setup_match()
                        self.state = "playing"

                    if self.btn_pause_options.handle_event(event):
                        self._open_options()

                    if self.btn_menu.handle_event(event):
                        self._teardown_match()
                        self.state = "menu"

                # GAME OVER
                elif self.state == "game_over":
                    if self.btn_restart.handle_event(event):
                        self._teardown_match()
                        self._setup_match()
                        self.state = "playing"

                    if self.btn_menu.handle_event(event):
                        self._teardown_match()
                        self.state = "menu"

            # UPDATE
            if self.state == "playing" and self.world:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.camera_x -= 200 * dt
                if keys[pygame.K_RIGHT]:
                    self.camera_x += 200 * dt
                if keys[pygame.K_UP]:
                    self.camera_y -= 200 * dt
                if keys[pygame.K_DOWN]:
                    self.camera_y += 200 * dt

                self.match_time += dt
                self.world.process(dt)

                self._snap_new_friendly_units_to_lane_start()
                self._update_kills_tracker()

                if esper.component_for_entity(self.enemy_pyramid_eid, Health).is_dead:
                    self.state = "game_over"
                    self.game_over_text = "VICTORY"
                    self._play_sound("victory")
                    self._check_record()
                elif esper.component_for_entity(self.player_pyramid_eid, Health).is_dead:
                    self.state = "game_over"
                    self.game_over_text = "DEFEAT"
                    self._play_sound("defeat")
                    self._check_record()

            # DRAW
            # Sauvegarder l'écran réel et rendre sur game_surface
            real_screen = self.screen
            self.screen = self.game_surface
            
            self.screen.fill((18, 18, 22))

            if self.game_map:
                self.game_map.draw(self.screen, int(self.camera_x), int(self.camera_y))

            if self.state in ("playing", "pause", "game_over") and self.world:
                self.renderer.draw_lane_preview_path()

                # Afficher les lanes (avant le terrain pour mieux voir)
                if self.opt_show_lanes:
                    self.renderer.draw_lane_paths_all()

                if self.opt_show_terrain:
                    self.renderer.draw_terrain_overlay()

                self.renderer.draw_entities()
                
                # Afficher les chemins des unités (par-dessus les entités)
                if self.opt_show_paths:
                    self.renderer.debug_draw_paths()
                
                # Ne pas dessiner le HUD en pause ou game_over
                if self.state not in ("pause", "game_over"):
                    self.renderer.draw_hud_minimal()
                    # Minimap en bas à droite
                    self.renderer.draw_minimap()

            if self.state == "menu":
                self.renderer.draw_menu()

            elif self.state == "difficulty_select":
                self.renderer.draw_difficulty_select()

            elif self.state == "options":
                self.renderer.draw_options()

            elif self.state == "controls":
                self.renderer.draw_controls()

            elif self.state == "pause":
                self.renderer.draw_pause()

            elif self.state == "game_over":
                self.renderer.draw_game_over()

            # Restaurer l'écran réel et afficher le résultat scalé
            self.screen = real_screen
            self._render_to_screen()

        self.shutdown()


def main():
    GameApp().run()


if __name__ == "__main__":
    main()
