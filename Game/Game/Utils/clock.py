# Game/Services/clock.py
import pygame


class GameClock:
    def __init__(self, fps: int = 60):
        self.fps = int(fps)
        self._clock = pygame.time.Clock()
        self.delta_time = 0.0
        self.time = 0.0

    def tick(self) -> float:
        self.delta_time = self._clock.tick(self.fps) / 1000.0
        self.time += self.delta_time
        return self.delta_time
