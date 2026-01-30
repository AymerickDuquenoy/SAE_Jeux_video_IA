# Game/App/ui.py
import pygame


class UIButton:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.font = font
        self.hover = False

    # Retourne True si le bouton a été cliqué
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    # Dessine le bouton sur l'écran
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

    # Retourne True si le bouton a été cliqué et False sinon
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    # Dessine le bouton avec style égyptien&
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
    """Toggle stylisé égyptien pour les options."""
    
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font, value: bool = False):
        self.rect = rect
        self.label = label
        self.font = font
        self.value = value
        self.hover = False
        
        # Couleurs style égyptien
        self.bg_normal = (58, 62, 70)
        self.bg_hover = (72, 76, 85)
        self.border_outer = (139, 119, 77)
        self.border_inner = (179, 156, 101)
        self.text_color = (222, 205, 163)

    # Retourne True si le bouton a été cliqué et False sinon
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                return True
        return False

    # Dessine le bouton avec style égyptien et status ON/OFF
    def draw(self, screen: pygame.Surface):
        # Fond du bouton
        bg = self.bg_hover if self.hover else self.bg_normal
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        
        # Bordure extérieure (dorée foncée)
        pygame.draw.rect(screen, self.border_outer, self.rect, 3, border_radius=6)
        
        # Bordure intérieure (dorée claire)
        inner_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(screen, self.border_inner, inner_rect, 2, border_radius=4)

        # Label
        left = self.font.render(self.label, True, self.text_color)
        screen.blit(left, (self.rect.x + 14, self.rect.y + 14))

        # Status ON/OFF
        status = "ON" if self.value else "OFF"
        color = (120, 240, 160) if self.value else (240, 120, 120)
        right = self.font.render(status, True, color)
        rr = right.get_rect(midright=(self.rect.right - 14, self.rect.y + self.rect.height // 2))
        screen.blit(right, rr)


class UISelector:
    """Selecteur de valeur avec fleches gauche/droite (style egyptien)."""
    
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font, options: list, index: int = 0):
        self.rect = rect
        self.label = label
        self.font = font
        self.options = options
        self.index = index
        self.hover = False
        self.hover_left = False
        self.hover_right = False
        
        # Couleurs style egyptien
        self.bg_normal = (58, 62, 70)
        self.bg_hover = (72, 76, 85)
        self.border_outer = (139, 119, 77)
        self.border_inner = (179, 156, 101)
        self.text_color = (222, 205, 163)
        self.arrow_color = (179, 156, 101)
        self.arrow_hover = (255, 220, 150)
        
        # Zones cliquables pour les fleches
        self.arrow_size = 30
        self.left_rect = pygame.Rect(0, 0, self.arrow_size, self.arrow_size)
        self.right_rect = pygame.Rect(0, 0, self.arrow_size, self.arrow_size)

    # Retourne la valeur actuellement selectionnee dans le selecteur
    def get_value(self):
        """Retourne la valeur actuellement selectionnee."""
        if 0 <= self.index < len(self.options):
            return self.options[self.index]
        return None

    # Retourne True si le bouton a été cliqué et False sinon
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            self.hover_left = self.left_rect.collidepoint(event.pos)
            self.hover_right = self.right_rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_rect.collidepoint(event.pos):
                self.index = (self.index - 1) % len(self.options)
                return True
            if self.right_rect.collidepoint(event.pos):
                self.index = (self.index + 1) % len(self.options)
                return True
        return False

    # Dessine le bouton avec style égyptien&& plus compact
    def draw(self, screen: pygame.Surface):
        # Fond du bouton
        bg = self.bg_hover if self.hover else self.bg_normal
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        
        # Bordure exterieure (doree foncee)
        pygame.draw.rect(screen, self.border_outer, self.rect, 3, border_radius=6)
        
        # Bordure interieure (doree claire)
        inner_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(screen, self.border_inner, inner_rect, 2, border_radius=4)

        # Label a gauche
        left = self.font.render(self.label, True, self.text_color)
        screen.blit(left, (self.rect.x + 10, self.rect.y + (self.rect.height - left.get_height()) // 2))

        # Zone de selection a droite (plus compacte)
        select_width = min(150, self.rect.width // 2)
        select_x = self.rect.right - select_width - 8
        select_cy = self.rect.y + self.rect.height // 2
        
        # Mettre a jour les zones de fleches
        arrow_size = 24
        self.left_rect = pygame.Rect(select_x, select_cy - arrow_size // 2, arrow_size, arrow_size)
        self.right_rect = pygame.Rect(self.rect.right - arrow_size - 10, select_cy - arrow_size // 2, arrow_size, arrow_size)
        
        # Fleche gauche <
        left_color = self.arrow_hover if self.hover_left else self.arrow_color
        left_points = [
            (self.left_rect.centerx + 6, self.left_rect.centery - 8),
            (self.left_rect.centerx - 4, self.left_rect.centery),
            (self.left_rect.centerx + 6, self.left_rect.centery + 8),
        ]
        pygame.draw.polygon(screen, left_color, left_points)
        
        # Valeur actuelle au centre
        value = self.get_value()
        if value:
            if isinstance(value, tuple):
                value_text = f"{value[0]}x{value[1]}"
            else:
                value_text = str(value)
        else:
            value_text = "---"
        value_surf = self.font.render(value_text, True, (255, 220, 150))
        value_rect = value_surf.get_rect(center=(select_x + select_width // 2, select_cy))
        screen.blit(value_surf, value_rect)
        
        # Fleche droite >
        right_color = self.arrow_hover if self.hover_right else self.arrow_color
        right_points = [
            (self.right_rect.centerx - 6, self.right_rect.centery - 8),
            (self.right_rect.centerx + 4, self.right_rect.centery),
            (self.right_rect.centerx - 6, self.right_rect.centery + 8),
        ]
        pygame.draw.polygon(screen, right_color, right_points)
