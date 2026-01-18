# constants.py

class Screen:
    WIDTH = 800
    HEIGHT = 600
    FPS = 60


class Colors:
    BG = (20, 20, 40)   


class Gameplay:
    # Temps entre deux spawns par Spawner
    SPAWN_COOLDOWN = 0.30

    # HP de base et gain par niveau de la pyramide
    PYRAMID_BASE_HP = 500
    PYRAMID_UPGRADE_HP = 50

    # Revenu de base en 𓍯 / seconde
    BASE_INCOME_PER_SEC = 2.0

class Grid:

    # Taille 
    TILE_SIZE = 32