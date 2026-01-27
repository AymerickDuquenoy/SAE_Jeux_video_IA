# Game/App/game_renderer.py
"""
Module de rendu pour Antique War.
Contient toutes les méthodes de dessin extraites de GameApp.
"""

import os
import pygame
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.projectile import Projectile
from Game.Ecs.Components.pyramidLevel import PyramidLevel
from Game.Ecs.Components.incomeRate import IncomeRate
from Game.Ecs.Components.path import Path as PathComponent

# Import conditionnel de PIL
try:
    from PIL import Image, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class GameRenderer:
    """
    Gère tout le rendu du jeu.
    Prend une référence vers GameApp pour accéder aux attributs nécessaires.
    """

    def __init__(self, app):
        """
        Args:
            app: Instance de GameApp
        """
        self.app = app

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════

    def grid_to_screen(self, gx: float, gy: float):
        """Convertit coordonnées grille -> écran."""
        tw = int(self.app.game_map.tilewidth)
        th = int(self.app.game_map.tileheight)
        px = (gx + 0.5) * tw
        py = (gy + 0.5) * th
        return int(px - self.app.camera_x), int(py - self.app.camera_y)

    def draw_panel(self, x: int, y: int, w: int, h: int, alpha: int = 120):
        """Dessine un panneau semi-transparent."""
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        self.app.screen.blit(s, (x, y))

    def draw_blurred_panel(self, x: int, y: int, w: int, h: int, blur_radius: int = 8):
        """Dessine un panneau avec effet de flou sur le fond."""
        if PIL_AVAILABLE:
            try:
                sub_surface = self.app.screen.subsurface((x, y, w, h)).copy()
                raw_str = pygame.image.tostring(sub_surface, "RGB")
                pil_img = Image.frombytes("RGB", (w, h), raw_str)
                pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                raw_str = pil_img.tobytes()
                blurred_surface = pygame.image.fromstring(raw_str, (w, h), "RGB")
                self.app.screen.blit(blurred_surface, (x, y))
                
                overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                overlay.fill((30, 25, 20, 140))
                self.app.screen.blit(overlay, (x, y))
                
                border_rect = pygame.Rect(x, y, w, h)
                pygame.draw.rect(self.app.screen, (139, 119, 77), border_rect, 3, border_radius=8)
            except Exception:
                self.draw_panel(x, y, w, h, alpha=180)
        else:
            self.draw_panel(x, y, w, h, alpha=180)

    def draw_center_overlay(self, title: str, subtitle: str = ""):
        """Dessine un overlay centré avec titre et sous-titre."""
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.app.screen.blit(overlay, (0, 0))

        surf = self.app.font_big.render(title, True, (255, 255, 255))
        rect = surf.get_rect(center=(self.app.width // 2, self.app.height // 2 - 140))
        self.app.screen.blit(surf, rect)

        if subtitle:
            sub = self.app.font.render(subtitle, True, (230, 230, 230))
            sr = sub.get_rect(center=(self.app.width // 2, self.app.height // 2 - 95))
            self.app.screen.blit(sub, sr)

    # ═══════════════════════════════════════════════════════════════════════════
    # ICÔNES
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_whip_icon(self, x: int, y: int, size: int = 20, with_background: bool = True):
        """Dessine l'icône du fouet depuis le PNG (avec cache multi-tailles)."""
        if with_background:
            bg_size = size - 2
            bg_x = x + 1
            bg_y = y + 1
            pygame.draw.rect(self.app.screen, (130, 115, 90), (bg_x, bg_y, bg_size, bg_size), border_radius=6)
            pygame.draw.rect(self.app.screen, (180, 155, 100), (bg_x, bg_y, bg_size, bg_size), 2, border_radius=6)
        
        if size in self.app.whip_icons_cache and self.app.whip_icons_cache[size] is not None:
            self.app.screen.blit(self.app.whip_icons_cache[size], (x, y))
            return
        
        if self.app.whip_icon is None:
            try:
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "fouet.png"),
                    os.path.join("Game", "assets", "sprites", "fouet.png"),
                    os.path.join("assets", "sprites", "fouet.png"),
                ]
                for whip_path in possible_paths:
                    if os.path.exists(whip_path):
                        self.app.whip_icon = pygame.image.load(whip_path).convert_alpha()
                        break
                else:
                    self.app.whip_icon = False
            except Exception as e:
                print(f"[WARN] Failed to load fouet.png: {e}")
                self.app.whip_icon = False
        
        if self.app.whip_icon and self.app.whip_icon is not False:
            orig_w, orig_h = self.app.whip_icon.get_size()
            scale = size / orig_h
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            
            if new_w > 0 and new_h > 0:
                scaled = pygame.transform.smoothscale(self.app.whip_icon, (new_w, new_h))
                self.app.whip_icons_cache[size] = scaled
                offset_x = (size - new_w) // 2
                self.app.screen.blit(scaled, (x + offset_x, y))
                return
        
        # Fallback
        handle_color = (139, 90, 43)
        pygame.draw.rect(self.app.screen, handle_color, (x, y + size//2 - 3, 8, 6), border_radius=2)
        whip_color = (180, 140, 80)
        points = [(x + 8, y + size//2), (x + 12, y + size//3), (x + 16, y + size//4), (x + size, y + 2)]
        pygame.draw.lines(self.app.screen, whip_color, False, points, 3)
        pygame.draw.circle(self.app.screen, (220, 180, 100), (x + size, y + 2), 2)

    def get_unit_icon(self, unit_key: str, size: int = 32) -> pygame.Surface:
        """Retourne une icône miniature de l'unité depuis le sprite."""
        cache_key = f"icon_{unit_key}_{size}"
        
        if cache_key in self.app.unit_icons_cache:
            return self.app.unit_icons_cache[cache_key]
        
        icon = pygame.Surface((size, size), pygame.SRCALPHA)
        
        try:
            from Game.App.sprite_renderer import sprite_renderer
            sprite_renderer._load_sprites()
            
            sprite_map = {"S": "momie_1", "M": "dromadaire_1", "L": "sphinx_1"}
            sprite_key = sprite_map.get(unit_key, "momie_1")
            
            frames = sprite_renderer.frames.get(sprite_key)
            if frames and frames[0]:
                orig = frames[0]
                orig_w, orig_h = orig.get_size()
                scale = min(size / orig_w, size / orig_h) * 0.9
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled = pygame.transform.smoothscale(orig, (new_w, new_h))
                icon.blit(scaled, ((size - new_w) // 2, (size - new_h) // 2))
                self.app.unit_icons_cache[cache_key] = icon
                return icon
        except Exception:
            pass
        
        # Fallback
        colors = {"S": (200, 180, 140), "M": (180, 140, 100), "L": (220, 200, 150)}
        color = colors.get(unit_key, (200, 180, 140))
        
        if unit_key == "S":
            pygame.draw.circle(icon, color, (size//2, size//2), size//3)
            pygame.draw.circle(icon, (255, 255, 200), (size//2 - 3, size//2 - 3), 2)
        elif unit_key == "M":
            pygame.draw.ellipse(icon, color, (4, 8, size - 8, size - 12))
            pygame.draw.circle(icon, color, (size//2 + 6, 8), 4)
        else:
            points = [(size//2, 4), (4, size - 4), (size - 4, size - 4)]
            pygame.draw.polygon(icon, color, points)
        
        self.app.unit_icons_cache[cache_key] = icon
        return icon

    def draw_upgrade_icon(self, surface: pygame.Surface, x: int, y: int, size: int = 24):
        """Dessine une icône d'upgrade (flèche vers le haut avec étoile)."""
        cx, cy = x + size // 2, y + size // 2
        
        arrow_color = (255, 220, 100)
        points = [
            (cx, y + 3), (cx - 8, y + 12), (cx - 4, y + 12),
            (cx - 4, y + size - 3), (cx + 4, y + size - 3),
            (cx + 4, y + 12), (cx + 8, y + 12),
        ]
        pygame.draw.polygon(surface, arrow_color, points)
        pygame.draw.polygon(surface, (200, 170, 60), points, 2)
        pygame.draw.circle(surface, (255, 255, 200), (cx, y + 5), 3)

    # ═══════════════════════════════════════════════════════════════════════════
    # LANES
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_lane_paths_all(self):
        """Affiche les 3 lanes du joueur (cyan) et les 3 lanes de l'ennemi (orange)."""
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        
        if self.app.lane_paths:
            for path in self.app.lane_paths:
                if not path or len(path) < 2:
                    continue
                pts = [self.grid_to_screen(x, y) for (x, y) in path]
                pygame.draw.lines(overlay, (80, 200, 255, 120), False, pts, 3)
                pygame.draw.circle(overlay, (80, 200, 255, 180), pts[0], 5)
                pygame.draw.circle(overlay, (80, 200, 255, 180), pts[-1], 5, 2)
        
        if self.app.lane_paths_enemy:
            for path in self.app.lane_paths_enemy:
                if not path or len(path) < 2:
                    continue
                pts = [self.grid_to_screen(x, y) for (x, y) in path]
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
        pts = [self.grid_to_screen(x, y) for (x, y) in self.app.lane_preview_path]
        pygame.draw.lines(overlay, (240, 240, 240, 210), False, pts, 4)

        for p in pts[::2]:
            pygame.draw.circle(overlay, (240, 240, 240, 200), p, 3, 1)

        self.app.screen.blit(overlay, (0, 0))

    def draw_lane_selector(self):
        """Dessine les boutons de sélection de lane avec style égyptien."""
        selected = self.app._get_selected_lane_index()
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        sand_bg = (58, 52, 45)
        sand_active = (90, 75, 55)
        text_gold = (222, 205, 163)
        
        for i, r in enumerate(self.app.lane_btn_rects):
            active = (i == selected)
            bg = sand_active if active else sand_bg
            pygame.draw.rect(self.app.screen, bg, r, border_radius=6)
            
            border_color = gold_light if active else gold_dark
            pygame.draw.rect(self.app.screen, border_color, r, width=3, border_radius=6)
            
            if active:
                inner = r.inflate(-6, -6)
                pygame.draw.rect(self.app.screen, gold_light, inner, width=2, border_radius=4)
            
            txt_col = (255, 230, 150) if active else text_gold
            s = self.app.font_small.render(f"Lane {i+1}", True, txt_col)
            tr = s.get_rect(center=r.center)
            self.app.screen.blit(s, tr)

    # ═══════════════════════════════════════════════════════════════════════════
    # TERRAIN
    # ═══════════════════════════════════════════════════════════════════════════

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

                sx, sy = self.grid_to_screen(float(x), float(y))
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
                    sx, sy = self.grid_to_screen(float(x), float(y))
                    rect = pygame.Rect(int(sx - tw / 2), int(sy - th / 2), tw, th)
                    pygame.draw.rect(self.app.screen, (220, 50, 50), rect, 1)

    def debug_draw_paths(self):
        """Debug: affiche les chemins de toutes les unités."""
        if self.app.world:
            self.app.world._activate()

        for ent, (t, path, team) in esper.get_components(Transform, PathComponent, Team):
            if not path.noeuds:
                continue

            pts = [self.grid_to_screen(n.x, n.y) for n in path.noeuds]
            if len(pts) >= 2:
                if team.id == 1:
                    color = (80, 200, 255)
                else:
                    color = (255, 120, 80)
                
                pygame.draw.lines(self.app.screen, color, False, pts, 2)
                pygame.draw.circle(self.app.screen, color, pts[-1], 4)

    # ═══════════════════════════════════════════════════════════════════════════
    # ENTITÉS
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_entities(self):
        """Dessine toutes les entités (pyramides, unités, projectiles)."""
        from Game.App.sprite_renderer import sprite_renderer
        
        if self.app.world:
            self.app.world._activate()

        # Pyramides
        for eid in (self.app.player_pyramid_eid, self.app.enemy_pyramid_eid):
            t = esper.component_for_entity(eid, Transform)
            team = esper.component_for_entity(eid, Team)
            h = esper.component_for_entity(eid, Health)

            sx, sy = self.grid_to_screen(t.pos[0], t.pos[1])
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

            sx, sy = self.grid_to_screen(t.pos[0], t.pos[1])
            
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
            sx, sy = self.grid_to_screen(t.pos[0], t.pos[1])
            sprite_renderer.draw_projectile(self.app.screen, sx, sy, p.team_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # HUD
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_hud_minimal(self):
        """Dessine le HUD principal avec style égyptien."""
        if not self.app.player_pyramid_eid or not self.app.enemy_pyramid_eid:
            return

        if self.app.world:
            self.app.world._activate()

        wallet = esper.component_for_entity(self.app.player_pyramid_eid, Wallet)
        player_hp = esper.component_for_entity(self.app.player_pyramid_eid, Health)
        enemy_hp = esper.component_for_entity(self.app.enemy_pyramid_eid, Health)

        try:
            income = esper.component_for_entity(self.app.player_pyramid_eid, IncomeRate)
            income_rate = income.effective_rate if hasattr(income, 'effective_rate') else income.rate
        except Exception:
            income_rate = 2.5

        # Couleurs égyptiennes
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)
        text_light = (255, 245, 220)
        bg_dark = (40, 35, 30, 220)
        
        # ═══════════════════════════════════════════════════════════════════════
        # PANNEAU RESSOURCES + HP
        # ═══════════════════════════════════════════════════════════════════════
        panel_w, panel_h = 280, 90
        panel_x, panel_y = 12, 12
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(bg_dark)
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=8)
        pygame.draw.rect(self.app.screen, gold_light, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 2, border_radius=6)
        
        # Ligne 1: Ressources
        self.draw_whip_icon(panel_x + 12, panel_y + 8, 22, with_background=False)
        
        fouet_text = f"{int(wallet.solde)}"
        prod_text = f"+{income_rate:.1f}/s"
        
        fouet_surf = self.app.font.render(fouet_text, True, (255, 215, 80))
        prod_surf = self.app.font_small.render(prod_text, True, (150, 220, 150))
        
        self.app.screen.blit(fouet_surf, (panel_x + 55, panel_y + 12))
        self.app.screen.blit(prod_surf, (panel_x + 55 + fouet_surf.get_width() + 8, panel_y + 16))
        
        # Ligne 2: Barre de vie JOUEUR
        bar_y = panel_y + 40
        bar_w = 120
        bar_h = 14
        
        you_label = self.app.font_small.render("Vous", True, text_gold)
        self.app.screen.blit(you_label, (panel_x + 15, bar_y - 1))
        
        bar_x = panel_x + 55
        hp_ratio = player_hp.hp / max(1, player_hp.hp_max)
        pygame.draw.rect(self.app.screen, (50, 45, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = max(0, int((bar_w - 4) * hp_ratio))
        if fill_w > 0:
            pygame.draw.rect(self.app.screen, (80, 180, 120), (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=2)
        pygame.draw.rect(self.app.screen, gold_dark, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)
        
        hp_text = self.app.font_small.render(f"{player_hp.hp}/{player_hp.hp_max}", True, text_light)
        self.app.screen.blit(hp_text, (bar_x + bar_w + 6, bar_y - 1))
        
        # Ligne 3: Barre de vie ENNEMI
        bar_y = panel_y + 62
        
        enemy_label = self.app.font_small.render("Ennemi", True, (220, 150, 150))
        self.app.screen.blit(enemy_label, (panel_x + 15, bar_y - 1))
        
        bar_x = panel_x + 70
        bar_w = 105
        hp_ratio = enemy_hp.hp / max(1, enemy_hp.hp_max)
        pygame.draw.rect(self.app.screen, (50, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = max(0, int((bar_w - 4) * hp_ratio))
        if fill_w > 0:
            pygame.draw.rect(self.app.screen, (220, 80, 80), (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=2)
        pygame.draw.rect(self.app.screen, (160, 100, 100), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)
        
        hp_text = self.app.font_small.render(f"{enemy_hp.hp}/{enemy_hp.hp_max}", True, (255, 200, 200))
        self.app.screen.blit(hp_text, (bar_x + bar_w + 6, bar_y - 1))
        
        # ═══════════════════════════════════════════════════════════════════════
        # BOUTONS UNITÉS
        # ═══════════════════════════════════════════════════════════════════════
        units_y = panel_y + panel_h + 10
        btn_size = 50
        btn_gap = 8
        
        try:
            unit_data = {
                "S": {"cost": int(self.app.factory.compute_unit_stats("S").cost), "key": "1", "name": "Momie"},
                "M": {"cost": int(self.app.factory.compute_unit_stats("M").cost), "key": "2", "name": "Dromadaire"},
                "L": {"cost": int(self.app.factory.compute_unit_stats("L").cost), "key": "3", "name": "Sphinx"},
            }
        except:
            unit_data = {
                "S": {"cost": 80, "key": "1", "name": "Momie"},
                "M": {"cost": 120, "key": "2", "name": "Dromadaire"},
                "L": {"cost": 180, "key": "3", "name": "Sphinx"},
            }
        
        btn_x = panel_x
        for unit_key, data in unit_data.items():
            cost = data["cost"]
            can_afford = wallet.solde >= cost
            
            btn_rect = pygame.Rect(btn_x, units_y, btn_size, btn_size + 18)
            self.app.unit_btn_rects[unit_key] = btn_rect
            
            if can_afford:
                bg_color = (55, 50, 42, 230)
                border_color = gold_light
            else:
                bg_color = (45, 40, 38, 200)
                border_color = (100, 80, 60)
            
            btn_surf = pygame.Surface((btn_size, btn_size + 18), pygame.SRCALPHA)
            btn_surf.fill(bg_color)
            self.app.screen.blit(btn_surf, (btn_x, units_y))
            pygame.draw.rect(self.app.screen, border_color, btn_rect, 2, border_radius=6)
            
            icon = self.get_unit_icon(unit_key, btn_size - 8)
            icon_x = btn_x + 4
            icon_y = units_y + 2
            self.app.screen.blit(icon, (icon_x, icon_y))
            
            cost_color = (150, 220, 150) if can_afford else (180, 100, 100)
            cost_text = self.app.font_small.render(f"{cost}", True, cost_color)
            cost_rect = cost_text.get_rect(centerx=btn_x + btn_size // 2, top=units_y + btn_size - 2)
            self.app.screen.blit(cost_text, cost_rect)
            
            key_text = self.app.font_small.render(data["key"], True, (180, 170, 150))
            self.app.screen.blit(key_text, (btn_x + 3, units_y + 3))
            
            btn_x += btn_size + btn_gap
        
        # ═══════════════════════════════════════════════════════════════════════
        # BOUTON UPGRADE
        # ═══════════════════════════════════════════════════════════════════════
        upgrade_x = btn_x + 5
        upgrade_w = 55
        upgrade_h = btn_size + 18
        
        try:
            pyr_level = esper.component_for_entity(self.app.player_pyramid_eid, PyramidLevel)
            current_level = pyr_level.level
        except:
            current_level = 1
        
        max_level = int(self.app.balance.get("pyramid", {}).get("level_max", 5))
        upgrade_costs = self.app.balance.get("pyramid", {}).get("upgrade_costs", [100, 125, 150, 175, 200])
        
        can_upgrade = current_level < max_level
        if can_upgrade and current_level - 1 < len(upgrade_costs):
            upgrade_cost = upgrade_costs[current_level - 1]
            can_afford_upgrade = wallet.solde >= upgrade_cost
        else:
            upgrade_cost = 0
            can_afford_upgrade = False
        
        self.app.upgrade_btn_rect = pygame.Rect(upgrade_x, units_y, upgrade_w, upgrade_h)
        
        if can_upgrade and can_afford_upgrade:
            bg_color = (60, 55, 40, 230)
            border_color = (200, 180, 100)
        elif can_upgrade:
            bg_color = (50, 45, 40, 200)
            border_color = gold_dark
        else:
            bg_color = (40, 40, 40, 180)
            border_color = (80, 80, 80)
        
        upgrade_surf = pygame.Surface((upgrade_w, upgrade_h), pygame.SRCALPHA)
        upgrade_surf.fill(bg_color)
        self.app.screen.blit(upgrade_surf, (upgrade_x, units_y))
        pygame.draw.rect(self.app.screen, border_color, self.app.upgrade_btn_rect, 2, border_radius=6)
        
        self.draw_upgrade_icon(self.app.screen, upgrade_x + (upgrade_w - 28) // 2, units_y + 5, 28)
        
        if can_upgrade:
            level_text = self.app.font_small.render(f"Nv.{current_level + 1}", True, text_gold)
            cost_color = (150, 220, 150) if can_afford_upgrade else (180, 100, 100)
            cost_text = self.app.font_small.render(f"{upgrade_cost}", True, cost_color)
        else:
            level_text = self.app.font_small.render("MAX", True, (180, 180, 180))
            cost_text = None
        
        level_rect = level_text.get_rect(centerx=upgrade_x + upgrade_w // 2, top=units_y + 36)
        self.app.screen.blit(level_text, level_rect)
        
        if cost_text:
            cost_rect = cost_text.get_rect(centerx=upgrade_x + upgrade_w // 2, top=units_y + btn_size + 2)
            self.app.screen.blit(cost_text, cost_rect)
        
        u_text = self.app.font_small.render("U", True, (180, 170, 150))
        self.app.screen.blit(u_text, (upgrade_x + 3, units_y + 3))

        # ═══════════════════════════════════════════════════════════════════════
        # SÉLECTEUR DE LANE
        # ═══════════════════════════════════════════════════════════════════════
        lane_y = units_y + btn_size + 28
        lane_bw = 75
        lane_bh = 28
        lane_gap = 8
        
        self.app.lane_btn_rects = [
            pygame.Rect(panel_x + i * (lane_bw + lane_gap), lane_y, lane_bw, lane_bh)
            for i in range(3)
        ]
        
        self.draw_lane_selector()

        # ═══════════════════════════════════════════════════════════════════════
        # MESSAGE D'ÉVÉNEMENT
        # ═══════════════════════════════════════════════════════════════════════
        if self.app.random_event_system:
            msg = self.app.random_event_system.get_message()
            if msg:
                event_surf = self.app.font_big.render(msg, True, (255, 220, 80))
                event_rect = event_surf.get_rect(center=(self.app.width // 2, 80))
                bg_rect = event_rect.inflate(30, 15)
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surf.fill((40, 30, 20, 220))
                self.app.screen.blit(bg_surf, bg_rect.topleft)
                pygame.draw.rect(self.app.screen, gold_light, bg_rect, 3, border_radius=8)
                self.app.screen.blit(event_surf, event_rect)

    def draw_hud_advanced(self):
        """Dessine le HUD avancé avec infos de debug."""
        self.draw_panel(12, 112, 640, 94, alpha=100)
        x = 22
        y = 120

        l1 = self.app.font_small.render(
            f"Map: {self.app.map_name} | Seed: {self.app.map_seed} | "
            f"open={self.app.zone_counts.get('open', 0)} dusty={self.app.zone_counts.get('dusty', 0)} interdit={self.app.zone_counts.get('forbidden', 0)}",
            True, (220, 220, 220)
        )
        l2 = self.app.font_small.render(
            f"Match: {self.app.match_time:.1f}s | Kills: {self.app.enemy_kills}",
            True, (220, 220, 220)
        )
        
        if self.app.enemy_spawner_system:
            diff_txt = self.app.enemy_spawner_system.hud_line()
        else:
            diff_txt = "Spawner: N/A"
        l3 = self.app.font_small.render(diff_txt, True, (220, 220, 220))

        self.app.screen.blit(l1, (x, y))
        self.app.screen.blit(l2, (x, y + 22))
        self.app.screen.blit(l3, (x, y + 44))

    # ═══════════════════════════════════════════════════════════════════════════
    # MINIMAP
    # ═══════════════════════════════════════════════════════════════════════════

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
