from dataclasses import dataclass

@dataclass
class Spawner:
    """
    Component Spawner. Décrit un générateur d'entités qui spawn à intervalles
    réguliers dans une zone rectangulaire (coordonnées monde/grille).

    Attributes:
        time_between_spawns: Délai entre deux spawns.
        current_time: Accumulateur de temps (remis à 0 à chaque spawn).
        min_x: Coordonnée X du bord gauche de la zone de spawn.
        min_y: Coordonnée Y du bord haut de la zone de spawn.
        max_x: Coordonnée X du bord droit de la zone de spawn.
        max_y: Coordonnée Y du bord bas de la zone de spawn.
    """
    time_between_spawns: float = 1.0
    current_time: float = 0.0
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0