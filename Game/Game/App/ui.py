# Game/App/ui.py
"""
UI Components for Antique War.
Reusable UI elements: buttons, toggles, panels, etc.
"""

import pygame
from Game.App.constants import (
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT,
    COLOR_PLAYER, COLOR_BACKGROUND
)


class UIButton:
    """
    Clickable button with text.
    """
    
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 bg_color=COLOR_PANEL_BG, border_color=COLOR_PANEL_BORDER,
                 text_color=COLOR_TEXT, border_radius: int = 12):
        self.rect = rect
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.hovered = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse events. Returns True if button was clicked.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            return self.rect.collidepoint(mx, my)
        return False
    
    def update(self):
        """Update hover state."""
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mx, my)
    
    def draw(self, screen: pygame.Surface):
        """Draw the button."""
        # Background
        bg = self.bg_color if not self.hovered else tuple(min(c + 15, 255) for c in self.bg_color)
        pygame.draw.rect(screen, bg, self.rect, border_radius=self.border_radius)
        
        # Border
        pygame.draw.rect(screen, self.border_color, self.rect, width=2, border_radius=self.border_radius)
        
        # Text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class UIToggle:
    """
    Toggle switch with label.
    """
    
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font,
                 value: bool = False, bg_color=COLOR_PANEL_BG,
                 border_color=COLOR_PANEL_BORDER, text_color=COLOR_TEXT,
                 border_radius: int = 12):
        self.rect = rect
        self.label = label
        self.font = font
        self.value = bool(value)
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.border_radius = border_radius
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse events. Returns True if toggle was clicked.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if self.rect.collidepoint(mx, my):
                self.value = not self.value
                return True
        return False
    
    def draw(self, screen: pygame.Surface):
        """Draw the toggle."""
        # Background
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=self.border_radius)
        
        # Border
        pygame.draw.rect(screen, self.border_color, self.rect, width=2, border_radius=self.border_radius)
        
        # Label + state
        state_text = "ON" if self.value else "OFF"
        text = f"{self.label}: {state_text}"
        text_surface = self.font.render(text, True, self.text_color)
        screen.blit(text_surface, (self.rect.x + 16, self.rect.y + 14))


class UIPanel:
    """
    Semi-transparent panel for grouping UI elements.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, alpha: int = 120):
        self.rect = pygame.Rect(x, y, width, height)
        self.alpha = alpha
        self._surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    def draw(self, screen: pygame.Surface):
        """Draw the panel."""
        self._surface.fill((0, 0, 0, self.alpha))
        screen.blit(self._surface, self.rect.topleft)


class UILaneSelector:
    """
    Lane selection buttons (Lane 1, Lane 2, Lane 3).
    """
    
    def __init__(self, x: int, y: int, btn_width: int, btn_height: int,
                 gap: int, font: pygame.font.Font, lane_count: int = 3):
        self.font = font
        self.lane_count = lane_count
        self.selected_index = 1  # Default: Lane 2
        
        self.buttons = []
        for i in range(lane_count):
            rect = pygame.Rect(x + i * (btn_width + gap), y, btn_width, btn_height)
            self.buttons.append(rect)
    
    def handle_event(self, event: pygame.event.Event) -> int:
        """
        Handle mouse events. Returns clicked lane index (0-2) or -1 if no click.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, rect in enumerate(self.buttons):
                if rect.collidepoint(mx, my):
                    self.selected_index = i
                    return i
        return -1
    
    def set_selected(self, index: int):
        """Set the selected lane index."""
        self.selected_index = max(0, min(self.lane_count - 1, index))
    
    def get_selected(self) -> int:
        """Get the selected lane index."""
        return self.selected_index
    
    def draw(self, screen: pygame.Surface):
        """Draw all lane buttons."""
        for i, rect in enumerate(self.buttons):
            is_active = (i == self.selected_index)
            
            # Colors based on active state
            bg_color = COLOR_PLAYER if is_active else COLOR_PANEL_BG
            border_color = COLOR_TEXT if is_active else COLOR_PANEL_BORDER
            text_color = COLOR_BACKGROUND if is_active else COLOR_TEXT
            
            # Draw button
            pygame.draw.rect(screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(screen, border_color, rect, width=2, border_radius=10)
            
            # Draw text
            text_surface = self.font.render(f"Lane {i + 1}", True, text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)


class UIOverlay:
    """
    Full-screen overlay with title and subtitle.
    Used for menus, pause, game over screens.
    """
    
    def __init__(self, width: int, height: int, alpha: int = 150):
        self.width = width
        self.height = height
        self.alpha = alpha
        self._surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    def draw(self, screen: pygame.Surface, title: str, subtitle: str,
             font_big: pygame.font.Font, font_normal: pygame.font.Font):
        """Draw the overlay with title and subtitle."""
        # Darken background
        self._surface.fill((0, 0, 0, self.alpha))
        screen.blit(self._surface, (0, 0))
        
        # Title
        title_surface = font_big.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 2 - 140))
        screen.blit(title_surface, title_rect)
        
        # Subtitle
        if subtitle:
            sub_surface = font_normal.render(subtitle, True, (230, 230, 230))
            sub_rect = sub_surface.get_rect(center=(self.width // 2, self.height // 2 - 95))
            screen.blit(sub_surface, sub_rect)
