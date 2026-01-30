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

    # Initialise la façade de rendu et crée tous les sous-renderers spécialisés
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

    # Convertit coordonnées grille en coordonnées écran (délégué)
    def grid_to_screen(self, gx: float, gy: float):
        return self.base.grid_to_screen(gx, gy)

    # Dessine un panneau semi-transparent (délégué)
    def draw_panel(self, x: int, y: int, w: int, h: int, alpha: int = 120):
        self.base.draw_panel(x, y, w, h, alpha)

    # Dessine un panneau avec flou (délégué)
    def draw_blurred_panel(self, x: int, y: int, w: int, h: int, blur_radius: int = 8):
        self.base.draw_blurred_panel(x, y, w, h, blur_radius)

    # Dessine un overlay centré (délégué)
    def draw_center_overlay(self, title: str, subtitle: str = ""):
        self.base.draw_center_overlay(title, subtitle)

    # ═══════════════════════════════════════════════════════════════════════════
    # HUD (délégué à HUDRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    # Affiche le HUD minimal du joueur (délégué)
    def draw_hud_minimal(self):
        self.hud.draw_hud_minimal()

    # Affiche le HUD du joueur 2 en mode 1v1 (délégué)
    def draw_hud_player2(self):
        self.hud.draw_hud_player2()

    # Affiche le HUD avancé avec infos détaillées (délégué)
    def draw_hud_advanced(self):
        self.hud.draw_hud_advanced(self.base)

    # Affiche le sélecteur de lanes en bas (délégué)
    def draw_lane_selector(self):
        self.hud.draw_lane_selector()

    # ═══════════════════════════════════════════════════════════════════════════
    # ENTITÉS ET TERRAIN (délégué à EntityRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    # Dessine toutes les entités (délégué)
    def draw_entities(self):
        self.entity.draw_entities()

    # Dessine la minimap (délégué)
    def draw_minimap(self):
        self.entity.draw_minimap()

    # Dessine l'overlay de terrain (délégué)
    def draw_terrain_overlay(self):
        self.entity.draw_terrain_overlay()

    # Affiche tous les chemins de lanes (délégué)
    def draw_lane_paths_all(self):
        self.entity.draw_lane_paths_all()

    # Affiche le chemin de preview (délégué)
    def draw_lane_preview_path(self):
        self.entity.draw_lane_preview_path()

    # Debug : affiche les chemins (délégué)
    def debug_draw_paths(self):
        self.entity.debug_draw_paths()

    # Debug : affiche les zones interdites (délégué)
    def debug_draw_forbidden(self):
        self.entity.debug_draw_forbidden()

    # ═══════════════════════════════════════════════════════════════════════════
    # MENUS (délégué à MenuRenderer)
    # ═══════════════════════════════════════════════════════════════════════════

    # Affiche le menu principal (délégué)
    def draw_menu(self):
        self.menu.draw_menu()

    # Affiche la sélection de mode (délégué)
    def draw_mode_select(self):
        self.menu.draw_mode_select()

    # Affiche la sélection de difficulté (délégué)
    def draw_difficulty_select(self):
        self.menu.draw_difficulty_select()

    # Affiche le menu des options (délégué)
    def draw_options(self):
        self.menu.draw_options()

    # Affiche le menu des contrôles (délégué)
    def draw_controls(self):
        self.menu.draw_controls()

    # Affiche le menu pause (délégué)
    def draw_pause(self):
        self.menu.draw_pause()

    # Affiche l'écran de game over (délégué)
    def draw_game_over(self):
        self.menu.draw_game_over()