# Game/App/renderer.py
"""
Rendering module for Antique War.
Handles all drawing operations: entities, terrain, debug overlays, etc.
"""

import pygame
import esper

from Game.App.constants import (
    COLOR_BACKGROUND, COLOR_PLAYER, COLOR_PLAYER_LIGHT, COLOR_ENEMY, COLOR_ENEMY_DARK,
    COLOR_PROJECTILE, COLOR_TEXT, COLOR_FORBIDDEN_OVERLAY, COLOR_DUSTY_OVERLAY,
    COLOR_LANE_PATH, COLOR_LANE_PREVIEW,
    UNIT_RADIUS, PYRAMID_SIZE_MULT, PROJECTILE_RADIUS,
    HEALTH_BAR_HEIGHT
)

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.path import Path as PathComponent


class GameRenderer:
    """
    Handles all rendering operations for the game.
    """
    
    def __init__(self, screen: pygame.Surface, game_map, nav_grid):
        self.screen = screen
        self.game_map = game_map
        self.nav_grid = nav_grid
        self.width = screen.get_width()
        self.height = screen.get_height()
    
    def update_references(self, game_map, nav_grid):
        """Update map and nav grid references (called on new match)."""
        self.game_map = game_map
        self.nav_grid = nav_grid
    
    def clear(self):
        """Clear screen with background color."""
        self.screen.fill(COLOR_BACKGROUND)
    
    def grid_to_screen(self, gx: float, gy: float, camera_x: float, camera_y: float) -> tuple[int, int]:
        """Convert grid coordinates to screen coordinates."""
        if not self.game_map:
            return (0, 0)
        tw = int(self.game_map.tilewidth)
        th = int(self.game_map.tileheight)
        px = (gx + 0.5) * tw
        py = (gy + 0.5) * th
        return int(px - camera_x), int(py - camera_y)
    
    def draw_map(self, camera_x: float, camera_y: float):
        """Draw the tile map."""
        if self.game_map:
            self.game_map.draw(self.screen, int(camera_x), int(camera_y))
    
    def draw_pyramids(self, player_pyramid_eid: int, enemy_pyramid_eid: int,
                      camera_x: float, camera_y: float):
        """Draw both pyramids with health bars."""
        for eid, is_player in [(player_pyramid_eid, True), (enemy_pyramid_eid, False)]:
            try:
                t = esper.component_for_entity(eid, Transform)
                team = esper.component_for_entity(eid, Team)
                h = esper.component_for_entity(eid, Health)
            except Exception:
                continue
            
            sx, sy = self.grid_to_screen(t.pos[0], t.pos[1], camera_x, camera_y)
            size = int(self.game_map.tilewidth * PYRAMID_SIZE_MULT)
            rect = pygame.Rect(int(sx - size / 2), int(sy - size / 2), size, size)
            
            # Pyramid color
            color = COLOR_PLAYER_LIGHT if is_player else COLOR_ENEMY_DARK
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLOR_BACKGROUND, rect, 3)
            
            # Health bar
            self._draw_health_bar(sx, sy - size // 2 - 8, size, h)
    
    def draw_units(self, pyramid_ids: set[int], camera_x: float, camera_y: float):
        """Draw all units (excluding pyramids)."""
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if ent in pyramid_ids:
                continue
            
            sx, sy = self.grid_to_screen(t.pos[0], t.pos[1], camera_x, camera_y)
            
            # Unit color based on team
            color = COLOR_PLAYER if team.id == 1 else COLOR_ENEMY
            
            # Draw unit circle
            pygame.draw.circle(self.screen, color, (sx, sy), UNIT_RADIUS)
            pygame.draw.circle(self.screen, COLOR_BACKGROUND, (sx, sy), UNIT_RADIUS, 2)
            
            # Draw health bar for units
            try:
                h = esper.component_for_entity(ent, Health)
                self._draw_health_bar(sx, sy - UNIT_RADIUS - 6, UNIT_RADIUS * 2, h)
            except Exception:
                pass
    
    def draw_projectiles(self, camera_x: float, camera_y: float):
        """Draw all projectiles."""
        for ent, (t, p) in esper.get_components(Transform, Projectile):
            sx, sy = self.grid_to_screen(t.pos[0], t.pos[1], camera_x, camera_y)
            pygame.draw.circle(self.screen, COLOR_PROJECTILE, (sx, sy), PROJECTILE_RADIUS)
    
    def _draw_health_bar(self, cx: int, top_y: int, width: int, health: Health):
        """Draw a health bar centered at cx, with top at top_y."""
        if health.hp_max <= 0:
            return
        
        ratio = max(0.0, min(1.0, health.hp / health.hp_max))
        bar_x = cx - width // 2
        
        # Background
        bg_rect = pygame.Rect(bar_x, top_y, width, HEALTH_BAR_HEIGHT)
        pygame.draw.rect(self.screen, (20, 20, 20), bg_rect)
        
        # Foreground (health)
        fg_rect = pygame.Rect(bar_x, top_y, int(width * ratio), HEALTH_BAR_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_TEXT, fg_rect)
    
    # =========================================================================
    # LANE PATH RENDERING
    # =========================================================================
    
    def draw_lane_paths(self, lane_paths: list[list[tuple[int, int]]],
                        camera_x: float, camera_y: float):
        """Draw all three lane paths (subtle overlay)."""
        if not lane_paths:
            return
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for path in lane_paths:
            if not path or len(path) < 2:
                continue
            
            pts = [self.grid_to_screen(x, y, camera_x, camera_y) for (x, y) in path]
            pygame.draw.lines(overlay, COLOR_LANE_PATH, False, pts, 3)
        
        self.screen.blit(overlay, (0, 0))
    
    def draw_lane_preview(self, preview_path: list[tuple[int, int]],
                          camera_x: float, camera_y: float, timer: float):
        """Draw the lane preview (highlighted path when selecting lane)."""
        if timer <= 0.0 or not preview_path or len(preview_path) < 2:
            return
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pts = [self.grid_to_screen(x, y, camera_x, camera_y) for (x, y) in preview_path]
        
        # Main line
        pygame.draw.lines(overlay, COLOR_LANE_PREVIEW, False, pts, 4)
        
        # Dots along path
        for p in pts[::2]:
            pygame.draw.circle(overlay, (240, 240, 240, 200), p, 3, 1)
        
        self.screen.blit(overlay, (0, 0))
    
    # =========================================================================
    # DEBUG OVERLAYS
    # =========================================================================
    
    def draw_terrain_overlay(self, camera_x: float, camera_y: float):
        """Draw terrain type overlay (debug: shows dusty/forbidden zones)."""
        if not self.nav_grid:
            return
        
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
                    color = COLOR_FORBIDDEN_OVERLAY
                elif m < 0.99:
                    color = COLOR_DUSTY_OVERLAY
                else:
                    continue  # Open terrain - no overlay
                
                sx, sy = self.grid_to_screen(float(x), float(y), camera_x, camera_y)
                rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                s = pygame.Surface((tw, th), pygame.SRCALPHA)
                s.fill(color)
                self.screen.blit(s, rect.topleft)
    
    def draw_forbidden_debug(self, camera_x: float, camera_y: float):
        """Draw red borders around forbidden cells (debug)."""
        if not self.nav_grid:
            return
        
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
                    sx, sy = self.grid_to_screen(float(x), float(y), camera_x, camera_y)
                    rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                    pygame.draw.rect(self.screen, (220, 50, 50), rect, 1)
    
    def draw_paths_debug(self, camera_x: float, camera_y: float):
        """Draw unit paths (debug)."""
        from Game.Ecs.Components.path import Path as PathComponent
        
        for ent, (t, path) in esper.get_components(Transform, PathComponent):
            if not path.noeuds:
                continue
            
            pts = [self.grid_to_screen(n.x, n.y, camera_x, camera_y) for n in path.noeuds]
            if len(pts) >= 2:
                pygame.draw.lines(self.screen, (30, 30, 30), False, pts, 2)
