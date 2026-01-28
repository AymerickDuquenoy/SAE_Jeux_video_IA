# Game/Services/clock.py
import pygame


class GameClock:
    """
    Classe gérant le temps de jeu avec un FPS fixe.
    Attributes:
        fps: Nombre d'images par seconde cible.
        delta_time: Temps écoulé depuis la dernière image (en secondes).
        time: Temps total écoulé depuis le début du jeu (en secondes).
    """
    def __init__(self, fps: int = 60):
        self.fps = int(fps)
        self._clock = pygame.time.Clock()
        self.delta_time = 0.0
        self.time = 0.0

    # Met à jour le clock et calcule le delta time
    def tick(self) -> float:
        self.delta_time = self._clock.tick(self.fps) / 1000.0
        self.time += self.delta_time
        return self.delta_time
