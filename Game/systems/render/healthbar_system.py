import pygame
import esper
from components import Health, Position, Sprite


class HealthBarSystem(esper.Processor):
    def __init__(self, screen: pygame.Surface):
        super().__init__()
        self.screen = screen

    def process(self, dt: float):
        for _e, (hp, pos, spr) in esper.get_components(Health, Position, Sprite):
            if hp.hp <= 0:
                continue
            w = spr.width
            h = 6
            x = int(pos.x)
            y = int(pos.y - h - 3)
            ratio = hp.hp / max(1.0, hp.max_hp)
            ratio = max(0.0, min(1.0, ratio))
            pygame.draw.rect(self.screen, (180, 40, 40), (x, y, w, h))
            pygame.draw.rect(self.screen, (40, 200, 40), (x, y, int(w * ratio), h))