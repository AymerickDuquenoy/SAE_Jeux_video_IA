import pygame
from Game.Services.clock import GameClock
from Game.Services.event_bus import EventBus


class GameBoot:
    def __init__(self, app):
        self.app = app
        self.screen = None
        self.clock = GameClock(fps=60)
        self.bus = EventBus()
        self.running = True


    def boot(self):
        pygame.init()
        pygame.display.set_caption(self.app.title)
        self.screen = pygame.display.set_mode((self.app.width, self.app.height))


    def tick(self):
        self.clock.tick()


    def shutdown(self):
        pygame.quit()