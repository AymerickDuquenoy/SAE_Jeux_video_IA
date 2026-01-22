# Game/App/game_app.py
"""
Main application module for Antique War.
Handles the main game loop, state management, and event processing.

Refactored from monolithic 1745-line file into modular architecture.
"""

import json
import pygame
import esper
from pathlib import Path

from Game.Services.clock import GameClock
from Game.Services.event_bus import EventBus
from Game.Services.balance_config import BalanceConfig

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.unitStats import UnitStats

from Game.App.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS,
    STATE_MENU, STATE_OPTIONS, STATE_CONTROLS, STATE_PLAYING, STATE_PAUSE, STATE_GAME_OVER,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_BIG,
    DEFAULT_LANE_INDEX, LANE_FLASH_DURATION, CAMERA_SPEED,
    MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT, MENU_BUTTON_GAP,
    TOGGLE_WIDTH, TOGGLE_HEIGHT, TOGGLE_GAP,
    BACK_BTN_X, BACK_BTN_Y, BACK_BTN_WIDTH, BACK_BTN_HEIGHT,
    COLOR_BACKGROUND, COLOR_TEXT_DIM
)

from Game.App.ui import UIButton, UIToggle, UIOverlay
from Game.App.renderer import GameRenderer
from Game.App.hud import GameHUD, ControlsDisplay, GameOverDisplay
from Game.App.match_manager import MatchManager


class GameApp:
    """Main game application class."""
    
    def __init__(self, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT,
                 title: str = WINDOW_TITLE):
        self.width = width
        self.height = height
        self.title = title
        
        # Pygame resources
        self.screen = None
        self.running = False
        self.clock = GameClock(fps=FPS)
        self.bus = EventBus()
        
        # Fonts
        self.font = None
        self.font_small = None
        self.font_big = None
        
        # Paths
        self.game_root = Path(__file__).resolve().parents[1]
        self.save_path = self.game_root / "assets" / "config" / "save.json"
        
        # Configuration
        self.balance = None
        
        # State machine
        self.state = STATE_MENU
        self.state_return = STATE_MENU
        self.game_over_text = ""
        
        # Match manager
        self.match_manager = None
        
        # Renderer and HUD
        self.renderer = None
        self.hud = None
        self.controls_display = None
        self.game_over_display = None
        self.overlay = None
        
        # Debug options
        self.opt_show_lanes = False
        self.opt_show_terrain = False
        self.opt_show_nav = False
        self.opt_show_paths = False
        self.opt_show_advhud = False
        
        # Camera
        self.camera_x = 0.0
        self.camera_y = 0.0
        
        # Lane selection
        self.selected_lane_idx = DEFAULT_LANE_INDEX
        
        # Lane preview
        self.lane_flash_timer = 0.0
        self.lane_preview_path = []
        
        # Stats
        self.match_time = 0.0
        self.enemy_kills = 0
        self.best_time = 0.0
        self.best_kills = 0
        self._prev_enemy_ids = set()
        self._known_units = set()
        
        # UI buttons
        self.btn_play = None
        self.btn_options = None
        self.btn_controls = None
        self.btn_quit = None
        self.btn_back = None
        self.btn_resume = None
        self.btn_restart = None
        self.btn_pause_options = None
        self.btn_menu = None
        
        # Toggle buttons
        self.tog_lanes = None
        self.tog_terrain = None
        self.tog_nav = None
        self.tog_paths = None
        self.tog_advhud = None
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    def boot(self):
        """Initialize pygame and load resources."""
        pygame.init()
        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        self.font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE_NORMAL)
        self.font_small = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE_SMALL)
        self.font_big = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE_BIG)
        
        self._load_save()
        
        balance_file = self.game_root / "assets" / "config" / "balance.json"
        self.balance = BalanceConfig.load(str(balance_file)).data
        
        self.match_manager = MatchManager(self.game_root, self.balance)
        self._build_ui()
        
        self.overlay = UIOverlay(self.width, self.height)
        self.controls_display = ControlsDisplay(self.screen, self.font)
        self.game_over_display = GameOverDisplay(self.screen, self.font, self.font_small)
    
    def shutdown(self):
        """Clean up resources."""
        pygame.quit()
    
    def run(self):
        """Main game loop."""
        self.boot()
        self.running = True
        
        while self.running:
            dt = self.clock.tick()
            
            if self.lane_flash_timer > 0.0:
                self.lane_flash_timer = max(0.0, self.lane_flash_timer - dt)
            
            self._process_events()
            self._update(dt)
            self._render()
            pygame.display.flip()
        
        self.shutdown()
    
    # =========================================================================
    # SAVE/LOAD
    # =========================================================================
    
    def _load_save(self):
        self.best_time = 0.0
        self.best_kills = 0
        try:
            if self.save_path.exists():
                data = json.loads(self.save_path.read_text(encoding="utf-8"))
                self.best_time = float(data.get("best_time", 0.0))
                self.best_kills = int(data.get("best_kills", 0))
        except Exception:
            pass
    
    def _save_save(self):
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"best_time": float(self.best_time), "best_kills": int(self.best_kills)}
            self.save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass
    
    # =========================================================================
    # UI BUILDING
    # =========================================================================
    
    def _build_ui(self):
        cx, cy = self.width // 2, self.height // 2
        w, h, gap = MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT, MENU_BUTTON_GAP
        
        self.btn_play = UIButton(pygame.Rect(cx - w // 2, cy - (h + gap), w, h), "Jouer", self.font)
        self.btn_options = UIButton(pygame.Rect(cx - w // 2, cy, w, h), "Options", self.font)
        self.btn_controls = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap), w, h), "Commandes", self.font)
        self.btn_quit = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 2, w, h), "Quitter", self.font)
        
        self.btn_back = UIButton(pygame.Rect(BACK_BTN_X, BACK_BTN_Y, BACK_BTN_WIDTH, BACK_BTN_HEIGHT), "Retour", self.font)
        
        self.btn_resume = UIButton(pygame.Rect(cx - w // 2, cy - (h + gap), w, h), "Reprendre", self.font)
        self.btn_restart = UIButton(pygame.Rect(cx - w // 2, cy, w, h), "Recommencer", self.font)
        self.btn_pause_options = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap), w, h), "Options", self.font)
        self.btn_menu = UIButton(pygame.Rect(cx - w // 2, cy + (h + gap) * 2, w, h), "Menu", self.font)
        
        ox, oy = cx - TOGGLE_WIDTH // 2, 130
        tw, th, tg = TOGGLE_WIDTH, TOGGLE_HEIGHT, TOGGLE_GAP
        
        self.tog_lanes = UIToggle(pygame.Rect(ox, oy, tw, th), "Afficher les lanes", self.font, False)
        self.tog_terrain = UIToggle(pygame.Rect(ox, oy + (th + tg), tw, th), "Afficher terrain", self.font, False)
        self.tog_nav = UIToggle(pygame.Rect(ox, oy + (th + tg) * 2, tw, th), "Debug nav", self.font, False)
        self.tog_paths = UIToggle(pygame.Rect(ox, oy + (th + tg) * 3, tw, th), "Debug paths", self.font, False)
        self.tog_advhud = UIToggle(pygame.Rect(ox, oy + (th + tg) * 4, tw, th), "HUD avancée", self.font, False)
    
    # =========================================================================
    # MATCH LIFECYCLE
    # =========================================================================
    
    def _start_match(self):
        self.match_time = 0.0
        self.enemy_kills = 0
        self._prev_enemy_ids = set()
        self._known_units = set()
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.selected_lane_idx = DEFAULT_LANE_INDEX
        self.game_over_text = ""
        
        self.match_manager.setup_match()
        
        self.renderer = GameRenderer(self.screen, self.match_manager.game_map, self.match_manager.nav_grid)
        self.hud = GameHUD(self.screen, self.font, self.font_small)
        self.hud.set_selected_lane(self.selected_lane_idx)
        self._flash_lane()
    
    def _end_match(self):
        self.match_manager.teardown_match()
        self.renderer = None
        self.hud = None
        self.lane_flash_timer = 0.0
        self.lane_preview_path = []
    
    # =========================================================================
    # LANE MANAGEMENT
    # =========================================================================
    
    def _set_selected_lane(self, idx: int):
        idx = max(0, min(2, int(idx)))
        self.selected_lane_idx = idx
        if self.hud:
            self.hud.set_selected_lane(idx)
        if self.match_manager and self.match_manager.systems.get("input"):
            try:
                self.match_manager.systems["input"].selected_lane = idx
            except Exception:
                pass
    
    def _flash_lane(self):
        self.lane_flash_timer = LANE_FLASH_DURATION
        if self.match_manager and self.match_manager.lane_paths:
            idx = self.selected_lane_idx
            if 0 <= idx < len(self.match_manager.lane_paths):
                self.lane_preview_path = list(self.match_manager.lane_paths[idx])
            else:
                self.lane_preview_path = []
        else:
            self.lane_preview_path = []
    
    # =========================================================================
    # EVENT PROCESSING
    # =========================================================================
    
    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                if self.state in (STATE_OPTIONS, STATE_CONTROLS) and event.key == pygame.K_ESCAPE:
                    self._return_from_submenu()
                    continue
            
            if self.state == STATE_MENU:
                self._process_menu_events(event)
            elif self.state == STATE_OPTIONS:
                self._process_options_events(event)
            elif self.state == STATE_CONTROLS:
                self._process_controls_events(event)
            elif self.state == STATE_PLAYING:
                self._process_playing_events(event)
            elif self.state == STATE_PAUSE:
                self._process_pause_events(event)
            elif self.state == STATE_GAME_OVER:
                self._process_game_over_events(event)
    
    def _process_menu_events(self, event):
        if self.btn_play.handle_event(event):
            self._end_match()
            self._start_match()
            self.state = STATE_PLAYING
        if self.btn_options.handle_event(event):
            self._open_options()
        if self.btn_controls.handle_event(event):
            self._open_controls()
        if self.btn_quit.handle_event(event):
            self.running = False
    
    def _process_options_events(self, event):
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
    
    def _process_controls_events(self, event):
        if self.btn_back.handle_event(event):
            self._return_from_submenu()
    
    def _process_playing_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            lane_clicked = self.hud.handle_event(event)
            if lane_clicked >= 0:
                self._set_selected_lane(lane_clicked)
                self._flash_lane()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = STATE_PAUSE
            if event.key in (pygame.K_z, pygame.K_w):
                self._set_selected_lane(0)
                self._flash_lane()
            elif event.key == pygame.K_x:
                self._set_selected_lane(1)
                self._flash_lane()
            elif event.key == pygame.K_c:
                self._set_selected_lane(2)
                self._flash_lane()
            if event.key == pygame.K_u and self.match_manager.systems.get("upgrade"):
                self.match_manager.systems["upgrade"].request_upgrade()
    
    def _process_pause_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = STATE_PLAYING
        if self.btn_resume.handle_event(event):
            self.state = STATE_PLAYING
        if self.btn_restart.handle_event(event):
            self._end_match()
            self._start_match()
            self.state = STATE_PLAYING
        if self.btn_pause_options.handle_event(event):
            self._open_options()
        if self.btn_menu.handle_event(event):
            self._end_match()
            self.state = STATE_MENU
    
    def _process_game_over_events(self, event):
        if self.btn_restart.handle_event(event):
            self._end_match()
            self._start_match()
            self.state = STATE_PLAYING
        if self.btn_menu.handle_event(event):
            self._end_match()
            self.state = STATE_MENU
    
    # =========================================================================
    # STATE HELPERS
    # =========================================================================
    
    def _open_options(self):
        self.state_return = self.state
        self.state = STATE_OPTIONS
        self.tog_lanes.value = self.opt_show_lanes
        self.tog_terrain.value = self.opt_show_terrain
        self.tog_nav.value = self.opt_show_nav
        self.tog_paths.value = self.opt_show_paths
        self.tog_advhud.value = self.opt_show_advhud
    
    def _open_controls(self):
        self.state_return = self.state
        self.state = STATE_CONTROLS
    
    def _return_from_submenu(self):
        self.state = self.state_return if self.state_return else STATE_MENU
    
    # =========================================================================
    # UPDATE
    # =========================================================================
    
    def _update(self, dt: float):
        if self.state != STATE_PLAYING or not self.match_manager.world:
            return
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.camera_x -= CAMERA_SPEED * dt
        if keys[pygame.K_RIGHT]:
            self.camera_x += CAMERA_SPEED * dt
        if keys[pygame.K_UP]:
            self.camera_y -= CAMERA_SPEED * dt
        if keys[pygame.K_DOWN]:
            self.camera_y += CAMERA_SPEED * dt
        
        self.match_time += dt
        self.match_manager.world.process(dt)
        self._snap_new_units_to_lane()
        self._update_kills_tracker()
        self._check_game_over()
    
    def _snap_new_units_to_lane(self):
        if not self.match_manager.world:
            return
        self.match_manager.world._activate()
        
        pyramid_ids = {int(self.match_manager.player_pyramid_eid), int(self.match_manager.enemy_pyramid_eid)}
        
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if int(ent) in pyramid_ids or team.id != 1 or ent in self._known_units:
                continue
            if self.match_manager.systems.get("lane_route"):
                try:
                    self.match_manager.systems["lane_route"].set_lane_for_entity(int(ent), int(self.selected_lane_idx))
                except Exception:
                    pass
            self._known_units.add(ent)
    
    def _update_kills_tracker(self):
        if not self.match_manager.world:
            return
        self.match_manager.world._activate()
        
        current = set()
        for ent, (team,) in esper.get_components(Team):
            if ent not in (self.match_manager.player_pyramid_eid, self.match_manager.enemy_pyramid_eid) and team.id == 2:
                current.add(ent)
        
        if self._prev_enemy_ids:
            self.enemy_kills += len(self._prev_enemy_ids - current)
        self._prev_enemy_ids = current
    
    def _check_game_over(self):
        try:
            enemy_hp = esper.component_for_entity(self.match_manager.enemy_pyramid_eid, Health)
            player_hp = esper.component_for_entity(self.match_manager.player_pyramid_eid, Health)
        except Exception:
            return
        
        if enemy_hp.is_dead:
            self.state = STATE_GAME_OVER
            self.game_over_text = "VICTORY"
            self._check_record()
        elif player_hp.is_dead:
            self.state = STATE_GAME_OVER
            self.game_over_text = "DEFEAT"
            self._check_record()
    
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
    
    # =========================================================================
    # RENDERING
    # =========================================================================
    
    def _render(self):
        self.screen.fill(COLOR_BACKGROUND)
        
        if self.match_manager and self.match_manager.game_map:
            self.match_manager.game_map.draw(self.screen, int(self.camera_x), int(self.camera_y))
        
        if self.state == STATE_MENU:
            self._render_menu()
        elif self.state == STATE_OPTIONS:
            self._render_options()
        elif self.state == STATE_CONTROLS:
            self._render_controls()
        elif self.state == STATE_PLAYING:
            self._render_playing()
        elif self.state == STATE_PAUSE:
            self._render_pause()
        elif self.state == STATE_GAME_OVER:
            self._render_game_over()
    
    def _render_menu(self):
        self.overlay.draw(self.screen, "Antique War", "Lane1=haut / Lane2=milieu / Lane3=bas", self.font_big, self.font)
        rec = self.font_small.render(f"Record: {self.best_time:.1f}s | Kills: {self.best_kills}", True, COLOR_TEXT_DIM)
        self.screen.blit(rec, rec.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.btn_play.draw(self.screen)
        self.btn_options.draw(self.screen)
        self.btn_controls.draw(self.screen)
        self.btn_quit.draw(self.screen)
    
    def _render_options(self):
        self.overlay.draw(self.screen, "Options", "ESC ou Retour pour revenir", self.font_big, self.font)
        self.btn_back.draw(self.screen)
        self.tog_lanes.draw(self.screen)
        self.tog_terrain.draw(self.screen)
        self.tog_nav.draw(self.screen)
        self.tog_paths.draw(self.screen)
        self.tog_advhud.draw(self.screen)
    
    def _render_controls(self):
        self.overlay.draw(self.screen, "Commandes", "ESC ou Retour pour revenir", self.font_big, self.font)
        self.btn_back.draw(self.screen)
        self.controls_display.draw()
    
    def _render_playing(self):
        if not self.renderer:
            return
        
        if self.opt_show_terrain:
            self.renderer.draw_terrain_overlay(self.camera_x, self.camera_y)
        if self.opt_show_nav:
            self.renderer.draw_forbidden_debug(self.camera_x, self.camera_y)
        if self.opt_show_lanes:
            self.renderer.draw_lane_paths(self.match_manager.lane_paths, self.camera_x, self.camera_y)
        
        self.renderer.draw_lane_preview(self.lane_preview_path, self.camera_x, self.camera_y, self.lane_flash_timer)
        
        if self.opt_show_paths:
            self.renderer.draw_paths_debug(self.camera_x, self.camera_y)
        
        pyramid_ids = {int(self.match_manager.player_pyramid_eid), int(self.match_manager.enemy_pyramid_eid)}
        self.renderer.draw_pyramids(self.match_manager.player_pyramid_eid, self.match_manager.enemy_pyramid_eid, self.camera_x, self.camera_y)
        self.renderer.draw_units(pyramid_ids, self.camera_x, self.camera_y)
        self.renderer.draw_projectiles(self.camera_x, self.camera_y)
        
        self.hud.draw(
            self.match_manager.player_pyramid_eid, self.match_manager.enemy_pyramid_eid,
            map_name=self.match_manager.last_map_name, show_advanced=self.opt_show_advhud,
            match_time=self.match_time, enemy_kills=self.enemy_kills,
            zone_counts=self.match_manager.last_zone_counts, map_seed=self.match_manager.last_map_seed
        )
    
    def _render_pause(self):
        self._render_playing()
        self.overlay.draw(self.screen, "Pause", "ESC pour reprendre", self.font_big, self.font)
        self.btn_resume.draw(self.screen)
        self.btn_restart.draw(self.screen)
        self.btn_pause_options.draw(self.screen)
        self.btn_menu.draw(self.screen)
    
    def _render_game_over(self):
        self._render_playing()
        self.overlay.draw(self.screen, self.game_over_text, "Rejoue pour battre ton record", self.font_big, self.font)
        self.game_over_display.draw(self.match_time, self.enemy_kills, self.best_time, self.best_kills)
        self.btn_restart.draw(self.screen)
        self.btn_menu.draw(self.screen)


def main():
    """Entry point."""
    GameApp().run()


if __name__ == "__main__":
    main()
