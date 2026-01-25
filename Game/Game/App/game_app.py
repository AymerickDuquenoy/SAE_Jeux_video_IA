# Game/App/game_app.py
import json
import random
import pygame
import esper
from pathlib import Path
import xml.etree.ElementTree as ET
import heapq

from Game.Ecs.world import World
from Game.Services.clock import GameClock
from Game.Services.event_bus import EventBus
from Game.Services.GridMap import GridMap
from Game.Services.balance_config import BalanceConfig
from Game.Factory.entity_factory import EntityFactory

from Game.Services.NavigationGrid import NavigationGrid
from Game.Services.GridTile import GridTile

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
from Game.Ecs.Systems.DifficultySystem import DifficultySystem

from Game.Ecs.Systems.LaneRouteSystem import LaneRouteSystem
from Game.Services.terrain_randomizer import apply_random_terrain


# UI : si tu as déjà Game/App/ui.py, il sera pris
try:
    from Game.App.ui import UIButton, UIToggle
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
    def __init__(self, width: int = 960, height: int = 640, title: str = "Antique War"):
        self.width = width
        self.height = height
        self.title = title

        self.screen = None
        self.running = False

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

        self.camera_x = 0.0
        self.camera_y = 0.0

        # UI / state machine
        self.state = "menu"  # menu/options/controls/playing/pause/game_over
        self.state_return = "menu"
        self.game_over_text = ""

        # options (OFF par défaut)
        self.opt_show_lanes = False
        self.opt_show_terrain = False
        self.opt_show_nav = False
        self.opt_show_paths = False
        self.opt_show_advhud = False

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
        self.lane_paths = [[], [], []]

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

        # toggles
        self.tog_lanes = None
        self.tog_terrain = None
        self.tog_nav = None
        self.tog_paths = None
        self.tog_advhud = None

        # lane selector HUD
        self.lane_btn_rects = []

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
        self.screen = pygame.display.set_mode((self.width, self.height))

        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_big = pygame.font.SysFont("consolas", 42)

        self._load_save()

        balance_file = self.game_root / "assets" / "config" / "balance.json"
        self.balance = BalanceConfig.load(str(balance_file)).data

        maps_dir = self.game_root / "assets" / "map"
        self.map_files = sorted(maps_dir.glob("map_*.tmx"))
        if not self.map_files:
            self.map_files = [maps_dir / "map.tmx"]

        # charge une map pour l’écran menu (juste visuel)
        self._load_map_for_visual(random.choice(self.map_files))

        # ✅ sécurité : options OFF au boot (au cas où ui.py a un comportement bizarre)
        self.opt_show_lanes = False
        self.opt_show_terrain = False
        self.opt_show_nav = False
        self.opt_show_paths = False
        self.opt_show_advhud = False

        # ✅ lane par défaut = 2 au boot
        self.selected_lane_idx = 1

        self._build_ui()

    def shutdown(self):
        pygame.quit()

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

    def _build_ui(self):
        cx = self.width // 2
        cy = self.height // 2
        w = 280
        h = 54
        gap = 14

        self.btn_play = UIButton(pygame.Rect(cx - w // 2, cy - (h + gap) * 1, w, h), "Jouer", self.font)
        self.btn_options = UIButton(pygame.Rect(cx - w // 2, cy, w, h), "Options", self.font)
        self.btn_controls = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 1, w, h), "Commandes", self.font)
        self.btn_quit = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 2, w, h), "Quitter", self.font)

        self.btn_back = UIButton(pygame.Rect(18, 18, 160, 44), "Retour", self.font)

        self.btn_resume = UIButton(pygame.Rect(cx - w // 2, cy - (h + gap) * 1, w, h), "Reprendre", self.font)
        self.btn_restart = UIButton(pygame.Rect(cx - w // 2, cy, w, h), "Recommencer", self.font)
        self.btn_pause_options = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 1, w, h), "Options", self.font)
        self.btn_menu = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 2, w, h), "Menu", self.font)

        ox = cx - 320
        oy = 130
        tw = 640
        th = 54
        tg = 16

        self.tog_lanes = UIToggle(pygame.Rect(ox, oy + (th + tg) * 0, tw, th), "Afficher les lanes", self.font, self.opt_show_lanes)
        self.tog_terrain = UIToggle(pygame.Rect(ox, oy + (th + tg) * 1, tw, th), "Afficher terrain (open/dusty/interdit)", self.font, self.opt_show_terrain)
        self.tog_nav = UIToggle(pygame.Rect(ox, oy + (th + tg) * 2, tw, th), "Debug nav (zones interdites)", self.font, self.opt_show_nav)
        self.tog_paths = UIToggle(pygame.Rect(ox, oy + (th + tg) * 3, tw, th), "Debug paths (chemins)", self.font, self.opt_show_paths)
        self.tog_advhud = UIToggle(pygame.Rect(ox, oy + (th + tg) * 4, tw, th), "HUD avancée", self.font, self.opt_show_advhud)

        # In-game lane buttons
        bx = 22
        by = 90
        bw = 92
        bh = 26
        gap = 10
        self.lane_btn_rects = [
            pygame.Rect(bx + i * (bw + gap), by, bw, bh)
            for i in range(3)
        ]

        # sécurité : on resync (au cas où ton ui.py gère différemment)
        self._sync_toggle_value(self.tog_lanes, self.opt_show_lanes)
        self._sync_toggle_value(self.tog_terrain, self.opt_show_terrain)
        self._sync_toggle_value(self.tog_nav, self.opt_show_nav)
        self._sync_toggle_value(self.tog_paths, self.opt_show_paths)
        self._sync_toggle_value(self.tog_advhud, self.opt_show_advhud)

    # ----------------------------
    # Map loading
    # ----------------------------
    def _load_map_for_visual(self, map_path: Path):
        self.last_map_name = map_path.name
        self.game_map = GridMap(str(map_path))

    def _build_nav_from_map(self) -> NavigationGrid:
        nav = NavigationGrid(int(self.game_map.width), int(self.game_map.height))
        vmax = float(getattr(GridTile, "VITESSE_MAX", 10.0))

        for t in getattr(self.game_map, "tiles", []):
            speed = float(getattr(t, "speed", vmax))
            walkable = bool(getattr(t, "walkable", True))
            mult = 0.0 if speed <= 0 else max(0.0, min(1.0, speed / vmax))
            nav.set_cell(int(t.x), int(t.y), walkable=walkable, mult=mult)

        # bordure interdite (zone vitesse=0)
        w = int(getattr(nav, "width", 0))
        h = int(getattr(nav, "height", 0))
        if w > 0 and h > 0:
            for x in range(w):
                nav.set_cell(x, 0, walkable=False, mult=0.0)
                nav.set_cell(x, h - 1, walkable=False, mult=0.0)
            for y in range(h):
                nav.set_cell(0, y, walkable=False, mult=0.0)
                nav.set_cell(w - 1, y, walkable=False, mult=0.0)

        return nav

    # ----------------------------
    # Helpers
    # ----------------------------
    def _clamp(self, v: int, lo: int, hi: int) -> int:
        return lo if v < lo else hi if v > hi else v

    def _find_walkable_near(self, x: int, y: int, max_r: int = 10):
        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        for r in range(0, max_r + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        if self.nav_grid.is_walkable(nx, ny):
                            return nx, ny
        return None

    def _force_open_cell(self, x: int, y: int, mult: float = 1.0):
        """Force une case walkable/open (utile après apply_random_terrain)."""
        try:
            self.nav_grid.set_cell(int(x), int(y), walkable=True, mult=float(mult))
            return
        except Exception:
            pass

        # fallback si jamais set_cell n'existe pas
        try:
            self.nav_grid.walkable[int(y)][int(x)] = True
        except Exception:
            pass
        try:
            self.nav_grid.mult[int(y)][int(x)] = float(mult)
        except Exception:
            pass

    def _attack_cell_for_lane(self, team_id: int, lane_idx: int) -> tuple[int, int]:
        """
        Case d'attaque alignée avec la lane.
        Utilise lanes_y pour garantir l'alignement correct.
        """
        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        px, py = int(self.player_pyr_pos[0]), int(self.player_pyr_pos[1])
        ex, ey = int(self.enemy_pyr_pos[0]), int(self.enemy_pyr_pos[1])
        
        # Utiliser lanes_y pour l'alignement Y
        lane_y = int(self.lanes_y[lane_idx])

        if team_id == 1:
            # Joueur attaque pyramide ennemie (à droite)
            if lane_idx == 1:
                ax, ay = ex - 1, lane_y
            else:
                ax, ay = ex, lane_y
        else:
            # Ennemi attaque pyramide joueur (à gauche)
            if lane_idx == 1:
                ax, ay = px + 1, lane_y
            else:
                ax, ay = px, lane_y

        ax = max(1, min(w - 2, int(ax)))
        ay = max(1, min(h - 2, int(ay)))
        return (ax, ay)

    def _carve_pyramid_connectors(self):
        """
        ✅ Assure que les 3 lanes peuvent rejoindre des cases d'attaque différentes
        - lane1 : haut
        - lane2 : milieu
        - lane3 : bas
        """
        if not self.nav_grid:
            return

        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return

        px, py = int(self.player_pyr_pos[0]), int(self.player_pyr_pos[1])
        ex, ey = int(self.enemy_pyr_pos[0]), int(self.enemy_pyr_pos[1])

        # colonnes "couloir"
        col_player = max(1, min(w - 2, px + 1))
        col_enemy = max(1, min(w - 2, ex - 1))

        ymin = max(1, min(self.lanes_y + [py, ey]))
        ymax = min(h - 2, max(self.lanes_y + [py, ey]))

        # couloir vertical près des pyramides
        for y in range(ymin, ymax + 1):
            self._force_open_cell(col_player, y, 1.0)
            self._force_open_cell(col_enemy, y, 1.0)

        # entrées lanes (sur les couloirs)
        for ly in self.lanes_y:
            self._force_open_cell(col_player, int(ly), 1.0)
            self._force_open_cell(col_enemy, int(ly), 1.0)

        # ✅ cases d'attaque lane (haut/milieu/bas) -> forcées walkable
        for lane_idx in (0, 1, 2):
            ax1, ay1 = self._attack_cell_for_lane(1, lane_idx)
            ax2, ay2 = self._attack_cell_for_lane(2, lane_idx)
            self._force_open_cell(ax1, ay1, 1.0)
            self._force_open_cell(ax2, ay2, 1.0)

        # petit pad autour pyramides (anti blocage)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            x1 = max(1, min(w - 2, px + dx))
            y1 = max(1, min(h - 2, py + dy))
            self._force_open_cell(x1, y1, 1.0)

            x2 = max(1, min(w - 2, ex + dx))
            y2 = max(1, min(h - 2, ey + dy))
            self._force_open_cell(x2, y2, 1.0)

        # ✅ mini-connecteurs autour de la pyramide ennemie pour lane1/lane3 (haut/bas)
        for (xx, yy) in (
            (ex - 1, ey - 1),
            (ex - 1, ey + 1),
            (ex, ey - 1),
            (ex, ey + 1),
        ):
            if 1 <= xx < w - 1 and 1 <= yy < h - 1:
                self._force_open_cell(xx, yy, 1.0)

        # ✅ mini-connecteurs autour de la pyramide joueur
        for (xx, yy) in (
            (px + 1, py - 1),
            (px + 1, py + 1),
            (px, py - 1),
            (px, py + 1),
        ):
            if 1 <= xx < w - 1 and 1 <= yy < h - 1:
                self._force_open_cell(xx, yy, 1.0)

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

    # ----------------------------
    # A* preview (même coût que ta nav mult)
    # ----------------------------
    def _cell_cost(self, x: int, y: int) -> float:
        try:
            m = float(self.nav_grid.mult[y][x])
        except Exception:
            m = 1.0
        if m <= 0.0:
            return 999999.0
        return 1.0 / max(0.05, m)

    def _astar_preview(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        if not self.nav_grid:
            return []
        if start == goal:
            return [start]

        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return []

        sx, sy = start
        gx, gy = goal
        if not self.nav_grid.is_walkable(sx, sy):
            return []
        if not self.nav_grid.is_walkable(gx, gy):
            return []

        def h_manh(a: tuple[int, int], b: tuple[int, int]) -> float:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_heap = []
        heapq.heappush(open_heap, (0.0, 0.0, (sx, sy)))

        came = {}
        gscore = {(sx, sy): 0.0}
        closed = set()

        while open_heap:
            _f, g, cur = heapq.heappop(open_heap)
            if cur in closed:
                continue

            if cur == (gx, gy):
                out = [cur]
                while cur in came:
                    cur = came[cur]
                    out.append(cur)
                out.reverse()
                return out

            closed.add(cur)
            cx, cy = cur

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = cx + dx
                ny = cy + dy
                if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
                    continue
                if not self.nav_grid.is_walkable(nx, ny):
                    continue

                ng = g + self._cell_cost(nx, ny)
                if (nx, ny) not in gscore or ng < gscore[(nx, ny)]:
                    gscore[(nx, ny)] = ng
                    came[(nx, ny)] = (cx, cy)
                    nf = ng + h_manh((nx, ny), (gx, gy))
                    heapq.heappush(open_heap, (nf, ng, (nx, ny)))

        return []

    def _compute_lane_route_path(self, lane_idx: int) -> list[tuple[int, int]]:
        """
        Lane réelle = chemin complet :
        ANCRE (haut/droite/bas de la pyramide) -> entrée lane -> sortie lane -> case d'attaque lane (haut/milieu/bas)

        Objectif : la ligne part "collée" à la pyramide :
        - lane 1 : haut de la pyramide
        - lane 2 : droite de la pyramide
        - lane 3 : bas de la pyramide
        """
        if not self.nav_grid:
            return []

        lane_idx = max(0, min(2, int(lane_idx)))
        lane_y = int(self.lanes_y[lane_idx])

        px = int(self.player_pyr_pos[0])
        py = int(self.player_pyr_pos[1])
        ex = int(self.enemy_pyr_pos[0])

        h = int(getattr(self.nav_grid, "height", 0))
        w = int(getattr(self.nav_grid, "width", 0))

        def clamp_xy(x: int, y: int) -> tuple[int, int]:
            if w > 0:
                x = self._clamp(x, 0, w - 1)
            if h > 0:
                y = self._clamp(y, 0, h - 1)
            return (x, y)

        # ✅ ancre de départ "collée" à la pyramide (selon lane)
        if lane_idx == 0:
            start_raw = (px, py - 1)      # haut
        elif lane_idx == 1:
            start_raw = (px + 1, py)      # droite
        else:
            start_raw = (px, py + 1)      # bas

        start_raw = clamp_xy(int(start_raw[0]), int(start_raw[1]))

        # entrée lane = à droite de ta base, sur la lane sélectionnée
        entry_raw = (px + 1, lane_y)
        entry_raw = clamp_xy(int(entry_raw[0]), int(entry_raw[1]))

        # milieu proche ennemi sur la lane
        mid_raw = (ex - 1, lane_y)
        mid_raw = clamp_xy(int(mid_raw[0]), int(mid_raw[1]))

        # fin = case d'attaque lane (haut/milieu/bas)
        end_raw = self._attack_cell_for_lane(1, lane_idx)
        end_raw = clamp_xy(int(end_raw[0]), int(end_raw[1]))

        s = self._find_walkable_near(int(start_raw[0]), int(start_raw[1]), max_r=12)
        e = self._find_walkable_near(int(entry_raw[0]), int(entry_raw[1]), max_r=12)
        m = self._find_walkable_near(int(mid_raw[0]), int(mid_raw[1]), max_r=12)
        g = self._find_walkable_near(int(end_raw[0]), int(end_raw[1]), max_r=12)

        if not s or not e or not m or not g:
            return []

        p1 = self._astar_preview(s, e)
        p2 = self._astar_preview(e, m)
        p3 = self._astar_preview(m, g)

        out = []
        if p1:
            out += p1
        if p2:
            out += p2[1:] if out else p2
        if p3:
            out += p3[1:] if out else p3

        if out:
            if tuple(out[0]) != tuple(start_raw):
                out.insert(0, start_raw)
        else:
            out = [start_raw]

        return out

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
        self.nav_grid = self._build_nav_from_map()

        mp = self.balance.get("map", {})

        # 3) positions pyramides d’abord
        def safe_pos(pos):
            x = int(pos[0])
            y = int(pos[1])
            found = self._find_walkable_near(x, y, max_r=12)
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
        self._carve_pyramid_connectors()

        # 6) pré-calcul des 3 lanes réelles
        self.lane_paths = [
            self._compute_lane_route_path(0),
            self._compute_lane_route_path(1),
            self._compute_lane_route_path(2),
        ]

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

        upgrade_costs = self.balance.get("pyramid", {}).get("upgrade_costs", [100.0])
        base_upgrade_cost = float(upgrade_costs[0]) if isinstance(upgrade_costs, list) and len(upgrade_costs) else 100.0
        self.upgrade_system = UpgradeSystem(player_pyramid_eid=self.player_pyramid_eid, base_cost=base_upgrade_cost)

        self.astar_system = AStarPathfindingSystem(self.nav_grid)
        self.terrain_system = TerrainEffectSystem(self.nav_grid)
        self.nav_system = NavigationSystem(arrive_radius=0.05)

        # objectifs fallback (lane2)
        goal_team1 = self._attack_cell_for_lane(1, 1)  # milieu
        goal_team2 = self._attack_cell_for_lane(2, 1)  # milieu

        goals_by_team = {
            1: GridPosition(int(goal_team1[0]), int(goal_team1[1])),
            2: GridPosition(int(goal_team2[0]), int(goal_team2[1])),
        }

        pyramid_ids = {int(self.player_pyramid_eid), int(self.enemy_pyramid_eid)}

        attack_range = 1.8  # ✅ FIX: Plus de marge pour la portée

        self.targeting_system = TargetingSystem(
            goals_by_team=goals_by_team,
            pyramid_ids=pyramid_ids,
            attack_range=attack_range
        )

        self.combat_system = CombatSystem(
            attack_range=attack_range,
            hit_cooldown=0.7,
            projectile_speed=10.0
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

        # lane route gameplay
        self.lane_route_system = LaneRouteSystem(
            self.nav_grid,
            self.lanes_y,
            self.player_pyr_pos,
            self.enemy_pyr_pos,
            pyramid_ids=pyramid_ids
        )

        # ✅ DIFFICULTY + ENEMY SPAWNER
        try:
            self.difficulty_system = DifficultySystem(self.balance)
        except TypeError:
            try:
                self.difficulty_system = DifficultySystem()
            except Exception:
                self.difficulty_system = None

        # ✅ FIX: Créer EnemySpawnerSystem TOUJOURS (indépendamment de difficulty)
        self.enemy_spawner_system = None
        try:
            self.enemy_spawner_system = EnemySpawnerSystem(
                self.factory,
                self.balance,
                self.player_pyramid_eid,
                self.enemy_pyramid_eid,
                self.nav_grid,
                lanes_y=self.lanes_y,
            )
            print("[OK] EnemySpawnerSystem created")
        except Exception as e:
            print(f"[WARN] EnemySpawnerSystem failed: {e}")
            self.enemy_spawner_system = None

        # ✅ RandomEventSystem pour les événements aléatoires
        try:
            self.random_event_system = RandomEventSystem(
                self.nav_grid,
                self.player_pyramid_eid,
                self.enemy_pyramid_eid
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
    def _grid_to_screen(self, gx: float, gy: float):
        tw = int(self.game_map.tilewidth)
        th = int(self.game_map.tileheight)
        px = (gx + 0.5) * tw
        py = (gy + 0.5) * th
        return int(px - self.camera_x), int(py - self.camera_y)

    def _draw_panel(self, x: int, y: int, w: int, h: int, alpha: int = 120):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        self.screen.blit(s, (x, y))

    def _draw_center_overlay(self, title: str, subtitle: str = ""):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        surf = self.font_big.render(title, True, (255, 255, 255))
        rect = surf.get_rect(center=(self.width // 2, self.height // 2 - 140))
        self.screen.blit(surf, rect)

        if subtitle:
            sub = self.font.render(subtitle, True, (230, 230, 230))
            sr = sub.get_rect(center=(self.width // 2, self.height // 2 - 95))
            self.screen.blit(sub, sr)

    def _draw_lane_paths_all(self):
        if not self.lane_paths:
            return

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        for path in self.lane_paths:
            if not path or len(path) < 2:
                continue

            pts = [self._grid_to_screen(x, y) for (x, y) in path]
            pygame.draw.lines(overlay, (240, 240, 240, 28), False, pts, 3)

        self.screen.blit(overlay, (0, 0))

    def _draw_lane_preview_path(self):
        if self.lane_flash_timer <= 0.0:
            return
        if not self.lane_preview_path or len(self.lane_preview_path) < 2:
            return

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pts = [self._grid_to_screen(x, y) for (x, y) in self.lane_preview_path]

        pygame.draw.lines(overlay, (240, 240, 240, 210), False, pts, 4)

        for p in pts[::2]:
            pygame.draw.circle(overlay, (240, 240, 240, 200), p, 3, 1)

        self.screen.blit(overlay, (0, 0))

    def _draw_terrain_overlay(self):
        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return

        tw = int(self.game_map.tilewidth)
        th = int(self.game_map.tileheight)

        for y in range(h):
            for x in range(w):
                walk = self.nav_grid.is_walkable(x, y)
                m = float(self.nav_grid.mult[y][x])

                if (not walk) or m <= 0.0:
                    color = (220, 50, 50, 70)
                elif m < 0.99:
                    color = (170, 120, 70, 60)
                else:
                    continue

                sx, sy = self._grid_to_screen(float(x), float(y))
                rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                s = pygame.Surface((tw, th), pygame.SRCALPHA)
                s.fill(color)
                self.screen.blit(s, rect.topleft)

    def _debug_draw_forbidden(self):
        w = int(getattr(self.nav_grid, "width", 0))
        h = int(getattr(self.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return

        tw = int(self.game_map.tilewidth)
        th = int(self.game_map.tileheight)

        for y in range(h):
            for x in range(w):
                walk = self.nav_grid.is_walkable(x, y)
                m = float(self.nav_grid.mult[y][x])
                if (not walk) or m <= 0:
                    sx, sy = self._grid_to_screen(float(x), float(y))
                    rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                    pygame.draw.rect(self.screen, (220, 50, 50), rect, 1)

    def _debug_draw_paths(self):
        if self.world:
            self.world._activate()

        for ent, (t, path) in esper.get_components(Transform, PathComponent):
            if not path.noeuds:
                continue

            pts = [self._grid_to_screen(n.x, n.y) for n in path.noeuds]
            if len(pts) >= 2:
                pygame.draw.lines(self.screen, (30, 30, 30), False, pts, 2)

    def _draw_entities(self):
        from Game.App.sprite_renderer import sprite_renderer
        
        if self.world:
            self.world._activate()

        # Dessiner les pyramides
        for eid in (self.player_pyramid_eid, self.enemy_pyramid_eid):
            t = esper.component_for_entity(eid, Transform)
            team = esper.component_for_entity(eid, Team)
            h = esper.component_for_entity(eid, Health)

            sx, sy = self._grid_to_screen(t.pos[0], t.pos[1])
            ratio = 0.0 if h.hp_max <= 0 else max(0.0, min(1.0, h.hp / h.hp_max))
            
            # Niveau de la pyramide
            level = 1
            if esper.has_component(eid, PyramidLevel):
                level = esper.component_for_entity(eid, PyramidLevel).level
            
            sprite_renderer.draw_pyramid(self.screen, sx, sy, team.id, ratio, level)

        # Dessiner les unités
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if ent in (self.player_pyramid_eid, self.enemy_pyramid_eid):
                continue

            # Vérifier si mort
            if esper.has_component(ent, Health):
                hp = esper.component_for_entity(ent, Health)
                if hp.is_dead:
                    continue
                ratio = max(0.0, min(1.0, hp.hp / hp.hp_max))
            else:
                ratio = 1.0

            sx, sy = self._grid_to_screen(t.pos[0], t.pos[1])
            
            # Vérifier si l'unité bouge
            is_moving = False
            if esper.has_component(ent, Velocity):
                vel = esper.component_for_entity(ent, Velocity)
                if abs(vel.vx) > 0.01 or abs(vel.vy) > 0.01:
                    is_moving = True
            
            # Type d'unité basé sur la puissance
            power = getattr(stats, 'power', 0)
            if power <= 9:
                sprite_renderer.draw_momie(self.screen, sx, sy, team.id, ratio, is_moving)
            elif power <= 14:
                sprite_renderer.draw_dromadaire(self.screen, sx, sy, team.id, ratio, is_moving)
            else:
                sprite_renderer.draw_sphinx(self.screen, sx, sy, team.id, ratio, is_moving)

        # Dessiner les projectiles
        for ent, (t, p) in esper.get_components(Transform, Projectile):
            sx, sy = self._grid_to_screen(t.pos[0], t.pos[1])
            sprite_renderer.draw_projectile(self.screen, sx, sy, p.team_id)

    def _draw_lane_selector(self):
        selected = self._get_selected_lane_index()

        for i, r in enumerate(self.lane_btn_rects):
            active = (i == selected)

            bg = (60, 200, 120) if active else (35, 35, 40)
            border = (240, 240, 240) if active else (80, 80, 90)
            txt_col = (18, 18, 22) if active else (240, 240, 240)

            pygame.draw.rect(self.screen, bg, r, border_radius=10)
            pygame.draw.rect(self.screen, border, r, width=2, border_radius=10)

            s = self.font_small.render(f"Lane {i+1}", True, txt_col)
            tr = s.get_rect(center=r.center)
            self.screen.blit(s, tr)

    def _handle_lane_selector_click(self, mx: int, my: int) -> bool:
        for i, r in enumerate(self.lane_btn_rects):
            if r.collidepoint(mx, my):
                self._set_selected_lane_index(i)
                self._flash_lane()
                return True
        return False

    def _draw_hud_minimal(self):
        if not self.player_pyramid_eid or not self.enemy_pyramid_eid:
            return

        if self.world:
            self.world._activate()

        wallet = esper.component_for_entity(self.player_pyramid_eid, Wallet)
        player_hp = esper.component_for_entity(self.player_pyramid_eid, Health)
        enemy_hp = esper.component_for_entity(self.enemy_pyramid_eid, Health)

        try:
            income = esper.component_for_entity(self.player_pyramid_eid, IncomeRate)
            income_txt = f"{income.rate:.1f}/s"
            if hasattr(income, 'multiplier') and income.multiplier != 1.0:
                income_txt += f" (x{income.multiplier:.2f})"
        except Exception:
            income_txt = "?"

        self._draw_panel(12, 12, 580, 130, alpha=115)
        x = 22
        y = 20

        line1 = self.font.render(f"Coups de fouet: {int(wallet.solde)}   |   Prod: {income_txt}", True, (240, 240, 240))
        line2 = self.font.render(f"Pyramide: {player_hp.hp}/{player_hp.hp_max}   |   Ennemi: {enemy_hp.hp}/{enemy_hp.hp_max}", True, (240, 240, 240))
        line3 = self.font_small.render("Z/X/C (ou W/X/C) lane   1/2/3 spawn   U upgrade   ESC pause", True, (220, 220, 220))

        self.screen.blit(line1, (x, y)); y += 24
        self.screen.blit(line2, (x, y)); y += 24
        self.screen.blit(line3, (x, y))

        self._draw_lane_selector()

        map_txt = self.font_small.render(f"Map: {self.last_map_name}", True, (200, 200, 200))
        self.screen.blit(map_txt, (22, 118))

        # ✅ Afficher message d'événement aléatoire
        if self.random_event_system:
            msg = self.random_event_system.get_message()
            if msg:
                event_surf = self.font_big.render(msg, True, (255, 220, 80))
                event_rect = event_surf.get_rect(center=(self.width // 2, self.height // 2 - 100))
                # Fond semi-transparent
                bg_rect = event_rect.inflate(20, 10)
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surf.fill((0, 0, 0, 180))
                self.screen.blit(bg_surf, bg_rect.topleft)
                self.screen.blit(event_surf, event_rect)

    def _draw_hud_advanced(self):
        self._draw_panel(12, 112, 640, 94, alpha=100)
        x = 22
        y = 120

        z = self.last_zone_counts
        l1 = self.font_small.render(
            f"Seed: {self.last_map_seed} | open={z.get('open',0)} dusty={z.get('dusty',0)} interdit={z.get('forbidden',0)}",
            True,
            (230, 230, 230),
        )
        l2 = self.font_small.render(f"Temps: {self.match_time:.1f}s | Kills: {self.enemy_kills}", True, (230, 230, 230))
        
        # ✅ Afficher niveau de difficulté
        diff_txt = ""
        if self.difficulty_system:
            diff_txt = self.difficulty_system.hud_line()
        l3 = self.font_small.render(diff_txt, True, (255, 200, 100))
        
        self.screen.blit(l1, (x, y))
        self.screen.blit(l2, (x, y + 20))
        self.screen.blit(l3, (x, y + 40))

    def _draw_minimap(self):
        """Dessine une minimap en bas à droite."""
        if not self.nav_grid:
            return
            
        grid_w = int(getattr(self.nav_grid, "width", 0))
        grid_h = int(getattr(self.nav_grid, "height", 0))
        if grid_w <= 0 or grid_h <= 0:
            return

        # Dimensions minimap
        mm_w = 150
        mm_h = 80
        mm_x = self.width - mm_w - 15
        mm_y = self.height - mm_h - 15
        
        # Fond semi-transparent
        bg = pygame.Surface((mm_w + 4, mm_h + 4), pygame.SRCALPHA)
        bg.fill((20, 20, 25, 200))
        self.screen.blit(bg, (mm_x - 2, mm_y - 2))
        
        # Bordure
        pygame.draw.rect(self.screen, (80, 80, 90), (mm_x - 2, mm_y - 2, mm_w + 4, mm_h + 4), 1)
        
        # Échelle
        scale_x = mm_w / grid_w
        scale_y = mm_h / grid_h
        
        # Dessiner le terrain (simplifié)
        for y in range(grid_h):
            for x in range(grid_w):
                walk = self.nav_grid.is_walkable(x, y)
                m = float(self.nav_grid.mult[y][x])
                
                px = mm_x + int(x * scale_x)
                py = mm_y + int(y * scale_y)
                pw = max(1, int(scale_x))
                ph = max(1, int(scale_y))
                
                if not walk or m <= 0:
                    color = (100, 50, 50)  # Interdit
                elif m < 0.99:
                    color = (120, 100, 70)  # Dusty
                else:
                    color = (80, 80, 60)  # Open
                
                pygame.draw.rect(self.screen, color, (px, py, pw, ph))
        
        # Dessiner les lanes
        for lane_y in self.lanes_y:
            py = mm_y + int(lane_y * scale_y)
            pygame.draw.line(self.screen, (60, 60, 80), (mm_x, py), (mm_x + mm_w, py), 1)
        
        # Dessiner les pyramides
        for eid in (self.player_pyramid_eid, self.enemy_pyramid_eid):
            if not esper.entity_exists(eid):
                continue
            t = esper.component_for_entity(eid, Transform)
            team = esper.component_for_entity(eid, Team)
            
            px = mm_x + int(t.pos[0] * scale_x)
            py = mm_y + int(t.pos[1] * scale_y)
            
            color = (80, 220, 140) if team.id == 1 else (240, 100, 100)
            pygame.draw.rect(self.screen, color, (px - 3, py - 3, 6, 6))
        
        # Dessiner les unités
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if ent in (self.player_pyramid_eid, self.enemy_pyramid_eid):
                continue
            
            if esper.has_component(ent, Health):
                hp = esper.component_for_entity(ent, Health)
                if hp.is_dead:
                    continue
            
            px = mm_x + int(t.pos[0] * scale_x)
            py = mm_y + int(t.pos[1] * scale_y)
            
            color = (100, 255, 160) if team.id == 1 else (255, 120, 120)
            pygame.draw.circle(self.screen, color, (px, py), 2)
        
        # Label
        label = self.font_small.render("Minimap", True, (180, 180, 180))
        self.screen.blit(label, (mm_x, mm_y - 18))

    # ----------------------------
    # State helpers
    # ----------------------------
    def _open_options(self):
        self.state_return = self.state
        self.state = "options"

        self._sync_toggle_value(self.tog_lanes, self.opt_show_lanes)
        self._sync_toggle_value(self.tog_terrain, self.opt_show_terrain)
        self._sync_toggle_value(self.tog_nav, self.opt_show_nav)
        self._sync_toggle_value(self.tog_paths, self.opt_show_paths)
        self._sync_toggle_value(self.tog_advhud, self.opt_show_advhud)

    def _open_controls(self):
        self.state_return = self.state
        self.state = "controls"

    def _return_from_submenu(self):
        self.state = self.state_return if self.state_return else "menu"

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
            from Game.App.sound_manager import sound_manager
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
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if self.state in ("options", "controls") and event.key == pygame.K_ESCAPE:
                        self._return_from_submenu()

                # MENU
                if self.state == "menu":
                    if self.btn_play.handle_event(event):
                        self._teardown_match()
                        self._setup_match()
                        self.state = "playing"

                    if self.btn_options.handle_event(event):
                        self._open_options()

                    if self.btn_controls.handle_event(event):
                        self._open_controls()

                    if self.btn_quit.handle_event(event):
                        self.running = False

                # OPTIONS
                elif self.state == "options":
                    if self.btn_back.handle_event(event):
                        self._return_from_submenu()

                    if self.tog_lanes.handle_event(event):
                        self.opt_show_lanes = self.tog_lanes.value
                    if self.tog_terrain.handle_event(event):
                        self.opt_show_terrain = self.tog_terrain.value
                    if self.tog_nav.handle_event(event):
                        self.opt_show_nav = self.tog_nav.value
                    if self.tog_paths.handle_event(event):
                        self.opt_show_paths = self.tog_paths.value
                    if self.tog_advhud.handle_event(event):
                        self.opt_show_advhud = self.tog_advhud.value

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
            self.screen.fill((18, 18, 22))

            if self.game_map:
                self.game_map.draw(self.screen, int(self.camera_x), int(self.camera_y))

            if self.state in ("playing", "pause", "game_over") and self.world:
                self._draw_lane_preview_path()

                if self.opt_show_lanes:
                    self._draw_lane_paths_all()

                if self.opt_show_terrain:
                    self._draw_terrain_overlay()
                if self.opt_show_nav:
                    self._debug_draw_forbidden()
                if self.opt_show_paths:
                    self._debug_draw_paths()

                self._draw_entities()
                self._draw_hud_minimal()
                if self.opt_show_advhud:
                    self._draw_hud_advanced()
                
                # Minimap en bas à droite
                self._draw_minimap()

            if self.state == "menu":
                self._draw_center_overlay("Antique War", "Lane1=haut / Lane2=milieu / Lane3=bas")
                rec = self.font_small.render(
                    f"Record: {self.best_time:.1f}s | Kills: {self.best_kills}",
                    True,
                    (230, 230, 230),
                )
                rr = rec.get_rect(center=(self.width // 2, self.height // 2 - 40))
                self.screen.blit(rec, rr)

                self.btn_play.draw(self.screen)
                self.btn_options.draw(self.screen)
                self.btn_controls.draw(self.screen)
                self.btn_quit.draw(self.screen)

            elif self.state == "options":
                self._draw_center_overlay("Options", "ESC ou Retour pour revenir")
                self.btn_back.draw(self.screen)

                self.tog_lanes.draw(self.screen)
                self.tog_terrain.draw(self.screen)
                self.tog_nav.draw(self.screen)
                self.tog_paths.draw(self.screen)
                self.tog_advhud.draw(self.screen)

            elif self.state == "controls":
                self._draw_center_overlay("Commandes", "ESC ou Retour pour revenir")
                self.btn_back.draw(self.screen)

                self._draw_panel(48, 120, self.width - 96, self.height - 190, alpha=110)
                x = 70
                y = 150
                lines = [
                    "Déplacement caméra : flèches",
                    "Choisir la lane : Z / X / C (ou W / X / C)",
                    "Lane cliquable : boutons Lane 1/2/3 en haut",
                    "Spawn unités : 1 / 2 / 3",
                    "Upgrade pyramide : U",
                    "Pause : ESC",
                ]
                for txt in lines:
                    surf = self.font.render(txt, True, (240, 240, 240))
                    self.screen.blit(surf, (x, y))
                    y += 24

            elif self.state == "pause":
                self._draw_center_overlay("Pause", "ESC pour reprendre")
                self.btn_resume.draw(self.screen)
                self.btn_restart.draw(self.screen)
                self.btn_pause_options.draw(self.screen)
                self.btn_menu.draw(self.screen)

            elif self.state == "game_over":
                # Titre victoire/défaite avec couleur
                title_color = (80, 255, 140) if self.game_over_text == "VICTORY" else (255, 100, 100)
                title_surf = self.font_big.render(self.game_over_text, True, title_color)
                title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 - 140))
                self.screen.blit(title_surf, title_rect)
                
                # Panel de stats
                self._draw_panel(self.width // 2 - 220, self.height // 2 - 100, 440, 180, alpha=140)
                
                # Statistiques détaillées
                stats_x = self.width // 2 - 200
                stats_y = self.height // 2 - 85
                line_h = 26
                
                # Temps de jeu
                time_txt = f"⏱️ Temps de jeu: {self.match_time:.1f}s"
                s1 = self.font.render(time_txt, True, (240, 240, 240))
                self.screen.blit(s1, (stats_x, stats_y))
                stats_y += line_h
                
                # Kills
                kills_txt = f"💀 Ennemis éliminés: {self.enemy_kills}"
                s2 = self.font.render(kills_txt, True, (240, 240, 240))
                self.screen.blit(s2, (stats_x, stats_y))
                stats_y += line_h
                
                # Niveau de difficulté atteint
                diff_level = 1
                if self.difficulty_system:
                    diff_level = self.difficulty_system.level
                diff_txt = f"📈 Niveau difficulté: {diff_level}"
                s3 = self.font.render(diff_txt, True, (240, 240, 240))
                self.screen.blit(s3, (stats_x, stats_y))
                stats_y += line_h
                
                # Score (basé sur temps + kills)
                score = int(self.match_time * 10 + self.enemy_kills * 50)
                score_txt = f"⭐ Score: {score}"
                s4 = self.font.render(score_txt, True, (255, 220, 100))
                self.screen.blit(s4, (stats_x, stats_y))
                stats_y += line_h + 5
                
                # Records
                record_txt = f"🏆 Records: {self.best_time:.1f}s | {self.best_kills} kills"
                s5 = self.font_small.render(record_txt, True, (200, 200, 200))
                self.screen.blit(s5, (stats_x, stats_y))
                
                # Nouveau record?
                if self.match_time >= self.best_time or self.enemy_kills >= self.best_kills:
                    new_rec = self.font.render("🎉 NOUVEAU RECORD!", True, (255, 220, 80))
                    rec_rect = new_rec.get_rect(center=(self.width // 2, self.height // 2 + 65))
                    self.screen.blit(new_rec, rec_rect)

                self.btn_restart.draw(self.screen)
                self.btn_menu.draw(self.screen)

            pygame.display.flip()

        self.shutdown()


def main():
    GameApp().run()


if __name__ == "__main__":
    main()
