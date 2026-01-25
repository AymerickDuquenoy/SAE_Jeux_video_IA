# Game/App/ui.py
import pygame


class UIButton:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.font = font
        self.hover = False

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, screen: pygame.Surface):
        bg = (70, 70, 78) if self.hover else (50, 50, 58)
        pygame.draw.rect(screen, bg, self.rect, border_radius=12)
        pygame.draw.rect(screen, (210, 210, 210), self.rect, 2, border_radius=12)

        surf = self.font.render(self.text, True, (240, 240, 240))
        r = surf.get_rect(center=self.rect.center)
        screen.blit(surf, r)


class UIMenuButton:
    """Bouton stylisé égyptien pour le menu principal."""
    
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.font = font
        self.hover = False
        
        # Couleurs style égyptien
        self.bg_normal = (58, 62, 70)       # Gris-bleu foncé
        self.bg_hover = (72, 76, 85)        # Plus clair au survol
        self.border_outer = (139, 119, 77)  # Bordure dorée extérieure
        self.border_inner = (179, 156, 101) # Bordure dorée intérieure
        self.text_color = (222, 205, 163)   # Texte beige/crème

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, screen: pygame.Surface):
        # Fond du bouton
        bg = self.bg_hover if self.hover else self.bg_normal
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        
        # Bordure extérieure (dorée foncée)
        pygame.draw.rect(screen, self.border_outer, self.rect, 3, border_radius=6)
        
        # Bordure intérieure (dorée claire)
        inner_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(screen, self.border_inner, inner_rect, 2, border_radius=4)
        
        # Texte
        surf = self.font.render(self.text, True, self.text_color)
        r = surf.get_rect(center=self.rect.center)
        screen.blit(surf, r)


class UIToggle:
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font, value: bool = False):
        self.rect = rect
        self.label = label
        self.font = font
        self.value = value
        self.hover = False

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                return True
        return False

    def draw(self, screen: pygame.Surface):
        bg = (60, 60, 70) if self.hover else (45, 45, 55)
        pygame.draw.rect(screen, bg, self.rect, border_radius=12)
        pygame.draw.rect(screen, (210, 210, 210), self.rect, 2, border_radius=12)

        left = self.font.render(self.label, True, (240, 240, 240))
        screen.blit(left, (self.rect.x + 14, self.rect.y + 14))

        status = "ON" if self.value else "OFF"
        color = (120, 240, 160) if self.value else (240, 120, 120)
        right = self.font.render(status, True, color)
        rr = right.get_rect(midright=(self.rect.right - 14, self.rect.y + self.rect.height // 2))
        screen.blit(right, rr)
