import esper
import pygame
from components import Position, Sprite
from constants import Screen


class RenderSystem(esper.Processor):
    def __init__(self, screen: pygame.Surface, world_w: int, world_h: int, camera_speed: float = 600.0):
        super().__init__()
        self.screen = screen
        self.world_w = world_w
        self.world_h = world_h
        self.camera_speed = camera_speed
        self.cam_x = 0.0
        self.cam_y = 0.0

    def process(self, dt: float):
        keys = pygame.key.get_pressed()
        dx = dy = 0.0
        if keys[pygame.K_UP] or keys[pygame.K_z] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_LEFT] or keys[pygame.K_q] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1

        if dx or dy:
            length = (dx*dx + dy*dy) ** 0.5
            dx /= length
            dy /= length
            self.cam_x += dx * self.camera_speed * dt
            self.cam_y += dy * self.camera_speed * dt

        max_x = max(0, self.world_w - Screen.WIDTH)
        max_y = max(0, self.world_h - Screen.HEIGHT)
        self.cam_x = max(0, min(self.cam_x, max_x))
        self.cam_y = max(0, min(self.cam_y, max_y))

        for _e, (pos, spr) in esper.get_components(Position, Sprite):
            sx = int(pos.x - self.cam_x)
            sy = int(pos.y - self.cam_y)
            if sx + spr.width < 0 or sy + spr.height < 0 or sx > Screen.WIDTH or sy > Screen.HEIGHT:
                continue
            pygame.draw.rect(self.screen, spr.color, pygame.Rect(sx, sy, spr.width, spr.height))
