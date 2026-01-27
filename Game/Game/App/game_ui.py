import pygame

class GameUI:
    def __init__(self, app):
        self.app = app


    def handle_events(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.app.boot.running = False