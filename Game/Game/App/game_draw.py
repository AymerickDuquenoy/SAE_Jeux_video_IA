import pygame

class GameDraw:
    def __init__(self, app):
        self.app = app

    def render(self):
        screen = self.app.boot.screen
        screen.fill((20, 20, 30))
        if self.app.match.world:
            pass
        pygame.display.flip()