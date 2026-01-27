# Game/App/renderers/entity_renderer.py
"""Entity, terrain and minimap rendering for Antique War."""

import pygame
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.pyramidLevel import PyramidLevel
from Game.Ecs.Components.path import Path as PathComponent


class EntityRenderer:
    """Rendu des entités, terrain et minimap."""

    def __init__(self, app, base_renderer):
        self.app = app
        self.base = base_renderer

    def draw_lane_paths_all(self):
        """Affiche les 3 lanes du joueur (cyan) et de l'ennemi (orange)."""
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        
        if self.app.lane_paths:
            for path in self.app.lane_paths:
                if not path or len(path) < 2:
                    continue
                pts = [self.base.grid_to_screen(x, y) for (x, y) in path]
                pygame.draw.lines(overlay, (80, 200, 255, 120), False, pts, 3)
                pygame.draw.circle(overlay, (80, 200, 255, 180), pts[0], 5)
                pygame.draw.circle(overlay, (80, 200, 255, 180), pts[-1], 5, 2)
        
        if self.app.lane_paths_enemy:
            for path in self.app.lane_paths_enemy:
                if not path or len(path) < 2:
                    continue
                pts = [self.base.grid_to_screen(x, y) for (x, y) in path]
                pygame.draw.lines(overlay, (255, 140, 80, 120), False, pts, 3)
                pygame.draw.circle(overlay, (255, 140, 80, 180), pts[0], 5)
                pygame.draw.circle(overlay, (255, 140, 80, 180), pts[-1], 5, 2)
        
        self.app.screen.blit(overlay, (0, 0))

    def draw_lane_preview_path(self):
        """Affiche le chemin de preview de lane."""
        if self.app.lane_flash_timer <= 0.0:
            return
        if not self.app.lane_preview_path or len(self.app.lane_preview_path) < 2:
            return

        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        pts = [self.base.grid_to_screen(x, y) for (x, y) in self.app.lane_preview_path]
        pygame.draw.lines(overlay, (240, 240, 240, 210), False, pts, 4)

        for p in pts[::2]:
            pygame.draw.circle(overlay, (240, 240, 240, 200), p, 3, 1)

        self.app.screen.blit(overlay, (0, 0))

    def draw_terrain_overlay(self):
        """Dessine l'overlay de terrain (zones interdites et dusty)."""
        w = int(getattr(self.app.nav_grid, "width", 0))
        h = int(getattr(self.app.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return

        tw = int(self.app.game_map.tilewidth)
        th = int(self.app.game_map.tileheight)

        for y in range(h):
            for x in range(w):
                walk = self.app.nav_grid.is_walkable(x, y)
                m = float(self.app.nav_grid.mult[y][x])

                if (not walk) or m <= 0.0:
                    color = (220, 50, 50, 70)
                elif m < 0.99:
                    color = (170, 120, 70, 60)
                else:
                    continue

                sx, sy = self.base.grid_to_screen(float(x), float(y))
                rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                s = pygame.Surface((tw, th), pygame.SRCALPHA)
                s.fill(color)
                self.app.screen.blit(s, rect.topleft)

    def debug_draw_forbidden(self):
        """Debug: dessine les zones interdites."""
        w = int(getattr(self.app.nav_grid, "width", 0))
        h = int(getattr(self.app.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return

        tw = int(self.app.game_map.tilewidth)
        th = int(self.app.game_map.tileheight)

        for y in range(h):
            for x in range(w):
                walk = self.app.nav_grid.is_walkable(x, y)
                m = float(self.app.nav_grid.mult[y][x])
                if (not walk) or m <= 0:
                    sx, sy = self.base.grid_to_screen(float(x), float(y))
                    rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                    pygame.draw.rect(self.app.screen, (220, 50, 50), rect, 1)

    def debug_draw_paths(self):
        """Debug: affiche les chemins de toutes les unités."""
        if self.app.world:
            self.app.world._activate()

        for ent, (t, path, team) in esper.get_components(Transform, PathComponent, Team):
            if not path.noeuds:
                continue

            pts = [self.base.grid_to_screen(n.x, n.y) for n in path.noeuds]
            if len(pts) >= 2:
                if team.id == 1:
                    color = (80, 200, 255)
                else:
                    color = (255, 120, 80)
                
                pygame.draw.lines(self.app.screen, color, False, pts, 2)
                pygame.draw.circle(self.app.screen, color, pts[-1], 4)

    def draw_entities(self):
        """Dessine toutes les entités (pyramides, unités, projectiles)."""
        from Game.Rendering.sprite_renderer import sprite_renderer
        
        if self.app.world:
            self.app.world._activate()

        # Pyramides
        for eid in (self.app.player_pyramid_eid, self.app.enemy_pyramid_eid):
            t = esper.component_for_entity(eid, Transform)
            team = esper.component_for_entity(eid, Team)
            h = esper.component_for_entity(eid, Health)

            sx, sy = self.base.grid_to_screen(t.pos[0], t.pos[1])
            ratio = 0.0 if h.hp_max <= 0 else max(0.0, min(1.0, h.hp / h.hp_max))
            
            level = 1
            if esper.has_component(eid, PyramidLevel):
                level = esper.component_for_entity(eid, PyramidLevel).level
            
            sprite_renderer.draw_pyramid(self.app.screen, sx, sy, team.id, ratio, level)

        # Unités
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if ent in (self.app.player_pyramid_eid, self.app.enemy_pyramid_eid):
                continue

            if esper.has_component(ent, Health):
                hp = esper.component_for_entity(ent, Health)
                if hp.is_dead:
                    continue
                ratio = max(0.0, min(1.0, hp.hp / hp.hp_max))
            else:
                ratio = 1.0

            sx, sy = self.base.grid_to_screen(t.pos[0], t.pos[1])
            
            is_moving = False
            if esper.has_component(ent, Velocity):
                vel = esper.component_for_entity(ent, Velocity)
                if abs(vel.vx) > 0.01 or abs(vel.vy) > 0.01:
                    is_moving = True
            
            power = getattr(stats, 'power', 0)
            if power <= 9:
                sprite_renderer.draw_momie(self.app.screen, sx, sy, team.id, ratio, is_moving)
            elif power <= 14:
                sprite_renderer.draw_dromadaire(self.app.screen, sx, sy, team.id, ratio, is_moving)
            else:
                sprite_renderer.draw_sphinx(self.app.screen, sx, sy, team.id, ratio, is_moving)

        # Projectiles
        for ent, (t, p) in esper.get_components(Transform, Projectile):
            sx, sy = self.base.grid_to_screen(t.pos[0], t.pos[1])
            sprite_renderer.draw_projectile(self.app.screen, sx, sy, p.team_id)

    def draw_minimap(self):
        """Dessine une minimap stylisée en bas à droite."""
        if not self.app.nav_grid:
            return
            
        grid_w = int(getattr(self.app.nav_grid, "width", 0))
        grid_h = int(getattr(self.app.nav_grid, "height", 0))
        if grid_w <= 0 or grid_h <= 0:
            return

        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)

        mm_w = 180
        mm_h = 90
        mm_x = self.app.width - mm_w - 15
        mm_y = self.app.height - mm_h - 35
        
        bg = pygame.Surface((mm_w + 8, mm_h + 8), pygame.SRCALPHA)
        bg.fill((35, 30, 25, 220))
        self.app.screen.blit(bg, (mm_x - 4, mm_y - 4))
        
        pygame.draw.rect(self.app.screen, gold_dark, (mm_x - 4, mm_y - 4, mm_w + 8, mm_h + 8), 3, border_radius=6)
        pygame.draw.rect(self.app.screen, gold_light, (mm_x, mm_y, mm_w, mm_h), 2, border_radius=4)
        
        scale_x = mm_w / grid_w
        scale_y = mm_h / grid_h
        
        # Terrain
        for y in range(grid_h):
            for x in range(grid_w):
                walk = self.app.nav_grid.is_walkable(x, y)
                m = float(self.app.nav_grid.mult[y][x])
                
                px = mm_x + int(x * scale_x)
                py = mm_y + int(y * scale_y)
                pw = max(1, int(scale_x))
                ph = max(1, int(scale_y))
                
                if not walk or m <= 0:
                    color = (80, 50, 45)
                elif m < 0.99:
                    color = (100, 85, 60)
                else:
                    color = (70, 65, 50)
                
                pygame.draw.rect(self.app.screen, color, (px, py, pw, ph))
        
        # Lanes
        for lane_y in self.app.lanes_y:
            py = mm_y + int(lane_y * scale_y)
            pygame.draw.line(self.app.screen, (100, 85, 60), (mm_x, py), (mm_x + mm_w, py), 1)
        
        # Pyramides
        for eid in (self.app.player_pyramid_eid, self.app.enemy_pyramid_eid):
            if not esper.entity_exists(eid):
                continue
            t = esper.component_for_entity(eid, Transform)
            team = esper.component_for_entity(eid, Team)
            
            px = mm_x + int(t.pos[0] * scale_x)
            py = mm_y + int(t.pos[1] * scale_y)
            
            if team.id == 1:
                color = (220, 190, 80)
            else:
                color = (220, 100, 80)
            points = [(px, py - 5), (px - 4, py + 3), (px + 4, py + 3)]
            
            pygame.draw.polygon(self.app.screen, color, points)
            pygame.draw.polygon(self.app.screen, (255, 255, 255), points, 1)
        
        # Unités
        for ent, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            if ent in (self.app.player_pyramid_eid, self.app.enemy_pyramid_eid):
                continue
            
            if esper.has_component(ent, Health):
                hp = esper.component_for_entity(ent, Health)
                if hp.is_dead:
                    continue
            
            px = mm_x + int(t.pos[0] * scale_x)
            py = mm_y + int(t.pos[1] * scale_y)
            
            if team.id == 1:
                color = (180, 220, 100)
            else:
                color = (255, 130, 100)
            
            pygame.draw.circle(self.app.screen, color, (px, py), 2)
        
        # Label
        label = self.app.font_small.render("Carte", True, text_gold)
        label_rect = label.get_rect(centerx=mm_x + mm_w // 2, bottom=mm_y - 8)
        self.app.screen.blit(label, label_rect)
