# Game/App/game_renderer.py
"""
Façade de rendu pour Antique War.
Coordonne les différents modules de rendu spécialisés.
"""

from Game.Rendering.base_renderer import BaseRenderer
from Game.Rendering.hud_renderer import HUDRenderer
from Game.Rendering.entity_renderer import EntityRenderer
from Game.Rendering.menu_renderer import MenuRenderer


class GameRenderer:
    """
    Façade de rendu principal.
    Délègue aux modules spécialisés.
    """

    def __init__(self, app):
        self.app = app
        
        # Sous-renderers spécialisés
        self.base = BaseRenderer(app)
        self.hud = HUDRenderer(app)
        self.entity = EntityRenderer(app, self.base)
        self.menu = MenuRenderer(app, self.base)

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES (délégués à BaseRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    def grid_to_screen(self, gx: float, gy: float):
        return self.base.grid_to_screen(gx, gy)

    def draw_panel(self, x: int, y: int, w: int, h: int, alpha: int = 120):
        self.base.draw_panel(x, y, w, h, alpha)

    def draw_blurred_panel(self, x: int, y: int, w: int, h: int, blur_radius: int = 8):
        self.base.draw_blurred_panel(x, y, w, h, blur_radius)

    def draw_center_overlay(self, title: str, subtitle: str = ""):
        self.base.draw_center_overlay(title, subtitle)

    # ═══════════════════════════════════════════════════════════════════════════
    # HUD (délégué à HUDRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_hud_minimal(self):
        self.hud.draw_hud_minimal()

    def draw_hud_player2(self):
        self.hud.draw_hud_player2()

    def draw_hud_advanced(self):
        self.hud.draw_hud_advanced(self.base)

    def draw_lane_selector(self):
        self.hud.draw_lane_selector()

    # ═══════════════════════════════════════════════════════════════════════════
    # ENTITÉS ET TERRAIN (délégué à EntityRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_entities(self):
        self.entity.draw_entities()

    def draw_minimap(self):
        self.entity.draw_minimap()

    def draw_terrain_overlay(self):
        self.entity.draw_terrain_overlay()

    def draw_lane_paths_all(self):
        self.entity.draw_lane_paths_all()

    def draw_lane_preview_path(self):
        self.entity.draw_lane_preview_path()

    def debug_draw_paths(self):
        self.entity.debug_draw_paths()

    def debug_draw_forbidden(self):
        self.entity.debug_draw_forbidden()

    # ═══════════════════════════════════════════════════════════════════════════
    # MENUS (délégué à MenuRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    def draw_menu(self):
        self.menu.draw_menu()

    def draw_mode_select(self):
        self.menu.draw_mode_select()

    def draw_difficulty_select(self):
        self.menu.draw_difficulty_select()

    def draw_options(self):
        self.menu.draw_options()

    def draw_controls(self):
        self.menu.draw_controls()

    def draw_pause(self):
        self.menu.draw_pause()

    def draw_game_over(self):
        self.menu.draw_game_over()
