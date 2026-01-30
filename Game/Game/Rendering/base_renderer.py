# Game/App/renderers/base_renderer.py
"""Base rendering utilities for Antique War."""

import pygame

try:
    from PIL import Image, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class BaseRenderer:
    """Utilitaires de rendu de base."""

    # Initialise le renderer de base avec référence à l'application
    def __init__(self, app):
        self.app = app

    # Convertit des coordonnées grille en coordonnées écran
    def grid_to_screen(self, gx: float, gy: float):
        """Convertit coordonnées grille -> écran."""
        tw = int(self.app.game_map.tilewidth)
        th = int(self.app.game_map.tileheight)
        px = (gx + 0.5) * tw
        py = (gy + 0.5) * th
        return int(px - self.app.camera_x), int(py - self.app.camera_y)

    # Dessine un panneau semi-transparent
    def draw_panel(self, x: int, y: int, w: int, h: int, alpha: int = 120):
        """Dessine un panneau semi-transparent."""
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        self.app.screen.blit(s, (x, y))

    # Dessine un panneau avec effet de flou sur le fond (si PIL disponible)
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

    # Dessine un overlay centré avec titre et sous-titre
    def draw_center_overlay(self, title: str, subtitle: str = ""):
        """Dessine un overlay centré avec titre et sous-titre."""
        overlay = pygame.Surface((self.app.base_width, self.app.base_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.app.screen.blit(overlay, (0, 0))

        surf = self.app.font_big.render(title, True, (255, 255, 255))
        rect = surf.get_rect(center=(self.app.base_width // 2, self.app.base_height // 2 - 140))
        self.app.screen.blit(surf, rect)

        if subtitle:
            sub = self.app.font.render(subtitle, True, (230, 230, 230))
            sr = sub.get_rect(center=(self.app.base_width // 2, self.app.base_height // 2 - 95))
            self.app.screen.blit(sub, sr)