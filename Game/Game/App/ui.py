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
